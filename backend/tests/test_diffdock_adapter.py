import shutil
from pathlib import Path

import pytest
from molecule_atlas.evidence import (
    AdapterImportRequest,
    AdapterImportResultV020,
    EvidenceInputError,
    PoseConfidencePrediction,
    audit_manifest,
    render_markdown_report,
    validate_adapter_import_result_json,
)
from molecule_atlas.evidence.adapters import get_adapter
from molecule_atlas.evidence.adapters.contracts import AdapterLayoutError
from molecule_atlas.evidence.adapters.diffdock import DiffDockAdapter

FIXTURE_ROOT = Path("../data/evidence-fixtures/diffdock-1.1.3/documented-layout")


def test_diffdock_adapter_declares_source_verified_compatibility() -> None:
    metadata = DiffDockAdapter().metadata

    assert metadata.adapter_id == "diffdock"
    assert metadata.adapter_version == "0.1.0"
    assert metadata.upstream_tool == "DiffDock"
    assert metadata.source_format == "diffdock-complex-directory"
    assert metadata.source_format_version == "1.1.3"
    assert metadata.verified_upstream_versions == ("1.1.3",)


def test_diffdock_adapter_remains_unregistered_without_genuine_fixture() -> None:
    with pytest.raises(EvidenceInputError, match="Unsupported adapter 'diffdock'"):
        get_adapter("diffdock")


def test_diffdock_adapter_normalizes_ranked_pose_confidence() -> None:
    result = DiffDockAdapter().import_evidence(AdapterImportRequest(source_path=FIXTURE_ROOT))

    assert isinstance(result, AdapterImportResultV020)
    assert result.manifest.run.state == "succeeded"
    assert result.manifest.method.upstream_tool == "DiffDock"
    assert result.manifest.method.upstream_version is None
    predictions = tuple(
        prediction
        for prediction in result.manifest.predictions
        if isinstance(prediction, PoseConfidencePrediction)
    )
    assert [prediction.scope_id for prediction in predictions] == ["pose-rank-1", "pose-rank-2"]
    assert [prediction.value for prediction in predictions] == [0.75, -0.5]
    assert all(prediction.raw_source.field == "filename.confidence" for prediction in predictions)
    assert all(
        prediction.optimization_direction == "higher_is_better" for prediction in predictions
    )
    assert all("not binding affinity" in prediction.caveats[0] for prediction in predictions)

    semantic_types = {
        artifact.logical_name: artifact.artifact_type
        for artifact in result.artifact_manifest.artifacts
    }
    assert semantic_types == {
        "pose_rank_1": "ligand-structure",
        "pose_rank_2": "ligand-structure",
        "top_pose_alias": "ligand-structure",
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
    assert report.count("### Pose confidence") == 2
    assert "0.75" in report
    assert "-0.5" in report
    assert "not binding affinity" in report
    assert "### Predicted affinity" not in report


def test_diffdock_adapter_marks_missing_rank_as_partial(tmp_path: Path) -> None:
    fixture = tmp_path / "diffdock-output"
    shutil.copytree(FIXTURE_ROOT, fixture)
    (fixture / "example/rank1_confidence0.75.sdf").unlink()

    result = DiffDockAdapter().import_evidence(AdapterImportRequest(source_path=fixture))

    assert result.manifest.run.state == "partial"
    assert result.manifest.run.missing_outputs == ("pose rank 1",)
    assert [prediction.scope_id for prediction in result.manifest.predictions] == ["pose-rank-2"]


def test_diffdock_adapter_rejects_duplicate_rank(tmp_path: Path) -> None:
    fixture = tmp_path / "diffdock-output"
    shutil.copytree(FIXTURE_ROOT, fixture)
    shutil.copyfile(
        fixture / "example/rank1_confidence0.75.sdf",
        fixture / "example/rank1_confidence0.80.sdf",
    )

    with pytest.raises(AdapterLayoutError, match="multiple files for pose rank 1") as captured:
        DiffDockAdapter().import_evidence(AdapterImportRequest(source_path=fixture))

    assert captured.value.code == "diffdock_duplicate_rank"


def test_diffdock_adapter_rejects_ambiguous_complex_directory(tmp_path: Path) -> None:
    fixture = tmp_path / "diffdock-output"
    shutil.copytree(FIXTURE_ROOT, fixture)
    shutil.copytree(fixture / "example", fixture / "second")

    with pytest.raises(AdapterLayoutError, match="multiple complex directories") as captured:
        DiffDockAdapter().import_evidence(AdapterImportRequest(source_path=fixture))

    assert captured.value.code == "diffdock_ambiguous_complex"


def test_diffdock_adapter_rejects_directory_without_ranked_poses(tmp_path: Path) -> None:
    (tmp_path / "example").mkdir()

    with pytest.raises(AdapterLayoutError, match="no supported ranked pose outputs") as captured:
        DiffDockAdapter().import_evidence(AdapterImportRequest(source_path=tmp_path))

    assert captured.value.code == "diffdock_no_supported_outputs"
