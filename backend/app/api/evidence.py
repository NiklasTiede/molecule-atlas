from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Annotated
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    Header,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)

from app.application.capabilities.models import ActorContext, CapabilityContext
from app.application.evidence.artifact_inspection import (
    ListAvailableArtifactsCapability,
    ValidateEvidenceArtifactsCapability,
)
from app.application.evidence.candidate_evidence import GetCandidateEvidenceCapability
from app.application.evidence.comparison import CompareCandidatesCapability
from app.application.evidence.contracts import (
    DEFAULT_ARTIFACT_PAGE_SIZE,
    DEFAULT_CANDIDATE_PREDICTION_LIMIT,
    DEFAULT_CANDIDATE_VALIDATION_LIMIT,
    DEFAULT_RUN_PAGE_SIZE,
    MAX_ARTIFACT_PAGE_SIZE,
    MAX_CANDIDATE_PREDICTION_LIMIT,
    MAX_CANDIDATE_VALIDATION_LIMIT,
    MAX_EVIDENCE_BUNDLE_BYTES,
    MAX_RUN_PAGE_SIZE,
    CompareCandidatesInput,
    CompareCandidatesOutput,
    EvidenceReportFormat,
    GenerateEvidenceReportInput,
    GenerateEvidenceReportOutput,
    GetCandidateEvidenceInput,
    GetCandidateEvidenceOutput,
    GetRunSummaryInput,
    GetRunSummaryOutput,
    ImportEvidenceBundleInput,
    ImportEvidenceBundleOutput,
    ListAvailableArtifactsInput,
    ListAvailableArtifactsOutput,
    ListEvidenceRunsInput,
    ListEvidenceRunsOutput,
    ValidateEvidenceArtifactsInput,
    ValidateEvidenceArtifactsOutput,
)
from app.application.evidence.import_bundle import ImportEvidenceBundleCapability
from app.application.evidence.ports import (
    EvidenceBundleConflictError,
    EvidenceBundleInputError,
    EvidenceBundleLimitError,
)
from app.application.evidence.report_generation import GenerateEvidenceReportCapability
from app.application.evidence.run_listing import ListEvidenceRunsCapability
from app.application.evidence.run_summary import (
    EvidenceRunNotFoundError,
    GetRunSummaryCapability,
)
from app.infrastructure.evidence.local_repository import LocalEvidenceRunRepository
from app.models.api import ErrorResponse

router = APIRouter(prefix="/api/evidence", tags=["evidence"])

DATA_ROOT = Path(__file__).resolve().parents[3] / "data" / "evidence-fixtures"
_TEMP_UPLOAD_DIRECTORY = TemporaryDirectory(prefix="molecule-atlas-evidence-")
_EVIDENCE_REPOSITORY = LocalEvidenceRunRepository(
    (DATA_ROOT,),
    upload_root=Path(_TEMP_UPLOAD_DIRECTORY.name),
)
_RUN_SUMMARY_CAPABILITY = GetRunSummaryCapability(_EVIDENCE_REPOSITORY)
_IMPORT_EVIDENCE_CAPABILITY = ImportEvidenceBundleCapability(_EVIDENCE_REPOSITORY)
_LIST_ARTIFACTS_CAPABILITY = ListAvailableArtifactsCapability(_EVIDENCE_REPOSITORY)
_VALIDATE_ARTIFACTS_CAPABILITY = ValidateEvidenceArtifactsCapability(_EVIDENCE_REPOSITORY)
_GET_CANDIDATE_EVIDENCE_CAPABILITY = GetCandidateEvidenceCapability(_EVIDENCE_REPOSITORY)
_LIST_EVIDENCE_RUNS_CAPABILITY = ListEvidenceRunsCapability(_EVIDENCE_REPOSITORY)
_COMPARE_CANDIDATES_CAPABILITY = CompareCandidatesCapability(_EVIDENCE_REPOSITORY)
_GENERATE_EVIDENCE_REPORT_CAPABILITY = GenerateEvidenceReportCapability(_EVIDENCE_REPOSITORY)

CorrelationHeader = Annotated[
    str | None,
    Header(
        alias="X-Correlation-ID",
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$",
    ),
]
IdempotencyHeader = Annotated[
    str,
    Header(
        alias="Idempotency-Key",
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$",
    ),
]
EvidenceBundleUpload = Annotated[
    UploadFile,
    File(description="Portable Molecule Atlas evidence bundle ZIP"),
]
_ZIP_MEDIA_TYPES = frozenset({"application/zip", "application/x-zip-compressed"})


def get_run_summary_capability() -> GetRunSummaryCapability:
    return _RUN_SUMMARY_CAPABILITY


def get_import_evidence_capability() -> ImportEvidenceBundleCapability:
    return _IMPORT_EVIDENCE_CAPABILITY


def get_list_available_artifacts_capability() -> ListAvailableArtifactsCapability:
    return _LIST_ARTIFACTS_CAPABILITY


