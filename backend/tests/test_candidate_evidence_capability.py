from pathlib import Path

import pytest
from molecule_atlas.evidence.models import InputReference
from molecule_atlas.evidence.serialization import load_manifest, write_manifest

from app.application.capabilities.models import ActorContext, CapabilityContext
from app.application.evidence.candidate_evidence import GetCandidateEvidenceCapability
from app.application.evidence.contracts import GetCandidateEvidenceInput
from app.application.evidence.run_summary import EvidenceRunNotFoundError
from app.infrastructure.evidence.local_repository import LocalEvidenceRunRepository

FIXTURE_ROOT = Path(__file__).parents[2] / "data" / "evidence-fixtures"


def _context() -> CapabilityContext:
    return CapabilityContext(
        actor=ActorContext(
            actor_id="test-suite",
            actor_type="service",
            permissions=("evidence:read",),
        ),
        correlation_id="corr-candidate-evidence",
        causation_id=None,
    )


def _capability() -> GetCandidateEvidenceCapability:
    return GetCandidateEvidenceCapability(LocalEvidenceRunRepository((FIXTURE_ROOT,)))


def test_get_candidate_evidence_preserves_typed_predictions_and_validation_lineage() -> None:
    result = _capability().execute(
        GetCandidateEvidenceInput(
            run_id="fixture-succeeded",
            candidate_id="candidate-1",
            candidate_external_id="synthetic-ligand-1",
        ),
        context=_context(),
    )

    assert result.capability_id == "get_candidate_evidence"
    assert result.correlation_id == "corr-candidate-evidence"
    assert result.binding.status == "bound"
    assert result.binding.reference_ids_checked == ("candidate-1", "synthetic-ligand-1")
    assert result.binding.matched_input_ids == ("ligand-input",)
    assert result.binding.matched_input_artifact_ids == ("ligand",)
    assert result.lineage_available is True
    assert result.related_artifact_ids == (
        "ligand",
        "predicted-pose",
        "raw-predictions",
        "validation-output",
    )
    assert result.prediction_total == 2
    assert tuple(prediction.type for prediction in result.predictions) == (
        "docking_energy",
        "binder_probability",
    )
    assert result.predictions[0].unit == "kcal/mol"
    assert result.predictions[0].raw_source.artifact_id == "raw-predictions"
    assert result.predictions[0].method_id == result.method.method_id
    assert result.validation_total == 2
    assert tuple(check.status for check in result.validation_results) == ("pass", "fail")
    assert result.validation_results[1].raw_output_artifact_id == "validation-output"
    assert result.warnings == ()


def test_get_candidate_evidence_returns_explicit_unbound_state() -> None:
    result = _capability().execute(
        GetCandidateEvidenceInput(
            run_id="fixture-succeeded",
            candidate_id="demo-1",
            candidate_external_id="DEMO-001",
        ),
        context=_context(),
    )

    assert result.binding.status == "unbound"
    assert result.binding.matched_input_ids == ()
    assert result.predictions == ()
    assert result.validation_results == ()
    assert {warning.code for warning in result.warnings} == {"candidate_not_bound"}


def test_get_candidate_evidence_reports_ambiguous_recorded_inputs(tmp_path: Path) -> None:
    manifest_path = FIXTURE_ROOT / "succeeded" / "molecule-atlas-run.json"
    manifest = load_manifest(manifest_path)
    duplicate_input = InputReference(
        id="ligand-input-duplicate",
        kind="ligand",
        artifact_id="ligand",
        representation="conformer",
        upstream_id="synthetic-ligand-1",
    )
    bundle_root = tmp_path / "ambiguous"
    bundle_root.mkdir()
    write_manifest(
        bundle_root / "molecule-atlas-run.json",
        manifest.model_copy(update={"inputs": (*manifest.inputs, duplicate_input)}),
    )

    result = GetCandidateEvidenceCapability(LocalEvidenceRunRepository((bundle_root,))).execute(
        GetCandidateEvidenceInput(
            run_id="fixture-succeeded",
            candidate_id="candidate-1",
            candidate_external_id="synthetic-ligand-1",
        ),
        context=_context(),
    )

    assert result.binding.status == "ambiguous"
    assert result.binding.matched_input_ids == (
        "ligand-input",
        "ligand-input-duplicate",
    )
    assert result.predictions == ()
    assert {warning.code for warning in result.warnings} == {"ambiguous_candidate_binding"}


def test_get_candidate_evidence_does_not_guess_without_semantic_lineage() -> None:
    result = _capability().execute(
        GetCandidateEvidenceInput(
            run_id="fixture-partial",
            candidate_id="candidate-2",
            candidate_external_id="synthetic-ligand-2",
        ),
        context=_context(),
    )

    assert result.binding.status == "bound"
    assert result.lineage_available is False
    assert result.related_artifact_ids == ("ligand",)
    assert result.predictions == ()
    assert result.prediction_total == 0
    assert {warning.code for warning in result.warnings} == {"semantic_lineage_unavailable"}


def test_get_candidate_evidence_applies_independent_result_bounds() -> None:
    result = _capability().execute(
        GetCandidateEvidenceInput(
            run_id="fixture-succeeded",
            candidate_id="synthetic-ligand-1",
            prediction_limit=1,
            validation_limit=1,
        ),
        context=_context(),
    )

    assert result.binding.status == "bound"
    assert result.prediction_total == 2
    assert len(result.predictions) == 1
    assert result.validation_total == 2
    assert len(result.validation_results) == 1
    assert {warning.code for warning in result.warnings} == {
        "prediction_limit_reached",
        "validation_limit_reached",
    }


def test_get_candidate_evidence_rejects_unknown_run() -> None:
    with pytest.raises(EvidenceRunNotFoundError, match="unknown-run"):
        _capability().execute(
            GetCandidateEvidenceInput(
                run_id="unknown-run",
                candidate_id="candidate-1",
            ),
            context=_context(),
        )
