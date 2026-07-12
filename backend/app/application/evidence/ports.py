from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from molecule_atlas.evidence.models import RunManifest
from molecule_atlas.evidence.semantic_artifacts import ArtifactManifest


@dataclass(frozen=True, slots=True)
class StoredEvidenceRun:
    root: Path
    manifest: RunManifest
    artifact_manifest: ArtifactManifest | None = None


class EvidenceBundleInputError(ValueError):
    """Raised when an uploaded bundle is unsafe or scientifically inconsistent."""


class EvidenceBundleLimitError(EvidenceBundleInputError):
    """Raised when an uploaded bundle exceeds a configured local safety limit."""


class EvidenceBundleConflictError(EvidenceBundleInputError):
    """Raised when an import conflicts with an existing run or idempotency record."""


class EvidenceRunRepository(Protocol):
    def list_runs(self) -> tuple[StoredEvidenceRun, ...]: ...

    def find(self, run_id: str) -> StoredEvidenceRun | None: ...

    def import_bundle(self, archive_bytes: bytes) -> StoredEvidenceRun: ...
