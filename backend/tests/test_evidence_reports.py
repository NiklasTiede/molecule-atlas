import json

from molecule_atlas.evidence import RunManifest, render_markdown_report


def _report_manifest(*, state: str = "partial") -> RunManifest:
    failure = None
    missing_outputs = ["predicted complex"]
    if state == "failed":
        failure = {
            "category": "upstream_error",
            "message": "Synthetic prediction failure",
            "stage": "prediction",
            "exit_code": 2,
            "details": {"stderr_artifact": "run-log"},
        }
        missing_outputs = []
    payload: dict[str, object] = {
        "schema_version": "0.1.0",
        "run": {
            "id": "report-run",
            "state": state,
            "started_at": "2026-01-01T00:00:00Z",
            "finished_at": "2026-01-01T00:00:01Z",
            "expected_outputs": ["raw prediction", "predicted complex"],
            "missing_outputs": missing_outputs,
            "failure": failure,
        },
        "method": {
            "id": "fixture-method",
            "adapter_id": "manifest",
            "adapter_version": "0.1.0",
            "upstream_tool": "Synthetic Fixture",
            "upstream_version": "1.0.0",
            "source_commit": None,
            "checkpoint_id": None,
            "checkpoint_sha256": None,
            "container_image": None,
            "container_digest": None,
            "command": ["fixture", "predict"],
            "random_seeds": [61453],
            "metadata": {},
        },
        "inputs": [],
        "parameters": {"samples": 1},
        "environment": {
            "operating_system": "fixture-os",
            "architecture": "fixture-arch",
            "python_version": None,
            "accelerator": "cpu",
            "hardware": None,
            "dependencies": {},
        },
        "artifacts": [
            {
                "id": "raw-output",
                "role": "raw_score_output",
                "path_or_uri": "artifacts/raw.json",
                "media_type": "application/json",
                "sha256": "a" * 64,
                "size_bytes": 17,
                "created_by_stage": "prediction",
                "original_name": "raw.json",
                "metadata": {},
            },
            {
                "id": "run-log",
                "role": "log",
                "path_or_uri": "artifacts/stderr.log",
                "media_type": "text/plain",
                "sha256": "b" * 64,
                "size_bytes": 28,
                "created_by_stage": "prediction",
                "original_name": "stderr.log",
                "metadata": {},
            },
        ],
        "predictions": [
            {
                "id": "binder-probability",
                "type": "binder_probability",
                "value": 0.8,
                "unit": "probability",
                "scope": "complex",
                "scope_id": "complex-1",
                "method_id": "fixture-method",
                "raw_source": {
                    "artifact_id": "raw-output",
                    "field": "binder_probability",
                    "upstream_record_id": "complex-1",
                },
                "optimization_direction": "higher_is_better",
                "uncertainty": None,
                "interpretation": "Predicted binder probability; not measured biological activity.",
                "caveats": ["Does not establish selectivity."],
            }
        ],
        "validation_results": [
            {
                "id": "distance-check",
                "validator": "Synthetic Validator",
                "validator_version": "1.0.0",
                "check_id": "minimum_distance",
                "status": "fail",
                "measured_value": 0.4,
                "unit": "angstrom",
                "threshold_or_configuration": {"minimum": 1.0},
                "explanation": "Atoms are closer than the configured threshold.",
                "input_artifact_id": "raw-output",
                "raw_output_artifact_id": "raw-output",
            }
        ],
        "licenses": [
            {
                "component": "dataset",
                "identifier": "CC0-1.0",
                "name": "CC0 1.0",
                "source_uri": None,
                "redistribution_restrictions": None,
                "acknowledgement_required": False,
                "notes": "Synthetic fixture only.",
            }
        ],
        "warnings": [
            {
                "code": "missing_predicted_complex",
                "message": "The expected predicted complex is absent.",
                "path": "run.missing_outputs",
            }
        ],
    }
    return RunManifest.model_validate_json(json.dumps(payload))


def test_markdown_report_exposes_partial_state_and_typed_evidence() -> None:
    report = render_markdown_report(_report_manifest())

    assert "# Molecule Atlas Evidence Report" in report
    assert "**partial**" in report
    assert "predicted complex" in report
    assert "Binder probability" in report
    assert "0.8 probability" in report
    assert "higher is better" in report
    assert "raw-output / `binder_probability`" in report
    assert "Predicted binder probability; not measured biological activity." in report
    assert "**fail**" in report
    assert "Atoms are closer than the configured threshold." in report
    assert "CC0-1.0" in report
    assert "does not establish biological activity" in report
    assert "universal ranking" in report


def test_markdown_report_exposes_structured_failure() -> None:
    report = render_markdown_report(_report_manifest(state="failed"))

    assert "**failed**" in report
    assert "Synthetic prediction failure" in report
    assert "upstream_error" in report
    assert "Exit code: `2`" in report
