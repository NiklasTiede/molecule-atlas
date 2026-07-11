import shutil
from pathlib import Path

import pytest
from molecule_atlas.evidence.serialization import load_manifest, write_manifest

from app.application.capabilities.models import ActorContext, CapabilityContext
from app.application.evidence.artifact_inspection import (
    ListAvailableArtifactsCapability,
    ValidateEvidenceArtifactsCapability,
)
from app.application.evidence.contracts import (
    ListAvailableArtifactsInput,
    ValidateEvidenceArtifactsInput,
)
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
        correlation_id="corr-artifact-test",
        causation_id=None,
    )


def _repository() -> LocalEvidenceRunRepository:
    return LocalEvidenceRunRepository((FIXTURE_ROOT,))


def test_list_available_artifacts_preserves_semantics_and_verification() -> None:
    result = ListAvailableArtifactsCapability(_repository()).execute(
        ListAvailableArtifactsInput(run_id="fixture-succeeded"),
        context=_context(),
    )

    assert result.capability_id == "list_available_artifacts"
    assert result.correlation_id == "corr-artifact-test"
    assert result.run_id == "fixture-succeeded"
    assert result.total == 4
    assert result.offset == 0
    assert result.limit == 50
    assert tuple(artifact.artifact_id for artifact in result.artifacts) == (
        "ligand",
        "predicted-pose",
        "raw-predictions",
        "validation-output",
    )
    predicted_pose = result.artifacts[1]
    assert predicted_pose.verification.status == "verified"
    assert predicted_pose.content_digest.startswith("sha256:")
    assert predicted_pose.semantic is not None
    assert predicted_pose.semantic.logical_name == "predicted_poses"
    assert predicted_pose.semantic.artifact_type == "docking-pose-set"
    assert predicted_pose.semantic.semantic_role == "primary_output"
    assert predicted_pose.semantic.derived_from_artifact_ids == ("ligand",)


def test_list_available_artifacts_applies_strict_bounds() -> None:
    result = ListAvailableArtifactsCapability(_repository()).execute(
        ListAvailableArtifactsInput(run_id="fixture-succeeded", offset=1, limit=2),
        context=_context(),
    )

    assert result.total == 4
    assert result.offset == 1
    assert result.limit == 2
    assert tuple(artifact.artifact_id for artifact in result.artifacts) == (
        "predicted-pose",
        "raw-predictions",
    )


def test_validate_evidence_artifacts_returns_checks_counts_and_warnings() -> None:
    result = ValidateEvidenceArtifactsCapability(_repository()).execute(
        ValidateEvidenceArtifactsInput(run_id="fixture-succeeded"),
        context=_context(),
    )

    assert result.capability_id == "validate_evidence_artifacts"
    assert result.correlation_id == "corr-artifact-test"
    assert result.run_id == "fixture-succeeded"
    assert result.counts.verified_count == 4
    assert result.counts.missing_count == 0
    assert result.counts.mismatch_count == 0
    assert result.counts.external_count == 0
    assert result.warnings == ()
    assert all(check.status == "verified" for check in result.artifact_checks)


@pytest.mark.parametrize(
    ("mutation", "expected_status", "warning_code"),
    (
        ("missing", "missing", "artifact_missing"),
        ("mismatch", "mismatch", "artifact_hash_mismatch"),
        ("external", "external", "artifact_external_not_verified"),
    ),
)
def test_validate_evidence_artifacts_keeps_integrity_failures_visible(
    tmp_path: Path,
    mutation: str,
    expected_status: str,
    warning_code: str,
) -> None:
    bundle_root = tmp_path / "bundle"
    shutil.copytree(FIXTURE_ROOT / "succeeded", bundle_root)
    ligand_path = bundle_root / "artifacts" / "ligand.sdf"
    if mutation == "missing":
        ligand_path.unlink()
    elif mutation == "mismatch":
        ligand_path.write_bytes(b"tampered")
    else:
        manifest_path = bundle_root / "molecule-atlas-run.json"
        manifest = load_manifest(manifest_path)
        artifacts = tuple(
            artifact.model_copy(update={"path_or_uri": "https://example.invalid/ligand.sdf"})
            if artifact.id == "ligand"
            else artifact
            for artifact in manifest.artifacts
        )
        write_manifest(manifest_path, manifest.model_copy(update={"artifacts": artifacts}))
        (bundle_root / "molecule-atlas-artifacts.json").unlink()

    result = ValidateEvidenceArtifactsCapability(
        LocalEvidenceRunRepository((bundle_root,))
    ).execute(
        ValidateEvidenceArtifactsInput(run_id="fixture-succeeded"),
        context=_context(),
    )

    ligand_check = next(check for check in result.artifact_checks if check.artifact_id == "ligand")
    assert ligand_check.status == expected_status
    assert warning_code in {warning.code for warning in result.warnings}


def test_artifact_inspection_rejects_unknown_run() -> None:
    capability = ListAvailableArtifactsCapability(_repository())

    with pytest.raises(EvidenceRunNotFoundError, match="unknown-run"):
        capability.execute(
            ListAvailableArtifactsInput(run_id="unknown-run"),
            context=_context(),
        )
