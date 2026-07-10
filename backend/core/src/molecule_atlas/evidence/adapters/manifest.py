from pathlib import Path

from pydantic import ValidationError

from molecule_atlas.evidence.adapters.contracts import (
    AdapterImportRequest,
    AdapterImportResult,
    AdapterMetadata,
    EvidenceInputError,
)
from molecule_atlas.evidence.serialization import load_manifest

MANIFEST_FILENAME = "molecule-atlas-run.json"

_METADATA = AdapterMetadata(
    adapter_id="manifest",
    adapter_version="0.1.0",
    title="Molecule Atlas run manifest",
    description="Imports an already normalized Molecule Atlas RunManifest bundle.",
    upstream_tool=None,
    source_format="molecule-atlas-run-manifest",
    source_format_version="0.1.0",
    verified_upstream_versions=(),
    supported_manifest_versions=("0.1.0",),
)


def resolve_manifest_path(path: Path) -> Path:
    if not path.exists():
        raise EvidenceInputError(f"Input path does not exist: {path}")
    manifest_path = path / MANIFEST_FILENAME if path.is_dir() else path
    if not manifest_path.is_file():
        raise EvidenceInputError(f"Manifest does not exist: {manifest_path}")
    return manifest_path


class ManifestAdapter:
    """Importer for bundles that already contain RunManifest 0.1.0."""

    @property
    def metadata(self) -> AdapterMetadata:
        return _METADATA

    def import_evidence(self, request: AdapterImportRequest) -> AdapterImportResult:
        manifest_path = resolve_manifest_path(request.source_path)
        try:
            manifest = load_manifest(manifest_path)
        except ValidationError as error:
            raise EvidenceInputError(
                f"Manifest validation failed for {manifest_path}: {error}"
            ) from error
        return AdapterImportResult(
            adapter_id=self.metadata.adapter_id,
            adapter_version=self.metadata.adapter_version,
            artifact_root=manifest_path.parent,
            manifest=manifest,
        )
