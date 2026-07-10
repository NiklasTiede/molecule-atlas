from datetime import UTC, datetime
from typing import cast

import pytest
from molecule_atlas.evidence import (
    Artifact,
    BinderProbabilityPrediction,
    DockingEnergyPrediction,
    EnvironmentMetadata,
    InputReference,
    ManifestWarning,
    MethodMetadata,
    PoseConfidencePrediction,
    PredictedAffinityPrediction,
    PredictionRawSource,
    RunFailure,
    RunManifest,
    RunMetadata,
    RunState,
    StructureConfidencePrediction,
    ValidationResult,
)
from pydantic import ValidationError


def _artifact(artifact_id: str = "raw-output") -> Artifact:
    return Artifact(
        id=artifact_id,
        role="raw_score_output",
        path_or_uri="artifacts/raw.json",
        media_type="application/json",
        sha256="a" * 64,
        size_bytes=17,
        created_by_stage="prediction",
        original_name="raw.json",
        metadata={},
    )


def _method() -> MethodMetadata:
    return MethodMetadata(
        id="fixture-method",
        adapter_id="manifest",
        adapter_version="0.1.0",
        upstream_tool="Synthetic Fixture",
        upstream_version="1.0.0",
        source_commit=None,
        checkpoint_id=None,
        checkpoint_sha256=None,
        container_image=None,
        container_digest=None,
        command=("fixture", "predict"),
        random_seeds=(61453,),
        metadata={},
    )


def _run(
    state: RunState = "succeeded",
    *,
    missing_outputs: tuple[str, ...] = (),
    failure: RunFailure | None = None,
) -> RunMetadata:
    return RunMetadata(
        id="fixture-run",
        state=state,
        started_at=datetime(2026, 1, 1, tzinfo=UTC),
        finished_at=datetime(2026, 1, 1, 0, 0, 1, tzinfo=UTC),
        expected_outputs=("raw prediction",),
        missing_outputs=missing_outputs,
        failure=failure,
    )


def _manifest() -> RunManifest:
    artifact = _artifact()
    return RunManifest(
        schema_version="0.1.0",
        run=_run(),
        method=_method(),
        inputs=(
            InputReference(
                id="ligand-input",
                kind="ligand",
                artifact_id=artifact.id,
                representation="conformer",
                upstream_id="fixture-ligand",
            ),
        ),
        parameters={"samples": 1},
        environment=EnvironmentMetadata(
            operating_system="fixture-os",
            architecture="fixture-arch",
            python_version=None,
            accelerator="cpu",
            hardware=None,
            dependencies={},
        ),
        artifacts=(artifact,),
        predictions=(
            DockingEnergyPrediction(
                id="vina-energy",
                type="docking_energy",
                value=-7.4,
                unit="kcal/mol",
                scope="pose",
                scope_id="pose-1",
                method_id="fixture-method",
                raw_source=PredictionRawSource(
                    artifact_id="raw-output",
                    field="affinity",
                    upstream_record_id="pose-1",
                ),
                optimization_direction="lower_is_better",
                uncertainty=None,
                interpretation="Docking energy; not measured binding affinity.",
                caveats=(),
            ),
        ),
        validation_results=(),
        licenses=(),
        warnings=(),
    )


def test_run_manifest_round_trips_strictly() -> None:
    manifest = _manifest()

    reparsed = RunManifest.model_validate_json(manifest.model_dump_json())

    assert reparsed == manifest
    assert reparsed.predictions[0].type == "docking_energy"


def test_run_manifest_rejects_unsupported_schema_version() -> None:
    payload = _manifest().model_dump(mode="json")
    payload["schema_version"] = "1.0.0"

    with pytest.raises(ValidationError, match=r"0\.1\.0"):
        RunManifest.model_validate(payload)


def test_run_states_represent_partial_and_failed_attempts() -> None:
    partial = _run(
        state="partial",
        missing_outputs=("predicted complex",),
    )
    failed = _run(
        state="failed",
        failure=RunFailure(
            category="upstream_error",
            message="Synthetic upstream failure",
            stage="prediction",
            exit_code=2,
            details={},
        ),
    )

    assert partial.state == "partial"
    assert failed.state == "failed"


def test_failed_run_requires_structured_failure() -> None:
    with pytest.raises(ValidationError, match="failed run requires failure details"):
        _run(state="failed")


