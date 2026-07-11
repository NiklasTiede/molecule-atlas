from datetime import datetime
from typing import Literal

from molecule_atlas.evidence.models import ManifestWarning, RunFailure, RunState
from pydantic import Field

from app.models.base import ApiModel


class GetRunSummaryInput(ApiModel):
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
