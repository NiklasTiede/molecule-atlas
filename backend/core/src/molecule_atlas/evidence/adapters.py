from pathlib import Path

from pydantic import ValidationError

from molecule_atlas.evidence.audit import ManifestAudit, audit_manifest
from molecule_atlas.evidence.serialization import load_manifest

MANIFEST_FILENAME = "molecule-atlas-run.json"
SUPPORTED_ADAPTERS = ("manifest",)


class EvidenceInputError(ValueError):
    """Raised when a CLI input cannot be interpreted as portable evidence."""


def resolve_manifest_path(path: Path) -> Path:
    if not path.exists():
        raise EvidenceInputError(f"Input path does not exist: {path}")
    manifest_path = path / MANIFEST_FILENAME if path.is_dir() else path
    if not manifest_path.is_file():
        raise EvidenceInputError(f"Manifest does not exist: {manifest_path}")
    return manifest_path


def audit_path(path: Path, *, adapter: str = "manifest") -> ManifestAudit:
    if adapter not in SUPPORTED_ADAPTERS:
        supported = ", ".join(SUPPORTED_ADAPTERS)
        raise EvidenceInputError(
            f"Unsupported adapter {adapter!r}. Milestone 1 supports: {supported}"
        )
    manifest_path = resolve_manifest_path(path)
    try:
        manifest = load_manifest(manifest_path)
    except ValidationError as error:
        raise EvidenceInputError(
            f"Manifest validation failed for {manifest_path}: {error}"
        ) from error
    return audit_manifest(manifest, root=manifest_path.parent)
