import json
from pathlib import Path
from typing import cast

import pytest
from molecule_atlas.evidence import RunManifest, load_manifest
from molecule_atlas.evidence.cli import main

FIXTURE_ROOT = Path("../data/evidence-fixtures")


def test_inspect_summarizes_and_audits_fixture(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(["inspect", str(FIXTURE_ROOT / "succeeded")])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Run: fixture-succeeded" in captured.out
    assert "State: succeeded" in captured.out
    assert "Artifacts: 4 (4 verified)" in captured.out
    assert "Predictions: binder_probability=1, docking_energy=1" in captured.out


def test_audit_writes_canonical_manifest_with_derived_warnings(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output = tmp_path / "audited.json"

    exit_code = main(
        [
            "audit",
            str(FIXTURE_ROOT / "failed"),
            "--adapter",
            "manifest",
            "--output",
            str(output),
        ]
    )

    assert exit_code == 0
    manifest = load_manifest(output)
    assert manifest.run.state == "failed"
    assert any(warning.code == "missing_environment" for warning in manifest.warnings)
    captured = capsys.readouterr()
    assert str(output) in captured.out


def test_report_prints_markdown_to_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    manifest_path = FIXTURE_ROOT / "partial" / "molecule-atlas-run.json"

    exit_code = main(["report", str(manifest_path), "--format", "markdown"])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "# Molecule Atlas Evidence Report" in captured.out
    assert "**partial**" in captured.out
    assert "missing_predicted_complex" in captured.out


def test_schema_command_exports_run_manifest_schema(tmp_path: Path) -> None:
    output = tmp_path / "run-manifest.schema.json"

    exit_code = main(["schema", "--output", str(output)])

    assert exit_code == 0
    parsed: object = json.loads(output.read_text(encoding="utf-8"))
    assert isinstance(parsed, dict)
    schema = cast(dict[str, object], parsed)
    assert schema["title"] == "RunManifest"


def test_schema_command_exports_artifact_manifest_schema(tmp_path: Path) -> None:
    output = tmp_path / "artifact-manifest.schema.json"

    exit_code = main(["schema", "--contract", "artifact-manifest", "--output", str(output)])

    assert exit_code == 0
    parsed: object = json.loads(output.read_text(encoding="utf-8"))
    assert isinstance(parsed, dict)
    schema = cast(dict[str, object], parsed)
    assert schema["title"] == "ArtifactManifest"


def test_cli_rejects_unknown_adapter(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(
        [
            "audit",
            str(FIXTURE_ROOT / "succeeded"),
            "--adapter",
            "boltz",
            "--output",
            "unused.json",
        ]
    )

    assert exit_code == 2
    captured = capsys.readouterr()
    assert "Unsupported adapter 'boltz'" in captured.err
    assert "Supported adapters: manifest" in captured.err


def test_cli_rejects_missing_manifest(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    exit_code = main(["inspect", str(tmp_path / "does-not-exist")])

    assert exit_code == 2
    captured = capsys.readouterr()
    assert "does not exist" in captured.err


def test_core_models_are_importable_for_fastapi_consumers() -> None:
    assert RunManifest.__module__ == "molecule_atlas.evidence.models"
