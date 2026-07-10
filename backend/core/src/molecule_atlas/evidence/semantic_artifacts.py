from typing import Literal, Self

from pydantic import Field, JsonValue, model_validator

from molecule_atlas.evidence.models import EvidenceModel, RunManifest

ArtifactManifestSchemaVersion = Literal["0.1.0"]
ArtifactType = Literal[
    "model-input",
    "ligand-structure",
    "protein-structure",
    "predicted-complex",
    "docking-pose-set",
    "raw-prediction-output",
    "validation-report",
    "run-log",
    "evidence-report",
]
ArtifactSemanticRole = Literal[
    "input",
    "primary_output",
    "raw_output",
    "normalized_output",
    "validation_output",
    "log",
    "report",
]

_LOGICAL_NAME_PATTERN = r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$"
_CONTENT_DIGEST_PATTERN = r"^sha256:[0-9a-f]{64}$"


class ArtifactManifestMismatchError(ValueError):
    """Raised when semantic and RunManifest artifact inventories disagree."""


class SemanticArtifact(EvidenceModel):
    """Portable semantic metadata for one content-addressed artifact."""

    artifact_id: str = Field(min_length=1)
    logical_name: str = Field(pattern=_LOGICAL_NAME_PATTERN)
    artifact_type: ArtifactType
    schema_version: str | None = Field(default=None, min_length=1)
    semantic_role: ArtifactSemanticRole
    media_type: str = Field(min_length=1)
    path_or_uri: str = Field(min_length=1)
    content_digest: str = Field(pattern=_CONTENT_DIGEST_PATTERN)
    size_bytes: int = Field(ge=0)
    derived_from_artifact_ids: tuple[str, ...]
    domain_metadata: dict[str, JsonValue]
    preview_metadata: dict[str, JsonValue]


def _duplicates(values: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return tuple(sorted(duplicates))


def _derivation_cycle(artifacts: tuple[SemanticArtifact, ...]) -> tuple[str, ...] | None:
    graph = {artifact.artifact_id: artifact.derived_from_artifact_ids for artifact in artifacts}
    visited: set[str] = set()
    stack: list[str] = []
    positions: dict[str, int] = {}

    def visit(artifact_id: str) -> tuple[str, ...] | None:
        position = positions.get(artifact_id)
        if position is not None:
            return (*stack[position:], artifact_id)
        if artifact_id in visited:
            return None

        positions[artifact_id] = len(stack)
        stack.append(artifact_id)
        for source_id in graph[artifact_id]:
            if cycle := visit(source_id):
                return cycle
        stack.pop()
        positions.pop(artifact_id)
        visited.add(artifact_id)
        return None

    for artifact in artifacts:
        if cycle := visit(artifact.artifact_id):
            return cycle
    return None


class ArtifactManifest(EvidenceModel):
    """Versioned semantic inventory accompanying a portable RunManifest."""

    schema_version: ArtifactManifestSchemaVersion
    artifacts: tuple[SemanticArtifact, ...]

    @model_validator(mode="after")
    def validate_identity_and_derivation(self) -> Self:
        artifact_ids = tuple(artifact.artifact_id for artifact in self.artifacts)
        duplicate_ids = _duplicates(artifact_ids)
        if duplicate_ids:
            raise ValueError(f"duplicate artifact IDs: {', '.join(duplicate_ids)}")

        logical_names = tuple(artifact.logical_name for artifact in self.artifacts)
        duplicate_names = _duplicates(logical_names)
        if duplicate_names:
            raise ValueError(f"duplicate logical names: {', '.join(duplicate_names)}")

        known_ids = set(artifact_ids)
        for artifact in self.artifacts:
            duplicate_sources = _duplicates(artifact.derived_from_artifact_ids)
            if duplicate_sources:
                raise ValueError(
                    f"artifact {artifact.artifact_id} repeats derivation sources: "
                    f"{', '.join(duplicate_sources)}"
                )
            for source_id in artifact.derived_from_artifact_ids:
                if source_id == artifact.artifact_id:
                    raise ValueError(f"artifact {artifact.artifact_id} cannot derive from itself")
                if source_id not in known_ids:
                    raise ValueError(
                        f"artifact {artifact.artifact_id} derives from unknown artifact {source_id}"
                    )

        if cycle := _derivation_cycle(self.artifacts):
            raise ValueError(f"derivation cycle: {' -> '.join(cycle)}")
        return self


def validate_artifact_manifest_against_run(
    artifact_manifest: ArtifactManifest,
    *,
    run_manifest: RunManifest,
) -> None:
    """Require exact agreement between semantic and RunManifest artifact inventories."""

    semantic_by_id = {artifact.artifact_id: artifact for artifact in artifact_manifest.artifacts}
    run_by_id = {artifact.id: artifact for artifact in run_manifest.artifacts}

    missing = tuple(sorted(run_by_id.keys() - semantic_by_id.keys()))
    if missing:
        raise ArtifactManifestMismatchError(f"missing semantic artifacts: {', '.join(missing)}")
    unexpected = tuple(sorted(semantic_by_id.keys() - run_by_id.keys()))
    if unexpected:
        raise ArtifactManifestMismatchError(
            f"semantic artifacts are absent from RunManifest: {', '.join(unexpected)}"
        )

    for artifact_id in sorted(run_by_id):
        semantic = semantic_by_id[artifact_id]
        run_artifact = run_by_id[artifact_id]
        comparisons = (
            ("path", semantic.path_or_uri, run_artifact.path_or_uri),
            ("media type", semantic.media_type, run_artifact.media_type),
            ("content digest", semantic.content_digest, f"sha256:{run_artifact.sha256}"),
            ("size", semantic.size_bytes, run_artifact.size_bytes),
        )
        for label, semantic_value, run_value in comparisons:
            if semantic_value != run_value:
                raise ArtifactManifestMismatchError(
                    f"artifact {artifact_id} {label} does not match RunManifest"
                )
