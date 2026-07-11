from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from molecule_atlas.evidence.models import RunManifest


@dataclass(frozen=True, slots=True)
class StoredEvidenceRun:
    root: Path
    manifest: RunManifest


class EvidenceRunRepository(Protocol):
    def find(self, run_id: str) -> StoredEvidenceRun | None: ...
