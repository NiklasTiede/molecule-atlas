from pathlib import Path

from app.application.capabilities.models import ActorContext, CapabilityContext
from app.application.evidence.contracts import ListEvidenceRunsInput
from app.application.evidence.run_listing import ListEvidenceRunsCapability
from app.infrastructure.evidence.local_repository import LocalEvidenceRunRepository

FIXTURE_ROOT = Path(__file__).parents[2] / "data" / "evidence-fixtures"


def _context() -> CapabilityContext:
    return CapabilityContext(
        actor=ActorContext(
            actor_id="test-suite",
            actor_type="service",
            permissions=("evidence:read",),
        ),
        correlation_id="corr-run-list",
        causation_id=None,
    )


def test_list_evidence_runs_is_bounded_and_includes_ligand_references() -> None:
    capability = ListEvidenceRunsCapability(LocalEvidenceRunRepository((FIXTURE_ROOT,)))

    result = capability.execute(ListEvidenceRunsInput(offset=0, limit=2), context=_context())

    assert result.capability_id == "list_evidence_runs"
    assert result.correlation_id == "corr-run-list"
    assert result.total == 4
    assert result.offset == 0
    assert result.limit == 2
    assert len(result.runs) == 2
    assert result.runs[0].run_id == "fixture-alternative"
    assert result.runs[0].ligand_inputs[0].upstream_id == "synthetic-ligand-1"


def test_list_evidence_runs_paginates_without_exposing_repository_paths() -> None:
    capability = ListEvidenceRunsCapability(LocalEvidenceRunRepository((FIXTURE_ROOT,)))

    result = capability.execute(ListEvidenceRunsInput(offset=3, limit=2), context=_context())

    assert result.total == 4
    assert len(result.runs) == 1
    assert "root" not in result.model_dump(mode="json")["runs"][0]
