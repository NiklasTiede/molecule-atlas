from pathlib import Path

import pytest
from molecule_atlas.evidence import audit_manifest, canonical_json_bytes, load_manifest

FIXTURE_ROOT = Path("../data/evidence-fixtures")


@pytest.mark.parametrize("fixture_name", ["succeeded", "partial", "failed"])
def test_evidence_fixtures_are_canonical_and_hash_verified(fixture_name: str) -> None:
    fixture_dir = FIXTURE_ROOT / fixture_name
    manifest_path = fixture_dir / "molecule-atlas-run.json"

    manifest = load_manifest(manifest_path)
    audit = audit_manifest(manifest, root=fixture_dir)

    assert manifest_path.read_bytes() == canonical_json_bytes(manifest)
    assert all(check.status == "verified" for check in audit.artifact_checks)


def test_successful_fixture_has_typed_prediction_and_mixed_validation_evidence() -> None:
    manifest = load_manifest(FIXTURE_ROOT / "succeeded" / "molecule-atlas-run.json")

    assert manifest.run.state == "succeeded"
    assert {prediction.type for prediction in manifest.predictions} == {
        "docking_energy",
        "binder_probability",
    }
    assert {result.status for result in manifest.validation_results} == {"pass", "fail"}


def test_partial_fixture_explicitly_lists_missing_outputs() -> None:
    manifest = load_manifest(FIXTURE_ROOT / "partial" / "molecule-atlas-run.json")

    assert manifest.run.state == "partial"
    assert manifest.run.missing_outputs == ("predicted complex",)
    assert any(warning.code == "missing_predicted_complex" for warning in manifest.warnings)


def test_failed_fixture_retains_failure_and_raw_log() -> None:
    manifest = load_manifest(FIXTURE_ROOT / "failed" / "molecule-atlas-run.json")

    assert manifest.run.state == "failed"
    assert manifest.run.failure is not None
    assert manifest.run.failure.category == "upstream_error"
    assert manifest.predictions == ()
    assert manifest.artifacts[0].role == "log"
