import csv
from pathlib import Path

import pytest
from molecule_atlas.evidence import verify_artifact
from molecule_atlas.evidence.validation import (
    PoseBustersCompatibilityError,
    PoseBustersExecutionRequest,
    PoseBustersNormalizationRequest,
    normalize_posebusters_report,
    posebusters_metadata,
    run_posebusters,
)
from molecule_atlas.evidence.validation import posebusters as posebusters_module

FIXTURE_ROOT = Path("../data/evidence-fixtures/posebusters-0.6.5/mol-full-report")


def test_posebusters_metadata_pins_verified_optional_compatibility() -> None:
    metadata = posebusters_metadata()

    assert metadata.validator_id == "posebusters"
    assert metadata.integration_version == "0.1.0"
    assert metadata.upstream_tool == "PoseBusters"
    assert metadata.verified_upstream_versions == ("0.6.5",)
    assert metadata.configurations == ("mol", "dock", "redock")
    assert metadata.optional_dependency == "posebusters==0.6.5"


def test_posebusters_normalizes_genuine_full_report_and_preserves_raw_bytes() -> None:
    result = normalize_posebusters_report(
        PoseBustersNormalizationRequest(
            report_path=FIXTURE_ROOT / "raw-report.csv",
            artifact_root=FIXTURE_ROOT,
            input_artifact_id="predicted-pose",
            validator_version="0.6.5",
            config="mol",
        )
    )

    assert result.contract_version == "0.1.0"
    assert result.validator_id == "posebusters"
    assert result.raw_report_artifact.path_or_uri == "raw-report.csv"
    assert result.raw_report_artifact.role == "validation_output"
    assert result.semantic_artifact.artifact_type == "validation-report"
    assert result.semantic_artifact.logical_name == "posebusters_full_report"
    assert (
        verify_artifact(result.raw_report_artifact, root=result.artifact_root).status == "verified"
    )
    assert len(result.validation_results) == 12
    assert {validation.status for validation in result.validation_results} == {"pass"}
    assert all(
        validation.raw_output_artifact_id == result.raw_report_artifact.id
        for validation in result.validation_results
    )
    assert all(
        validation.input_artifact_id == "predicted-pose" for validation in result.validation_results
    )
    energy = next(
        validation
        for validation in result.validation_results
        if validation.check_id == "internal_energy"
    )
    assert energy.measured_value == pytest.approx(8.302534213025426)
    assert energy.unit == "ratio"
    assert energy.threshold_or_configuration == {
        "config": "mol",
        "maximum_energy_ratio": 100.0,
    }
    assert result.warnings == ()


def test_posebusters_normalizes_fail_unavailable_error_and_unknown_column(
    tmp_path: Path,
) -> None:
    with (FIXTURE_ROOT / "raw-report.csv").open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        row = next(reader)
        fieldnames = [*(reader.fieldnames or ()), "future_posebusters_metric"]
    row["bond_lengths"] = "False"
    row["bond_angles"] = ""
    row["no_radicals"] = "not-a-boolean"
    row["future_posebusters_metric"] = "42"
    report_path = tmp_path / "raw-report.csv"
    with report_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerow(row)

    result = normalize_posebusters_report(
        PoseBustersNormalizationRequest(
            report_path=report_path,
            artifact_root=tmp_path,
            input_artifact_id="predicted-pose",
            validator_version="0.6.5",
            config="mol",
        )
    )

    statuses = {validation.check_id: validation.status for validation in result.validation_results}
    assert statuses["bond_lengths"] == "fail"
    assert statuses["bond_angles"] == "unavailable"
    assert statuses["no_radicals"] == "error"
    assert result.warnings[0].code == "posebusters_unknown_columns"
    assert "future_posebusters_metric" in result.warnings[0].message
    assert "future_posebusters_metric" in report_path.read_text(encoding="utf-8")


def test_posebusters_rejects_unverified_upstream_version() -> None:
    with pytest.raises(PoseBustersCompatibilityError, match=r"supports exactly 0\.6\.5"):
        normalize_posebusters_report(
            PoseBustersNormalizationRequest(
                report_path=FIXTURE_ROOT / "raw-report.csv",
                artifact_root=FIXTURE_ROOT,
                input_artifact_id="predicted-pose",
                validator_version="0.6.4",
                config="mol",
            )
        )


def test_posebusters_dock_mapping_keeps_distance_and_overlap_semantics(
    tmp_path: Path,
) -> None:
    report_path = tmp_path / "dock-report.csv"
    report_path.write_text(
        "file,molecule,position,protein-ligand_maximum_distance,"
        "minimum_distance_to_protein,smallest_distance_protein,"
        "volume_overlap_with_protein,volume_overlap_protein\n"
        "pose.sdf,pose,0,True,False,1.25,False,0.12\n",
        encoding="utf-8",
    )

    result = normalize_posebusters_report(
        PoseBustersNormalizationRequest(
            report_path=report_path,
            artifact_root=tmp_path,
            input_artifact_id="predicted-pose",
            validator_version="0.6.5",
            config="dock",
        )
    )
    checks = {validation.check_id: validation for validation in result.validation_results}

    assert checks["protein-ligand_maximum_distance"].status == "pass"
    assert checks["protein-ligand_maximum_distance"].measured_value == 1.25
    assert checks["protein-ligand_maximum_distance"].unit == "angstrom"
    assert checks["minimum_distance_to_protein"].status == "fail"
    assert checks["volume_overlap_with_protein"].status == "fail"
    assert checks["volume_overlap_with_protein"].measured_value == 0.12
    assert checks["volume_overlap_with_protein"].unit == "fraction"


def test_posebusters_optional_runner_requests_full_report_and_normalizes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw_csv = (FIXTURE_ROOT / "raw-report.csv").read_text(encoding="utf-8")
    calls: dict[str, object] = {}

    class FakeReport:
        def to_csv(self, *, index: bool, lineterminator: str) -> str:
            calls["serialization"] = (index, lineterminator)
            return raw_csv

    class FakeValidator:
        def bust(
            self,
            mol_pred: Path,
            mol_true: Path | None = None,
            mol_cond: Path | None = None,
            *,
            full_report: bool,
        ) -> FakeReport:
            calls["bust"] = (mol_pred, mol_true, mol_cond, full_report)
            return FakeReport()

    def fake_factory(*, config: str, max_workers: int) -> FakeValidator:
        calls["factory"] = (config, max_workers)
        return FakeValidator()

    monkeypatch.setattr(posebusters_module, "_installed_version", lambda: "0.6.5")
    monkeypatch.setattr(posebusters_module, "_load_factory", lambda: fake_factory)
    report_path = tmp_path / "raw-report.csv"

    result = run_posebusters(
        PoseBustersExecutionRequest(
            mol_pred=FIXTURE_ROOT / "predicted-pose.sdf",
            mol_true=None,
            mol_cond=None,
            config="mol",
            artifact_root=tmp_path,
            report_path=report_path,
            input_artifact_id="predicted-pose",
        )
    )

    assert calls["factory"] == ("mol", 0)
    assert calls["bust"] == (
        FIXTURE_ROOT / "predicted-pose.sdf",
        None,
        None,
        True,
    )
    assert calls["serialization"] == (True, "\n")
    assert report_path.read_text(encoding="utf-8") == raw_csv
    assert len(result.validation_results) == 12
