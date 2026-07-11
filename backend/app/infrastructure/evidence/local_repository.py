from collections.abc import Iterable
from pathlib import Path

from molecule_atlas.evidence.adapters.manifest import MANIFEST_FILENAME
from molecule_atlas.evidence.serialization import load_manifest

from app.application.evidence.ports import StoredEvidenceRun


class LocalEvidenceRunRepository:
    """Read-only local manifest index used before persistent projects exist."""

    def __init__(self, roots: Iterable[Path]) -> None:
        by_run_id: dict[str, StoredEvidenceRun] = {}
        for root in roots:
            if not root.is_dir():
                continue
            for manifest_path in sorted(root.rglob(MANIFEST_FILENAME)):
                manifest = load_manifest(manifest_path)
                run_id = manifest.run.id
                if run_id in by_run_id:
                    raise ValueError(f"duplicate local evidence run ID: {run_id}")
                by_run_id[run_id] = StoredEvidenceRun(
                    root=manifest_path.parent,
                    manifest=manifest,
                )
        self._by_run_id = by_run_id

    def find(self, run_id: str) -> StoredEvidenceRun | None:
        return self._by_run_id.get(run_id)
