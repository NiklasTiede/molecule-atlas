from datetime import datetime
from typing import Literal, cast

from molecule_atlas.evidence.artifacts import ArtifactCheck
from molecule_atlas.evidence.models import (
    ArtifactRole,
    ManifestWarning,
    Prediction,
    RunFailure,
    RunState,
    ValidationResult,
)
from molecule_atlas.evidence.semantic_artifacts import (
    ArtifactSemanticRole,
    ArtifactType,
)
from pydantic import Field, JsonValue, field_validator, model_validator

from app.models.base import ApiModel

MAX_EVIDENCE_BUNDLE_BYTES = 10 * 1024 * 1024
DEFAULT_ARTIFACT_PAGE_SIZE = 50
MAX_ARTIFACT_PAGE_SIZE = 200
DEFAULT_CANDIDATE_PREDICTION_LIMIT = 50
MAX_CANDIDATE_PREDICTION_LIMIT = 100
DEFAULT_CANDIDATE_VALIDATION_LIMIT = 100
MAX_CANDIDATE_VALIDATION_LIMIT = 200
DEFAULT_RUN_PAGE_SIZE = 20
MAX_RUN_PAGE_SIZE = 100
MAX_COMPARISON_SUBJECTS = 10

CandidateBindingStatus = Literal["bound", "unbound", "ambiguous"]
CandidateEvidenceWarningCode = Literal[
    "candidate_not_bound",
    "ambiguous_candidate_binding",
    "semantic_lineage_unavailable",
    "prediction_limit_reached",
    "validation_limit_reached",
]
EvidenceReportFormat = Literal["markdown", "html"]
ComparisonWarningCode = Literal[
    "comparison_subject_unbound",
    "comparison_subject_ambiguous",
    "no_shared_prediction_groups",
]
PredictionType = Literal[
    "docking_energy",
    "pose_confidence",
    "structure_confidence",
    "binder_probability",
    "predicted_affinity",
]
OptimizationDirection = Literal["lower_is_better", "higher_is_better", "none"]


class ImportEvidenceBundleInput(ApiModel):
    contract_version: Literal["0.1.0"] = "0.1.0"
    archive_bytes: bytes = Field(min_length=1, max_length=MAX_EVIDENCE_BUNDLE_BYTES)
    original_filename: str = Field(min_length=1, max_length=255, pattern=r"^.+\.[zZ][iI][pP]$")
    idempotency_key: str = Field(
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$",
    )


class GetRunSummaryInput(ApiModel):
    contract_version: Literal["0.1.0"] = "0.1.0"
    run_id: str = Field(min_length=1, max_length=200)


class ListEvidenceRunsInput(ApiModel):
    contract_version: Literal["0.1.0"] = "0.1.0"
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=DEFAULT_RUN_PAGE_SIZE, ge=1, le=MAX_RUN_PAGE_SIZE)


class ListAvailableArtifactsInput(ApiModel):
    contract_version: Literal["0.1.0"] = "0.1.0"
    run_id: str = Field(min_length=1, max_length=200)
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=DEFAULT_ARTIFACT_PAGE_SIZE, ge=1, le=MAX_ARTIFACT_PAGE_SIZE)


class ValidateEvidenceArtifactsInput(ApiModel):
    contract_version: Literal["0.1.0"] = "0.1.0"
    run_id: str = Field(min_length=1, max_length=200)


class GetCandidateEvidenceInput(ApiModel):
    contract_version: Literal["0.1.0"] = "0.1.0"
    run_id: str = Field(min_length=1, max_length=200)
    candidate_id: str = Field(min_length=1, max_length=200)
    candidate_external_id: str | None = Field(default=None, min_length=1, max_length=200)
    prediction_limit: int = Field(
        default=DEFAULT_CANDIDATE_PREDICTION_LIMIT,
        ge=1,
        le=MAX_CANDIDATE_PREDICTION_LIMIT,
    )
    validation_limit: int = Field(
        default=DEFAULT_CANDIDATE_VALIDATION_LIMIT,
        ge=1,
        le=MAX_CANDIDATE_VALIDATION_LIMIT,
    )


class ComparisonSubjectInput(ApiModel):
    subject_id: str = Field(min_length=1, max_length=200)
    label: str = Field(min_length=1, max_length=200)
    run_id: str = Field(min_length=1, max_length=200)
    candidate_id: str = Field(min_length=1, max_length=200)
    candidate_external_id: str | None = Field(default=None, min_length=1, max_length=200)


