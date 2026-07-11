from datetime import datetime
from typing import Literal

from molecule_atlas.evidence.artifacts import ArtifactCheck
from molecule_atlas.evidence.models import ArtifactRole, ManifestWarning, RunFailure, RunState
from molecule_atlas.evidence.semantic_artifacts import (
    ArtifactSemanticRole,
    ArtifactType,
)
from pydantic import Field, JsonValue

from app.models.base import ApiModel

MAX_EVIDENCE_BUNDLE_BYTES = 10 * 1024 * 1024
DEFAULT_ARTIFACT_PAGE_SIZE = 50
MAX_ARTIFACT_PAGE_SIZE = 200


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


class ListAvailableArtifactsInput(ApiModel):
    contract_version: Literal["0.1.0"] = "0.1.0"
    run_id: str = Field(min_length=1, max_length=200)
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=DEFAULT_ARTIFACT_PAGE_SIZE, ge=1, le=MAX_ARTIFACT_PAGE_SIZE)


class ValidateEvidenceArtifactsInput(ApiModel):
    contract_version: Literal["0.1.0"] = "0.1.0"
    run_id: str = Field(min_length=1, max_length=200)


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


class ValidationCounts(ApiModel):
    pass_count: int = Field(ge=0)
    fail_count: int = Field(ge=0)
    warning_count: int = Field(ge=0)
    unavailable_count: int = Field(ge=0)
    error_count: int = Field(ge=0)


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


class ImportEvidenceBundleOutput(ApiModel):
    contract_version: Literal["0.1.0"] = "0.1.0"
    capability_id: Literal["import_evidence_bundle"] = "import_evidence_bundle"
    capability_version: Literal["0.1.0"] = "0.1.0"
    correlation_id: str
    idempotency_replayed: bool
    run: RunSummary


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
