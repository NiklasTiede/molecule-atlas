"""Typed import adapters for portable scientific evidence."""

from molecule_atlas.evidence.adapters.contracts import (
    AdapterImportRequest,
    AdapterImportResult,
    AdapterMetadata,
    EvidenceAdapter,
    EvidenceInputError,
)
from molecule_atlas.evidence.adapters.manifest import (
    MANIFEST_FILENAME,
    ManifestAdapter,
    resolve_manifest_path,
)
from molecule_atlas.evidence.adapters.registry import (
    SUPPORTED_ADAPTERS,
    audit_path,
    get_adapter,
    list_adapters,
)

__all__ = [
    "MANIFEST_FILENAME",
    "SUPPORTED_ADAPTERS",
    "AdapterImportRequest",
    "AdapterImportResult",
    "AdapterMetadata",
    "EvidenceAdapter",
    "EvidenceInputError",
    "ManifestAdapter",
    "audit_path",
    "get_adapter",
    "list_adapters",
    "resolve_manifest_path",
]