def test_partial_run_requires_missing_output_or_failure() -> None:
    with pytest.raises(ValidationError, match="partial run requires"):
        _run(state="partial")


def test_manifest_rejects_broken_artifact_lineage() -> None:
    manifest = _manifest()
    prediction = manifest.predictions[0].model_copy(
        update={
            "raw_source": PredictionRawSource(
                artifact_id="not-in-inventory",
                field="affinity",
                upstream_record_id=None,
            )
        }
    )

    with pytest.raises(ValidationError, match="unknown raw artifact"):
        RunManifest.model_validate(
            manifest.model_copy(update={"predictions": (prediction,)}).model_dump()
        )


def test_typed_predictions_preserve_distinct_semantics() -> None:
    source = PredictionRawSource(
        artifact_id="raw-output",
        field="value",
        upstream_record_id="pose-1",
    )
    common: dict[str, object] = {
        "id": "prediction",
        "value": 0.8,
        "scope": "pose",
        "scope_id": "pose-1",
        "method_id": "fixture-method",
        "raw_source": source,
        "uncertainty": None,
        "interpretation": "Synthetic evidence for contract testing.",
        "caveats": (),
    }

    pose = PoseConfidencePrediction.model_validate(
        common
        | {
            "type": "pose_confidence",
            "unit": None,
            "optimization_direction": "higher_is_better",
        }
    )
    structure = StructureConfidencePrediction.model_validate(
        common
        | {
            "type": "structure_confidence",
            "unit": None,
            "optimization_direction": "higher_is_better",
        }
    )
    binder = BinderProbabilityPrediction.model_validate(
        common
        | {
            "type": "binder_probability",
            "unit": "probability",
            "optimization_direction": "higher_is_better",
        }
    )
    affinity = PredictedAffinityPrediction.model_validate(
        common
        | {
            "type": "predicted_affinity",
            "unit": "pKd",
            "optimization_direction": "higher_is_better",
        }
    )

    assert pose.type != structure.type
    assert binder.unit == "probability"
    assert affinity.type == "predicted_affinity"


def test_binder_probability_rejects_values_outside_zero_to_one() -> None:
    with pytest.raises(ValidationError, match="less than or equal to 1"):
        BinderProbabilityPrediction(
            id="binder",
            type="binder_probability",
            value=1.1,
            unit="probability",
            scope="complex",
            scope_id="complex-1",
            method_id="fixture-method",
            raw_source=PredictionRawSource(
                artifact_id="raw-output",
                field="probability",
                upstream_record_id=None,
            ),
            optimization_direction="higher_is_better",
            uncertainty=None,
            interpretation="Binder probability; not measured biological activity.",
            caveats=(),
        )


def test_validation_result_retains_raw_traceability() -> None:
    result = ValidationResult(
        id="distance-check",
        validator="Synthetic Validator",
        validator_version="1.0.0",
        check_id="minimum_distance",
        status="fail",
        measured_value=0.4,
        unit="angstrom",
        threshold_or_configuration={"minimum": 1.0},
        explanation="Atoms are closer than the configured threshold.",
        input_artifact_id="raw-output",
        raw_output_artifact_id="raw-output",
    )

    assert result.status == "fail"
    assert result.raw_output_artifact_id == "raw-output"


def test_evidence_schema_has_no_unqualified_score_field() -> None:
    schema = RunManifest.model_json_schema()

    def collect_property_names(value: object) -> set[str]:
        if isinstance(value, dict):
            mapping = cast(dict[object, object], value)
            properties = mapping.get("properties")
            names: set[str] = set()
            if isinstance(properties, dict):
                property_mapping = cast(dict[object, object], properties)
                names.update(key for key in property_mapping if isinstance(key, str))
            for item in mapping.values():
                names.update(collect_property_names(item))
            return names
        if isinstance(value, list):
            items = cast(list[object], value)
            names = set()
            for item in items:
                names.update(collect_property_names(item))
            return names
        return set()

    assert "score" not in collect_property_names(schema)


def test_warning_is_structured_and_not_invented_metadata() -> None:
    warning = ManifestWarning(
        code="missing_upstream_version",
        message="Upstream version was not recorded.",
        path="method.upstream_version",
    )

    assert warning.code == "missing_upstream_version"
    assert warning.path == "method.upstream_version"
