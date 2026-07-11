from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Header, HTTPException, Response, UploadFile, status

from app.application.capabilities.models import ActorContext, CapabilityContext
from app.application.evidence.contracts import (
    MAX_EVIDENCE_BUNDLE_BYTES,
    GetRunSummaryInput,
    GetRunSummaryOutput,
    ImportEvidenceBundleInput,
    ImportEvidenceBundleOutput,
)
from app.application.evidence.import_bundle import ImportEvidenceBundleCapability
from app.application.evidence.ports import (
    EvidenceBundleConflictError,
    EvidenceBundleInputError,
    EvidenceBundleLimitError,
)
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
