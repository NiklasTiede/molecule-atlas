import json
from pathlib import Path

from molecule_atlas.evidence import (
    RunManifest,
    artifact_manifest_schema_json,
    canonical_json_bytes,
    manifest_schema_json,
)


def test_canonical_json_is_stable_and_sorted() -> None:
    fixture = Path("../data/evidence-fixtures/succeeded/molecule-atlas-run.json")
    payload: dict[str, object] = {
        "schema_version": "0.1.0",
        "run": {
            "id": "run",
            "state": "unknown",
            "started_at": None,
            "finished_at": None,
            "expected_outputs": [],
            "missing_outputs": [],
            "failure": None,
        },
        "method": {
            "id": "method",
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
        "parameters": {"z": 1, "a": True},
        "environment": {
            "operating_system": None,
            "architecture": None,
            "python_version": None,
            "accelerator": None,
            "hardware": None,
            "dependencies": {},
        },
        "artifacts": [],
        "predictions": [],
        "validation_results": [],
        "licenses": [],
        "warnings": [],
    }
    manifest = RunManifest.model_validate_json(json.dumps(payload))

    first = canonical_json_bytes(manifest)
    second = canonical_json_bytes(manifest)

    assert first == second
    assert first.endswith(b"\n")
    assert b'"parameters":{"a":true,"z":1}' in first
    assert json.loads(first) == manifest.model_dump(mode="json")
    assert fixture.name == "molecule-atlas-run.json"


def test_manifest_schema_export_is_deterministic() -> None:
    first = manifest_schema_json()
    second = manifest_schema_json()

    assert first == second
    assert first.endswith("\n")
    parsed = json.loads(first)
    assert parsed["title"] == "RunManifest"
    assert parsed["properties"]["schema_version"]["const"] == "0.1.0"


def test_artifact_manifest_schema_export_is_deterministic() -> None:
    first = artifact_manifest_schema_json()
    second = artifact_manifest_schema_json()

    assert first == second
    assert first.endswith("\n")
    parsed = json.loads(first)
    assert parsed["title"] == "ArtifactManifest"
    assert parsed["properties"]["schema_version"]["const"] == "0.1.0"