def get_validate_evidence_artifacts_capability() -> ValidateEvidenceArtifactsCapability:
    return _VALIDATE_ARTIFACTS_CAPABILITY


def get_candidate_evidence_capability() -> GetCandidateEvidenceCapability:
    return _GET_CANDIDATE_EVIDENCE_CAPABILITY


def get_list_evidence_runs_capability() -> ListEvidenceRunsCapability:
    return _LIST_EVIDENCE_RUNS_CAPABILITY


def get_compare_candidates_capability() -> CompareCandidatesCapability:
    return _COMPARE_CANDIDATES_CAPABILITY


def get_generate_evidence_report_capability() -> GenerateEvidenceReportCapability:
    return _GENERATE_EVIDENCE_REPORT_CAPABILITY


def _local_context(correlation_id: str | None) -> CapabilityContext:
    return CapabilityContext(
        actor=ActorContext(
            actor_id="local-anonymous-browser",
            actor_type="human",
            permissions=("evidence:import", "evidence:read"),
        ),
        correlation_id=correlation_id or f"corr-{uuid4().hex}",
        causation_id=None,
    )


@router.get(
    "/runs",
    operation_id="list_evidence_runs",
    response_model=ListEvidenceRunsOutput,
)
def list_evidence_runs(
    response: Response,
    capability: Annotated[
        ListEvidenceRunsCapability,
        Depends(get_list_evidence_runs_capability),
    ],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=MAX_RUN_PAGE_SIZE)] = DEFAULT_RUN_PAGE_SIZE,
    x_correlation_id: CorrelationHeader = None,
) -> ListEvidenceRunsOutput:
    context = _local_context(x_correlation_id)
    result = capability.execute(
        ListEvidenceRunsInput(offset=offset, limit=limit),
        context=context,
    )
    response.headers["X-Correlation-ID"] = result.correlation_id
    return result


@router.post(
    "/comparisons",
    operation_id="compare_candidates",
    response_model=CompareCandidatesOutput,
    responses={404: {"model": ErrorResponse, "description": "Evidence run not found"}},
)
def compare_candidates(
    request: CompareCandidatesInput,
    response: Response,
    capability: Annotated[
        CompareCandidatesCapability,
        Depends(get_compare_candidates_capability),
    ],
    x_correlation_id: CorrelationHeader = None,
) -> CompareCandidatesOutput:
    context = _local_context(x_correlation_id)
    try:
        result = capability.execute(request, context=context)
    except EvidenceRunNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    response.headers["X-Correlation-ID"] = result.correlation_id
    return result


@router.get(
    "/runs/{run_id}",
    operation_id="get_run_summary",
    response_model=GetRunSummaryOutput,
    responses={404: {"model": ErrorResponse, "description": "Evidence run not found"}},
)
def get_run_summary(
    run_id: str,
    response: Response,
    capability: Annotated[GetRunSummaryCapability, Depends(get_run_summary_capability)],
    x_correlation_id: CorrelationHeader = None,
) -> GetRunSummaryOutput:
    context = _local_context(x_correlation_id)
    try:
        result = capability.execute(GetRunSummaryInput(run_id=run_id), context=context)
    except EvidenceRunNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    response.headers["X-Correlation-ID"] = result.correlation_id
    return result


@router.get(
    "/runs/{run_id}/report",
    operation_id="generate_evidence_report",
    response_model=GenerateEvidenceReportOutput,
    responses={404: {"model": ErrorResponse, "description": "Evidence run not found"}},
)
def generate_evidence_report(
    run_id: str,
    response: Response,
    capability: Annotated[
        GenerateEvidenceReportCapability,
        Depends(get_generate_evidence_report_capability),
    ],
    report_format: Annotated[EvidenceReportFormat, Query()] = "markdown",
    x_correlation_id: CorrelationHeader = None,
) -> GenerateEvidenceReportOutput:
    context = _local_context(x_correlation_id)
    try:
        result = capability.execute(
            GenerateEvidenceReportInput(run_id=run_id, report_format=report_format),
            context=context,
        )
    except EvidenceRunNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    response.headers["X-Correlation-ID"] = result.correlation_id
    return result


@router.get(
    "/runs/{run_id}/artifacts",
    operation_id="list_available_artifacts",
    response_model=ListAvailableArtifactsOutput,
    responses={404: {"model": ErrorResponse, "description": "Evidence run not found"}},
)
def list_available_artifacts(
    run_id: str,
    response: Response,
    capability: Annotated[
        ListAvailableArtifactsCapability,
        Depends(get_list_available_artifacts_capability),
    ],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=MAX_ARTIFACT_PAGE_SIZE)] = DEFAULT_ARTIFACT_PAGE_SIZE,
    x_correlation_id: CorrelationHeader = None,
) -> ListAvailableArtifactsOutput:
    context = _local_context(x_correlation_id)
    try:
        result = capability.execute(
            ListAvailableArtifactsInput(
                run_id=run_id,
                offset=offset,
                limit=limit,
            ),
            context=context,
        )
    except EvidenceRunNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    response.headers["X-Correlation-ID"] = result.correlation_id
    return result


