from pathlib import Path

from molecule_atlas.evidence.adapters.contracts import (
    AdapterImportRequest,
    AdapterMetadata,
    EvidenceAdapter,
    EvidenceInputError,
)
from molecule_atlas.evidence.adapters.manifest import ManifestAdapter
from molecule_atlas.evidence.audit import ManifestAudit, audit_manifest

_ADAPTERS: tuple[EvidenceAdapter, ...] = (ManifestAdapter(),)
SUPPORTED_ADAPTERS = tuple(adapter.metadata.adapter_id for adapter in _ADAPTERS)


def list_adapters() -> tuple[AdapterMetadata, ...]:
    """Return compatibility metadata for installed adapters in stable order."""

    return tuple(adapter.metadata for adapter in _ADAPTERS)


def get_adapter(adapter_id: str) -> EvidenceAdapter:
    """Return one explicitly registered adapter."""

    for adapter in _ADAPTERS:
        if adapter.metadata.adapter_id == adapter_id:
            return adapter
    supported = ", ".join(SUPPORTED_ADAPTERS)
    raise EvidenceInputError(f"Unsupported adapter {adapter_id!r}. Supported adapters: {supported}")


def audit_path(path: Path, *, adapter: str = "manifest") -> ManifestAudit:
    importer = get_adapter(adapter)
    imported = importer.import_evidence(AdapterImportRequest(source_path=path))
    return audit_manifest(imported.manifest, root=imported.artifact_root)
