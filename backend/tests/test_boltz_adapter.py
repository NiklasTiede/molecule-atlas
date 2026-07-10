import shutil
from pathlib import Path

import pytest
from molecule_atlas.evidence import (
    AdapterImportRequest,
    AdapterImportResultV020,
    BinderProbabilityPrediction,
    PredictedAffinityPrediction,
    StructureConfidencePrediction,
    audit_manifest,
    render_markdown_report,
    validate_adapter_import_result_json,
)
from molecule_atlas.evidence.adapters.boltz import BoltzAdapter
from molecule_atlas.evidence.adapters.contracts import AdapterLayoutError

FIXTURE_ROOT = Path("../data/evidence-fixtures/boltz-2.2.1/documented-layout")


def test_boltz_adapter_declares_source_verified_compatibility() -> None:
    metadata = BoltzAdapter().metadata

    assert metadata.adapter_id == "boltz"
    assert metadata.adapter_version == "0.1.0"
    assert metadata.upstream_tool == "Boltz"
    assert metadata.source_format == "boltz-prediction-directory"
    assert metadata.source_format_version == "2.2.1"
    assert metadata.verified_upstream_versions == ("2.2.1",)


def test_boltz_adapter_normalizes_documented_primary_fields() -> None:
    result = BoltzAdapter().import_evidence(AdapterImportRequest(source_path=FIXTURE_ROOT))

    assert isinstance(result, AdapterImportResultV020)
    assert result.contract_version == "0.2.0"
    assert result.manifest.run.state == "succeeded"
    assert result.manifest.method.upstream_tool == "Boltz"
    assert result.manifest.method.upstream_version is None
    assert {prediction.type for prediction in result.manifest.predictions} == {
        "structure_confidence",
        "binder_probability",
        "predicted_affinity",
    }

    structure = next(
        prediction
        for prediction in result.manifest.predictions
        if isinstance(prediction, StructureConfidencePrediction)
    )
    binder = next(
        prediction
        for prediction in result.manifest.predictions
        if isinstance(prediction, BinderProbabilityPrediction)
    )
    affinity = next(
        prediction
        for prediction in result.manifest.predictions
        if isinstance(prediction, PredictedAffinityPrediction)
    )
    assert structure.value == 0.8367
    assert structure.raw_source.field == "confidence_score"
    assert structure.scope == "complex"
    assert binder.value == 0.8425
    assert binder.raw_source.field == "affinity_probability_binary"
    assert affinity.value == 0.8367
    assert affinity.unit == "log10(IC50/µM)"
    assert affinity.optimization_direction == "lower_is_better"
    assert "not measured affinity" in affinity.caveats[0]

    semantic_types = {
        artifact.logical_name: artifact.artifact_type
        for artifact in result.artifact_manifest.artifacts
    }
    assert semantic_types == {
        "predicted_complex_model_0": "predicted-complex",
        "confidence_model_0": "raw-prediction-output",
        "affinity": "raw-prediction-output",
    }
    assert validate_adapter_import_result_json(result.model_dump_json()) == result
    assert all(
        check.status == "verified"
        for check in audit_manifest(
            result.manifest,
            root=result.artifact_root,
        ).artifact_checks
    )

    report = render_markdown_report(result.manifest)
    assert "### Structure confidence" in report
    assert "### Binder probability" in report
    assert "### Predicted affinity" in report
    assert "0.8367 log10(IC50/µM)" in report
    assert "not measured affinity" in report


def test_boltz_adapter_marks_missing_confidence_as_partial(tmp_path: Path) -> None:
    fixture = tmp_path / "boltz-output"
    shutil.copytree(FIXTURE_ROOT, fixture)
    (fixture / "predictions/example/confidence_example_model_0.json").unlink()

    result = BoltzAdapter().import_evidence(AdapterImportRequest(source_path=fixture))

    assert result.manifest.run.state == "partial"
    assert result.manifest.run.missing_outputs == ("confidence model 0",)
    assert {prediction.type for prediction in result.manifest.predictions} == {
        "binder_probability",
        "predicted_affinity",
    }


def test_boltz_adapter_inventories_documented_array_outputs_as_opaque_raw_artifacts(
    tmp_path: Path,
) -> None:
    fixture = tmp_path / "boltz-output"
    shutil.copytree(FIXTURE_ROOT, fixture)
    target = fixture / "predictions/example"
    for array_name in ("plddt", "pae", "pde"):
        (target / f"{array_name}_example_model_0.npz").write_bytes(
            f"synthetic opaque {array_name} bytes".encode()
        )

    result = BoltzAdapter().import_evidence(AdapterImportRequest(source_path=fixture))

    arrays = {
        artifact.logical_name: artifact
        for artifact in result.artifact_manifest.artifacts
        if artifact.logical_name in {"plddt_model_0", "pae_model_0", "pde_model_0"}
    }
    assert set(arrays) == {"plddt_model_0", "pae_model_0", "pde_model_0"}
    assert all(artifact.artifact_type == "raw-prediction-output" for artifact in arrays.values())
    assert all(artifact.semantic_role == "raw_output" for artifact in arrays.values())
    assert all(artifact.media_type == "application/x-npz" for artifact in arrays.values())
    assert result.manifest.run.state == "succeeded"
    assert all(
        check.status == "verified"
        for check in audit_manifest(
            result.manifest,
            root=result.artifact_root,
        ).artifact_checks
    )


def test_boltz_adapter_rejects_ambiguous_target_directory(tmp_path: Path) -> None:
    fixture = tmp_path / "boltz-output"
    shutil.copytree(FIXTURE_ROOT, fixture)
    shutil.copytree(
        fixture / "predictions/example",
        fixture / "predictions/second",
    )

    with pytest.raises(AdapterLayoutError, match="multiple prediction targets") as captured:
        BoltzAdapter().import_evidence(AdapterImportRequest(source_path=fixture))

    assert captured.value.code == "boltz_ambiguous_target"


def test_boltz_adapter_rejects_malformed_json(tmp_path: Path) -> None:
    fixture = tmp_path / "boltz-output"
    shutil.copytree(FIXTURE_ROOT, fixture)
    (fixture / "predictions/example/confidence_example_model_0.json").write_text(
        "{not-json}\n",
        encoding="utf-8",
    )

    with pytest.raises(AdapterLayoutError, match="invalid JSON") as captured:
        BoltzAdapter().import_evidence(AdapterImportRequest(source_path=fixture))

    assert captured.value.code == "boltz_invalid_json"


def test_boltz_adapter_rejects_directory_without_supported_outputs(tmp_path: Path) -> None:
    (tmp_path / "predictions/example").mkdir(parents=True)

    with pytest.raises(AdapterLayoutError, match="no supported Boltz outputs") as captured:
        BoltzAdapter().import_evidence(AdapterImportRequest(source_path=tmp_path))

    assert captured.value.code == "boltz_no_supported_outputs"
