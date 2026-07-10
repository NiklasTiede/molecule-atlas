from pathlib import Path
from typing import Literal, Self

from pydantic import Field, model_validator

from molecule_atlas.evidence.models import (
    Artifact,
    EvidenceModel,
    ManifestWarning,
    ValidationResult,
)
from molecule_atlas.evidence.semantic_artifacts import SemanticArtifact

ValidationConfig = Literal["mol", "dock", "redock"]

_SEMVER_PATTERN = (
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$"
)


class ValidationInputError(ValueError):
    """Raised when a raw validator report cannot be normalized safely."""


class PoseBustersCompatibilityError(ValidationInputError):
    """Raised when a report claims an unverified PoseBusters version."""


class PoseBustersUnavailableError(RuntimeError):
    """Raised when optional PoseBusters execution was requested but is unavailable."""


class PoseBustersExecutionError(RuntimeError):
    """Raised when the optional upstream validator fails to produce a report."""


class ValidatorMetadata(EvidenceModel):
    """Pinned compatibility metadata for one scientific validator integration."""

    validator_id: str = Field(pattern=r"^[a-z][a-z0-9]*(?:[-_][a-z0-9]+)*$")
    integration_version: str = Field(pattern=_SEMVER_PATTERN)
    upstream_tool: str = Field(min_length=1)
    verified_upstream_versions: tuple[str, ...] = Field(min_length=1)
    configurations: tuple[ValidationConfig, ...] = Field(min_length=1)
    optional_dependency: str = Field(min_length=1)


class PoseBustersNormalizationRequest(EvidenceModel):
    """Input contract for normalizing an existing PoseBusters full-report CSV."""

    contract_version: Literal["0.1.0"] = "0.1.0"
    report_path: Path
    artifact_root: Path
    input_artifact_id: str = Field(min_length=1)
    raw_output_artifact_id: str = Field(default="posebusters-raw-report", min_length=1)
    validator_version: str = Field(pattern=_SEMVER_PATTERN)
    config: ValidationConfig


class PoseBustersExecutionRequest(EvidenceModel):
    """Typed request for optional local CPU validation through PoseBusters."""

    contract_version: Literal["0.1.0"] = "0.1.0"
    mol_pred: Path
    mol_true: Path | None = None
    mol_cond: Path | None = None
    config: ValidationConfig
    artifact_root: Path
    report_path: Path
    input_artifact_id: str = Field(min_length=1)
    raw_output_artifact_id: str = Field(default="posebusters-raw-report", min_length=1)

    @model_validator(mode="after")
    def validate_configuration_inputs(self) -> Self:
        if self.config == "dock" and self.mol_cond is None:
            raise ValueError("dock validation requires mol_cond")
        if self.config == "redock" and (self.mol_true is None or self.mol_cond is None):
            raise ValueError("redock validation requires mol_true and mol_cond")
        return self


class PoseBustersNormalizationResult(EvidenceModel):
    """Portable normalized checks plus the content-addressed raw report."""

    contract_version: Literal["0.1.0"] = "0.1.0"
    validator_id: Literal["posebusters"] = "posebusters"
    integration_version: Literal["0.1.0"] = "0.1.0"
    validator_version: str = Field(pattern=_SEMVER_PATTERN)
    config: ValidationConfig
    artifact_root: Path
    raw_report_artifact: Artifact
    semantic_artifact: SemanticArtifact
    validation_results: tuple[ValidationResult, ...]
    warnings: tuple[ManifestWarning, ...]

    @model_validator(mode="after")
    def validate_raw_lineage(self) -> Self:
        raw = self.raw_report_artifact
        semantic = self.semantic_artifact
        if semantic.artifact_id != raw.id:
            raise ValueError("semantic validation report must reference the raw report artifact")
        comparisons = (
            (semantic.path_or_uri, raw.path_or_uri),
            (semantic.media_type, raw.media_type),
            (semantic.content_digest, f"sha256:{raw.sha256}"),
            (semantic.size_bytes, raw.size_bytes),
        )
        if any(left != right for left, right in comparisons):
            raise ValueError("semantic validation report does not match raw report inventory")
        if any(result.raw_output_artifact_id != raw.id for result in self.validation_results):
            raise ValueError("normalized validation result does not reference the raw report")
        return self
