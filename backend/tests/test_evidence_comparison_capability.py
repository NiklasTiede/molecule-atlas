from pathlib import Path

import pytest
from pydantic import ValidationError

from app.application.capabilities.models import ActorContext, CapabilityContext
from app.application.evidence.comparison import CompareCandidatesCapability
from app.application.evidence.contracts import (
    CompareCandidatesInput,
    ComparisonSubjectInput,
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
        correlation_id="corr-comparison",
        causation_id=None,
    )


def _request() -> CompareCandidatesInput:
    return CompareCandidatesInput(
        subjects=(
            ComparisonSubjectInput(
                subject_id="method-a",
                label="Synthetic method A",
                run_id="fixture-succeeded",
                candidate_id="synthetic-ligand-1",
                candidate_external_id=None,
            ),
            ComparisonSubjectInput(
                subject_id="method-b",
                label="Synthetic method B",
                run_id="fixture-alternative",
                candidate_id="synthetic-ligand-1",
                candidate_external_id=None,
            ),
        )
    )


def test_compare_candidates_groups_only_like_for_like_typed_predictions() -> None:
    capability = CompareCandidatesCapability(LocalEvidenceRunRepository((FIXTURE_ROOT,)))

    result = capability.execute(_request(), context=_context())

    assert result.capability_id == "compare_candidates"
    assert result.correlation_id == "corr-comparison"
    assert tuple(subject.binding.status for subject in result.subjects) == ("bound", "bound")
    assert tuple(subject.method.method_id for subject in result.subjects) == (
        "synthetic-method",
        "synthetic-method-alternative",
    )
    assert result.excluded_prediction_count == 0
    assert tuple(group.prediction_type for group in result.prediction_groups) == (
        "docking_energy",
        "binder_probability",
    )

    docking_group = result.prediction_groups[0]
    assert docking_group.unit == "kcal/mol"
    assert docking_group.optimization_direction == "lower_is_better"
    assert tuple(entry.subject_id for entry in docking_group.entries) == (
        "method-a",
        "method-b",
    )
    assert tuple(entry.prediction.value for entry in docking_group.entries) == (-7.4, -6.8)
    assert all(entry.prediction.type == "docking_energy" for entry in docking_group.entries)
    assert result.warnings == ()


def test_compare_candidates_surfaces_unbound_subject_without_cross_type_ranking() -> None:
    request = CompareCandidatesInput(
        subjects=(
            _request().subjects[0],
            ComparisonSubjectInput(
                subject_id="unbound",
                label="Unbound demo candidate",
                run_id="fixture-partial",
                candidate_id="DEMO-001",
                candidate_external_id=None,
            ),
        )
    )
    capability = CompareCandidatesCapability(LocalEvidenceRunRepository((FIXTURE_ROOT,)))

    result = capability.execute(request, context=_context())

    assert result.subjects[1].binding.status == "unbound"
    assert result.prediction_groups == ()
    assert {warning.code for warning in result.warnings} == {
        "comparison_subject_unbound",
        "no_shared_prediction_groups",
    }


def test_compare_candidates_requires_unique_two_to_ten_subjects() -> None:
    subject = _request().subjects[0]

    with pytest.raises(ValidationError):
        CompareCandidatesInput(subjects=(subject,))
    with pytest.raises(ValidationError, match="subject IDs must be unique"):
        CompareCandidatesInput(subjects=(subject, subject))