class CompareCandidatesInput(ApiModel):
    contract_version: Literal["0.1.0"] = "0.1.0"
    subjects: tuple[ComparisonSubjectInput, ...] = Field(
        min_length=2,
        max_length=MAX_COMPARISON_SUBJECTS,
    )

    @field_validator("subjects", mode="before")
    @classmethod
    def accept_json_array(cls, value: object) -> object:
        return tuple(cast(list[object], value)) if isinstance(value, list) else value

    @model_validator(mode="after")
    def validate_unique_subject_ids(self) -> "CompareCandidatesInput":
        subject_ids = tuple(subject.subject_id for subject in self.subjects)
        if len(set(subject_ids)) != len(subject_ids):
            raise ValueError("comparison subject IDs must be unique")
        return self


class GenerateEvidenceReportInput(ApiModel):
    contract_version: Literal["0.1.0"] = "0.1.0"
    run_id: str = Field(min_length=1, max_length=200)
    report_format: EvidenceReportFormat


class MethodSummary(ApiModel):
    method_id: str
    adapter_id: str
    adapter_version: str
    upstream_tool: str | None
    upstream_version: str | None
    source_commit: str | None
    checkpoint_id: str | None
    checkpoint_sha256: str | None
    container_image: str | None
    container_digest: str | None
    command: tuple[str, ...]
    random_seeds: tuple[int, ...]


class CandidateEvidenceBinding(ApiModel):
    status: CandidateBindingStatus
    candidate_id: str
    candidate_external_id: str | None
    reference_ids_checked: tuple[str, ...]
    matched_input_ids: tuple[str, ...]
    matched_input_artifact_ids: tuple[str, ...]
    explanation: str


class CandidateEvidenceWarning(ApiModel):
    code: CandidateEvidenceWarningCode
    message: str


class ValidationCounts(ApiModel):
    pass_count: int = Field(ge=0)
    fail_count: int = Field(ge=0)
    warning_count: int = Field(ge=0)
    unavailable_count: int = Field(ge=0)
    error_count: int = Field(ge=0)


class LigandInputSummary(ApiModel):
    input_id: str
    artifact_id: str
    representation: str | None
    upstream_id: str | None


class RunSummary(ApiModel):
    run_id: str
    schema_version: str
    state: RunState
    started_at: datetime | None
    finished_at: datetime | None
    expected_outputs: tuple[str, ...]
    missing_outputs: tuple[str, ...]
    failure: RunFailure | None
    method: MethodSummary
    ligand_inputs: tuple[LigandInputSummary, ...]
    artifact_count: int = Field(ge=0)
    prediction_count: int = Field(ge=0)
    validation_counts: ValidationCounts
    warnings: tuple[ManifestWarning, ...]


class GetRunSummaryOutput(ApiModel):
    contract_version: Literal["0.1.0"] = "0.1.0"
    capability_id: Literal["get_run_summary"] = "get_run_summary"
    capability_version: Literal["0.1.0"] = "0.1.0"
    correlation_id: str
    run: RunSummary


class ListEvidenceRunsOutput(ApiModel):
    contract_version: Literal["0.1.0"] = "0.1.0"
    capability_id: Literal["list_evidence_runs"] = "list_evidence_runs"
    capability_version: Literal["0.1.0"] = "0.1.0"
    correlation_id: str
    total: int = Field(ge=0)
    offset: int = Field(ge=0)
    limit: int = Field(ge=1, le=MAX_RUN_PAGE_SIZE)
    runs: tuple[RunSummary, ...]


class ImportEvidenceBundleOutput(ApiModel):
    contract_version: Literal["0.1.0"] = "0.1.0"
    capability_id: Literal["import_evidence_bundle"] = "import_evidence_bundle"
    capability_version: Literal["0.1.0"] = "0.1.0"
    correlation_id: str
    idempotency_replayed: bool
    run: RunSummary


