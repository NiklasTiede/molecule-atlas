"""Typed import adapters for portable scientific evidence."""

from molecule_atlas.evidence.adapters.contracts import (
    AdapterImportRequest,
    AdapterImportResult,
    AdapterImportResultContract,
    AdapterImportResultV020,
    AdapterLayoutError,
    AdapterMetadata,
    EvidenceAdapter,
    EvidenceInputError,
    validate_adapter_import_result_json,
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
    "AdapterImportResultContract",
    "AdapterImportResultV020",
    "AdapterLayoutError",
    "AdapterMetadata",
    "EvidenceAdapter",
    "EvidenceInputError",
    "ManifestAdapter",
    "audit_path",
    "get_adapter",
    "list_adapters",
    "resolve_manifest_path",
    "validate_adapter_import_result_json",
]
