from app.application.capabilities.catalog import LIST_EVIDENCE_RUNS
from app.application.capabilities.models import CapabilityContext, require_permissions
from app.application.evidence.contracts import (
    ListEvidenceRunsInput,
    ListEvidenceRunsOutput,
)
from app.application.evidence.ports import EvidenceRunRepository, StoredEvidenceRun
from app.application.evidence.run_summary import build_run_summary


def _recency_key(stored_run: StoredEvidenceRun) -> tuple[bool, str, str]:
    finished_at = stored_run.manifest.run.finished_at
    return (
        finished_at is not None,
        finished_at.isoformat() if finished_at is not None else "",
        stored_run.manifest.run.id,
    )


class ListEvidenceRunsCapability:
    definition = LIST_EVIDENCE_RUNS

    def __init__(self, repository: EvidenceRunRepository) -> None:
        self._repository = repository

    def execute(
        self,
        request: ListEvidenceRunsInput,
        *,
        context: CapabilityContext,
    ) -> ListEvidenceRunsOutput:
        require_permissions(self.definition, context)
        stored_runs = tuple(sorted(self._repository.list_runs(), key=_recency_key, reverse=True))
        selected = stored_runs[request.offset : request.offset + request.limit]
        return ListEvidenceRunsOutput(
            correlation_id=context.correlation_id,
            total=len(stored_runs),
            offset=request.offset,
            limit=request.limit,
            runs=tuple(build_run_summary(run) for run in selected),
        )