class GetCandidateEvidenceOutput(ApiModel):
    contract_version: Literal["0.1.0"] = "0.1.0"
    capability_id: Literal["get_candidate_evidence"] = "get_candidate_evidence"
    capability_version: Literal["0.1.0"] = "0.1.0"
    correlation_id: str
    run_id: str
    binding: CandidateEvidenceBinding
    method: MethodSummary
    lineage_available: bool
    related_artifact_ids: tuple[str, ...]
    prediction_total: int = Field(ge=0)
    prediction_limit: int = Field(ge=1, le=MAX_CANDIDATE_PREDICTION_LIMIT)
    predictions: tuple[Prediction, ...]
    validation_total: int = Field(ge=0)
    validation_limit: int = Field(ge=1, le=MAX_CANDIDATE_VALIDATION_LIMIT)
    validation_results: tuple[ValidationResult, ...]
    warnings: tuple[CandidateEvidenceWarning, ...]


class ComparisonWarning(ApiModel):
    code: ComparisonWarningCode
    message: str
    subject_id: str | None = None


class ComparisonSubjectResult(ApiModel):
    subject_id: str
    label: str
    run_id: str
    candidate_id: str
    candidate_external_id: str | None
    binding: CandidateEvidenceBinding
    method: MethodSummary
    validation_counts: ValidationCounts
    related_artifact_ids: tuple[str, ...]


class ComparisonPredictionEntry(ApiModel):
    subject_id: str
    run_id: str
    candidate_id: str
    prediction: Prediction


class PredictionComparisonGroup(ApiModel):
    prediction_type: PredictionType
    unit: str | None
    optimization_direction: OptimizationDirection
    entries: tuple[ComparisonPredictionEntry, ...]


class CompareCandidatesOutput(ApiModel):
    contract_version: Literal["0.1.0"] = "0.1.0"
    capability_id: Literal["compare_candidates"] = "compare_candidates"
    capability_version: Literal["0.1.0"] = "0.1.0"
    correlation_id: str
    subjects: tuple[ComparisonSubjectResult, ...]
    prediction_groups: tuple[PredictionComparisonGroup, ...]
    excluded_prediction_count: int = Field(ge=0)
    warnings: tuple[ComparisonWarning, ...]


class GenerateEvidenceReportOutput(ApiModel):
    contract_version: Literal["0.1.0"] = "0.1.0"
    capability_id: Literal["generate_evidence_report"] = "generate_evidence_report"
    capability_version: Literal["0.1.0"] = "0.1.0"
    correlation_id: str
    run_id: str
    report_format: EvidenceReportFormat
    media_type: str
    filename: str
    content: str


class SemanticArtifactSummary(ApiModel):
    logical_name: str
    artifact_type: ArtifactType
    schema_version: str | None
    semantic_role: ArtifactSemanticRole
    derived_from_artifact_ids: tuple[str, ...]
    domain_metadata: dict[str, JsonValue]
    preview_metadata: dict[str, JsonValue]


class AvailableArtifact(ApiModel):
    artifact_id: str
    role: ArtifactRole
    path_or_uri: str
    original_name: str
    media_type: str
    content_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    size_bytes: int = Field(ge=0)
    created_by_stage: str
    source_metadata: dict[str, JsonValue]
    verification: ArtifactCheck
    semantic: SemanticArtifactSummary | None


class ListAvailableArtifactsOutput(ApiModel):
    contract_version: Literal["0.1.0"] = "0.1.0"
    capability_id: Literal["list_available_artifacts"] = "list_available_artifacts"
    capability_version: Literal["0.1.0"] = "0.1.0"
    correlation_id: str
    run_id: str
    total: int = Field(ge=0)
    offset: int = Field(ge=0)
    limit: int = Field(ge=1, le=MAX_ARTIFACT_PAGE_SIZE)
    artifacts: tuple[AvailableArtifact, ...]


class ArtifactCheckCounts(ApiModel):
    verified_count: int = Field(ge=0)
    missing_count: int = Field(ge=0)
    mismatch_count: int = Field(ge=0)
    external_count: int = Field(ge=0)
    unsafe_path_count: int = Field(ge=0)
    unreadable_count: int = Field(ge=0)


class ValidateEvidenceArtifactsOutput(ApiModel):
    contract_version: Literal["0.1.0"] = "0.1.0"
    capability_id: Literal["validate_evidence_artifacts"] = "validate_evidence_artifacts"
    capability_version: Literal["0.1.0"] = "0.1.0"
    correlation_id: str
    run_id: str
    counts: ArtifactCheckCounts
    artifact_checks: tuple[ArtifactCheck, ...]
    warnings: tuple[ManifestWarning, ...]