@router.get(
    "/runs/{run_id}/artifact-validation",
    operation_id="validate_evidence_artifacts",
    response_model=ValidateEvidenceArtifactsOutput,
    responses={404: {"model": ErrorResponse, "description": "Evidence run not found"}},
)
def validate_evidence_artifacts(
    run_id: str,
    response: Response,
    capability: Annotated[
        ValidateEvidenceArtifactsCapability,
        Depends(get_validate_evidence_artifacts_capability),
    ],
    x_correlation_id: CorrelationHeader = None,
) -> ValidateEvidenceArtifactsOutput:
    context = _local_context(x_correlation_id)
    try:
        result = capability.execute(
            ValidateEvidenceArtifactsInput(run_id=run_id),
            context=context,
        )
    except EvidenceRunNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    response.headers["X-Correlation-ID"] = result.correlation_id
    return result


@router.get(
    "/runs/{run_id}/candidates/{candidate_id}/evidence",
    operation_id="get_candidate_evidence",
    response_model=GetCandidateEvidenceOutput,
    responses={404: {"model": ErrorResponse, "description": "Evidence run not found"}},
)
def get_candidate_evidence(
    run_id: str,
    candidate_id: str,
    response: Response,
    capability: Annotated[
        GetCandidateEvidenceCapability,
        Depends(get_candidate_evidence_capability),
    ],
    candidate_external_id: Annotated[
        str | None,
        Query(min_length=1, max_length=200),
    ] = None,
    prediction_limit: Annotated[
        int,
        Query(ge=1, le=MAX_CANDIDATE_PREDICTION_LIMIT),
    ] = DEFAULT_CANDIDATE_PREDICTION_LIMIT,
    validation_limit: Annotated[
        int,
        Query(ge=1, le=MAX_CANDIDATE_VALIDATION_LIMIT),
    ] = DEFAULT_CANDIDATE_VALIDATION_LIMIT,
    x_correlation_id: CorrelationHeader = None,
) -> GetCandidateEvidenceOutput:
    context = _local_context(x_correlation_id)
    try:
        result = capability.execute(
            GetCandidateEvidenceInput(
                run_id=run_id,
                candidate_id=candidate_id,
                candidate_external_id=candidate_external_id,
                prediction_limit=prediction_limit,
                validation_limit=validation_limit,
            ),
            context=context,
        )
    except EvidenceRunNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    response.headers["X-Correlation-ID"] = result.correlation_id
    return result


@router.post(
    "/imports",
    operation_id="import_evidence_bundle",
    response_model=ImportEvidenceBundleOutput,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Unsafe or invalid evidence bundle"},
        409: {"model": ErrorResponse, "description": "Import conflict"},
        413: {"model": ErrorResponse, "description": "Evidence bundle limit exceeded"},
    },
)
async def import_evidence_bundle(
    response: Response,
    bundle: EvidenceBundleUpload,
    idempotency_key: IdempotencyHeader,
    capability: Annotated[
        ImportEvidenceBundleCapability,
        Depends(get_import_evidence_capability),
    ],
    x_correlation_id: CorrelationHeader = None,
) -> ImportEvidenceBundleOutput:
    context = _local_context(x_correlation_id)
    error_headers = {"X-Correlation-ID": context.correlation_id}
    if bundle.content_type not in _ZIP_MEDIA_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Evidence bundle must use the application/zip media type",
            headers=error_headers,
        )
    if bundle.filename is None or not bundle.filename.lower().endswith(".zip"):
        raise HTTPException(
            status_code=400,
            detail="Evidence bundle filename must end with .zip",
            headers=error_headers,
        )

    archive_bytes = await bundle.read(MAX_EVIDENCE_BUNDLE_BYTES + 1)
    if len(archive_bytes) > MAX_EVIDENCE_BUNDLE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=(f"Evidence bundle exceeds the {MAX_EVIDENCE_BUNDLE_BYTES}-byte limit"),
            headers=error_headers,
        )

    request = ImportEvidenceBundleInput(
        archive_bytes=archive_bytes,
        original_filename=bundle.filename,
        idempotency_key=idempotency_key,
    )
    try:
        result = capability.execute(request, context=context)
    except EvidenceBundleLimitError as error:
        raise HTTPException(
            status_code=413,
            detail=str(error),
            headers=error_headers,
        ) from error
    except EvidenceBundleConflictError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
            headers=error_headers,
        ) from error
    except EvidenceBundleInputError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
            headers=error_headers,
        ) from error
    response.headers["X-Correlation-ID"] = result.correlation_id
    return result
