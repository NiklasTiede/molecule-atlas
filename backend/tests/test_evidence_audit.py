import json
from pathlib import Path

from molecule_atlas.evidence import RunManifest, audit_manifest, inventory_artifact


def _minimal_manifest(tmp_path: Path) -> RunManifest:
    raw = tmp_path / "raw.json"
    raw.write_text('{"prediction":0.8}\n', encoding="utf-8")
    artifact = inventory_artifact(
        raw,
        root=tmp_path,
        artifact_id="raw",
        role="raw_score_output",
        media_type="application/json",
        created_by_stage="prediction",
        metadata={},
    )
    payload: dict[str, object] = {
        "schema_version": "0.1.0",
        "run": {
            "id": "imported-run",
            "state": "unknown",
            "started_at": None,
            "finished_at": None,
            "expected_outputs": [],
            "missing_outputs": [],
            "failure": None,
        },
        "method": {
            "id": "unknown-method",
            "adapter_id": "manifest",
            "adapter_version": "0.1.0",
            "upstream_tool": None,
            "upstream_version": None,
            "source_commit": None,
            "checkpoint_id": None,
            "checkpoint_sha256": None,
            "container_image": None,
            "container_digest": None,
            "command": [],
            "random_seeds": [],
            "metadata": {},
        },
        "inputs": [],
        "parameters": {},
        "environment": {
            "operating_system": None,
            "architecture": None,
            "python_version": None,
            "accelerator": None,
            "hardware": None,
            "dependencies": {},
        },
        "artifacts": [artifact.model_dump(mode="json")],
        "predictions": [],
        "validation_results": [],
        "licenses": [],
        "warnings": [],
    }
    return RunManifest.model_validate_json(json.dumps(payload))


def test_audit_derives_warnings_without_inventing_provenance(tmp_path: Path) -> None:
    result = audit_manifest(_minimal_manifest(tmp_path), root=tmp_path)

    warning_codes = {warning.code for warning in result.manifest.warnings}
    assert {
        "missing_upstream_tool",
        "missing_upstream_version",
        "missing_command",
        "missing_random_seed",
        "missing_environment",
    }.issubset(warning_codes)
    assert result.manifest.method.upstream_tool is None
    assert result.manifest.method.upstream_version is None
    assert result.artifact_checks[0].status == "verified"


def test_audit_warns_when_artifact_bytes_no_longer_match(tmp_path: Path) -> None:
    manifest = _minimal_manifest(tmp_path)
    (tmp_path / "raw.json").write_text("changed\n", encoding="utf-8")

    result = audit_manifest(manifest, root=tmp_path)

    assert result.artifact_checks[0].status == "mismatch"
    assert any(warning.code == "artifact_hash_mismatch" for warning in result.manifest.warnings)


def test_audit_warning_derivation_is_idempotent(tmp_path: Path) -> None:
    first = audit_manifest(_minimal_manifest(tmp_path), root=tmp_path)
    second = audit_manifest(first.manifest, root=tmp_path)

    assert second.manifest.warnings == first.manifest.warnings
