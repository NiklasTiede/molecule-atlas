from pathlib import Path
from typing import Annotated, Literal, Protocol, Self

from pydantic import Field, TypeAdapter, model_validator

from molecule_atlas.evidence.models import EvidenceModel, RunManifest, SchemaVersion
from molecule_atlas.evidence.semantic_artifacts import (
    ArtifactManifest,
    validate_artifact_manifest_against_run,
)

AdapterContractVersion = Literal["0.1.0"]
NonEmptyString = Annotated[str, Field(min_length=1)]

_ADAPTER_ID_PATTERN = r"^[a-z][a-z0-9]*(?:[-_][a-z0-9]+)*$"
_SEMVER_PATTERN = (
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$"
)


class EvidenceInputError(ValueError):
    """Raised when an adapter cannot interpret portable evidence input."""


class AdapterLayoutError(EvidenceInputError):
    """Raised when a tool output directory is malformed or ambiguous."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


class AdapterMetadata(EvidenceModel):
    """Versioned compatibility claims for one installed import adapter."""

    adapter_id: str = Field(pattern=_ADAPTER_ID_PATTERN)
    adapter_version: str = Field(pattern=_SEMVER_PATTERN)
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    upstream_tool: str | None = Field(default=None, min_length=1)
    source_format: str = Field(min_length=1)
    source_format_version: str = Field(min_length=1)
    verified_upstream_versions: tuple[NonEmptyString, ...]
    supported_manifest_versions: tuple[SchemaVersion, ...] = Field(min_length=1)


class AdapterImportRequest(EvidenceModel):
    """Portable input contract for importing one evidence source."""

    contract_version: AdapterContractVersion = "0.1.0"
    source_path: Path


class AdapterImportResult(EvidenceModel):
    """Portable output contract for an imported RunManifest 0.1.0 bundle."""

    contract_version: AdapterContractVersion = "0.1.0"
    adapter_id: str = Field(pattern=_ADAPTER_ID_PATTERN)
    adapter_version: str = Field(pattern=_SEMVER_PATTERN)
    artifact_root: Path
    manifest: RunManifest


class AdapterImportResultV020(EvidenceModel):
    """Portable import result with a semantic artifact inventory."""

    contract_version: Literal["0.2.0"] = "0.2.0"
    adapter_id: str = Field(pattern=_ADAPTER_ID_PATTERN)
    adapter_version: str = Field(pattern=_SEMVER_PATTERN)
    artifact_root: Path
    manifest: RunManifest
    artifact_manifest: ArtifactManifest

    @model_validator(mode="after")
    def validate_artifact_binding(self) -> Self:
        validate_artifact_manifest_against_run(
            self.artifact_manifest,
            run_manifest=self.manifest,
        )
        return self


AdapterImportResultContract = Annotated[
    AdapterImportResult | AdapterImportResultV020,
    Field(discriminator="contract_version"),
]
_ADAPTER_IMPORT_RESULT_ADAPTER: TypeAdapter[AdapterImportResultContract] = TypeAdapter(
    AdapterImportResultContract
)


def validate_adapter_import_result_json(
    data: str | bytes,
) -> AdapterImportResultContract:
    """Parse any supported adapter result using its contract discriminator."""

    return _ADAPTER_IMPORT_RESULT_ADAPTER.validate_json(data)


class EvidenceAdapter(Protocol):
    """Concrete boundary implemented by each built-in evidence adapter."""

    @property
    def metadata(self) -> AdapterMetadata: ...

    def import_evidence(
        self,
        request: AdapterImportRequest,
    ) -> AdapterImportResultContract: ...
