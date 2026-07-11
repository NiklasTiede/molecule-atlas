from pathlib import Path

import pytest

from app.application.capabilities.models import ActorContext, CapabilityContext
from app.application.evidence.contracts import GetRunSummaryInput
from app.application.evidence.run_summary import (
    EvidenceRunNotFoundError,
    GetRunSummaryCapability,
)
from app.infrastructure.evidence.local_repository import LocalEvidenceRunRepository

FIXTURE_ROOT = Path(__file__).parents[2] / "data" / "evidence-fixtures"


def _context() -> CapabilityContext:
    return CapabilityContext(
        actor=ActorContext(
            actor_id="test-suite",
            actor_type="service",
            permissions=("evidence:read",),
        ),
        correlation_id="corr-summary-test",
        causation_id=None,
    )


def _capability() -> GetRunSummaryCapability:
    return GetRunSummaryCapability(LocalEvidenceRunRepository((FIXTURE_ROOT,)))


def test_get_run_summary_projects_typed_scientific_counts_and_provenance() -> None:
    result = _capability().execute(
        GetRunSummaryInput(run_id="fixture-succeeded"),
        context=_context(),
    )

    assert result.capability_id == "get_run_summary"
    assert result.capability_version == "0.1.0"
    assert result.correlation_id == "corr-summary-test"
    assert result.run.run_id == "fixture-succeeded"
    assert result.run.state == "succeeded"
    assert result.run.method.adapter_id == "manifest"
    assert result.run.method.upstream_tool == "Synthetic Evidence Fixture"
    assert result.run.artifact_count == 4
    assert result.run.prediction_count == 2
    assert result.run.validation_counts.pass_count == 1
    assert result.run.validation_counts.fail_count == 1
    assert result.run.failure is None
    assert result.run.missing_outputs == ()


@pytest.mark.parametrize(
    ("run_id", "state", "missing_output_count", "has_failure"),
    (
        ("fixture-partial", "partial", 1, False),
        ("fixture-failed", "failed", 0, True),
    ),
)
def test_get_run_summary_preserves_incomplete_run_state(
    run_id: str,
    state: str,
    missing_output_count: int,
    has_failure: bool,
) -> None:
    result = _capability().execute(GetRunSummaryInput(run_id=run_id), context=_context())

    assert result.run.state == state
    assert len(result.run.missing_outputs) == missing_output_count
    assert (result.run.failure is not None) is has_failure


def test_get_run_summary_rejects_unknown_run() -> None:
    with pytest.raises(EvidenceRunNotFoundError, match="unknown-run"):
        _capability().execute(GetRunSummaryInput(run_id="unknown-run"), context=_context())
