from dataclasses import dataclass
from hashlib import sha256
from threading import Lock

from app.application.capabilities.catalog import IMPORT_EVIDENCE_BUNDLE
from app.application.capabilities.models import CapabilityContext, require_permissions
from app.application.evidence.contracts import (
    ImportEvidenceBundleInput,
    ImportEvidenceBundleOutput,
)
from app.application.evidence.ports import (
    EvidenceBundleConflictError,
    EvidenceRunRepository,
    StoredEvidenceRun,
)
from app.application.evidence.run_summary import build_run_summary


@dataclass(frozen=True, slots=True)
class _ImportRecord:
    archive_sha256: str
    stored_run: StoredEvidenceRun


class ImportEvidenceBundleCapability:
    """Authorize, de-duplicate, and publish one portable evidence bundle."""

    definition = IMPORT_EVIDENCE_BUNDLE

    def __init__(self, repository: EvidenceRunRepository) -> None:
        self._repository = repository
        self._records: dict[str, _ImportRecord] = {}
        self._lock = Lock()

    def execute(
        self,
        request: ImportEvidenceBundleInput,
        *,
        context: CapabilityContext,
    ) -> ImportEvidenceBundleOutput:
        require_permissions(self.definition, context)
        archive_sha256 = sha256(request.archive_bytes).hexdigest()
        with self._lock:
            existing = self._records.get(request.idempotency_key)
            if existing is not None:
                if existing.archive_sha256 != archive_sha256:
                    raise EvidenceBundleConflictError(
                        "Idempotency key was already used for a different bundle"
                    )
                return ImportEvidenceBundleOutput(
                    correlation_id=context.correlation_id,
                    idempotency_replayed=True,
                    run=build_run_summary(existing.stored_run),
                )

            stored_run = self._repository.import_bundle(request.archive_bytes)
            self._records[request.idempotency_key] = _ImportRecord(
                archive_sha256=archive_sha256,
                stored_run=stored_run,
            )

        return ImportEvidenceBundleOutput(
            correlation_id=context.correlation_id,
            idempotency_replayed=False,
            run=build_run_summary(stored_run),
        )
