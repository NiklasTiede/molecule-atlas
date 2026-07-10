import json
import math
import re
from pathlib import Path
from typing import cast

from pydantic import JsonValue

from molecule_atlas.evidence.adapters.contracts import (
    AdapterImportRequest,
    AdapterImportResultV020,
    AdapterLayoutError,
    AdapterMetadata,
)
from molecule_atlas.evidence.artifacts import inventory_artifact
from molecule_atlas.evidence.models import (
    Artifact,
    BinderProbabilityPrediction,
    EnvironmentMetadata,
    ManifestWarning,
    MethodMetadata,
    PredictedAffinityPrediction,
    Prediction,
    PredictionRawSource,
    RunManifest,
    RunMetadata,
    StructureConfidencePrediction,
)
from molecule_atlas.evidence.semantic_artifacts import ArtifactManifest, SemanticArtifact

_MODEL_FILE_PATTERN = re.compile(r"^(?P<target>.+)_model_(?P<rank>\d+)\.(?P<format>cif|pdb)$")
_CONFIDENCE_FILE_PATTERN = re.compile(r"^confidence_(?P<target>.+)_model_(?P<rank>\d+)\.json$")
_ARRAY_FILE_PATTERN = re.compile(
    r"^(?P<kind>plddt|pae|pde)_(?P<target>.+)_model_(?P<rank>\d+)\.npz$"
)

_METADATA = AdapterMetadata(
    adapter_id="boltz",
    adapter_version="0.1.0",
    title="Boltz prediction directory",
    description=(
        "Normalizes documented Boltz 2.2.1 structure-confidence and affinity outputs "
        "without importing or executing Boltz."
    ),
    upstream_tool="Boltz",
    source_format="boltz-prediction-directory",
    source_format_version="2.2.1",
    verified_upstream_versions=("2.2.1",),
    supported_manifest_versions=("0.1.0",),
)


def _prediction_target(source_root: Path) -> tuple[str, Path]:
    if not source_root.is_dir():
        raise AdapterLayoutError(
            "boltz_input_not_directory",
            f"Boltz input is not a directory: {source_root}",
        )

    predictions_root = source_root / "predictions"
    if not predictions_root.is_dir():
        raise AdapterLayoutError(
            "boltz_predictions_missing",
            f"Boltz predictions directory does not exist: {predictions_root}",
        )
    target_directories = sorted(path for path in predictions_root.iterdir() if path.is_dir())
    if not target_directories:
        raise AdapterLayoutError(
            "boltz_prediction_target_missing",
            f"Boltz predictions directory has no prediction target: {predictions_root}",
        )
    if len(target_directories) > 1:
        names = ", ".join(path.name for path in target_directories)
        raise AdapterLayoutError(
            "boltz_ambiguous_target",
            f"Boltz output contains multiple prediction targets: {names}",
        )
    return target_directories[0].name, target_directories[0]


def _json_object(path: Path) -> dict[str, JsonValue]:
    try:
        value = cast(object, json.loads(path.read_text(encoding="utf-8")))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AdapterLayoutError(
            "boltz_invalid_json",
            f"Boltz output contains invalid JSON in {path}: {error}",
        ) from error
    if not isinstance(value, dict):
        raise AdapterLayoutError(
            "boltz_invalid_json",
            f"Boltz output contains invalid JSON object in {path}",
        )
    raw_mapping = cast(dict[object, object], value)
    if not all(isinstance(key, str) for key in raw_mapping):
        raise AdapterLayoutError(
            "boltz_invalid_json",
            f"Boltz output contains invalid JSON object in {path}",
        )
    return cast(dict[str, JsonValue], raw_mapping)


def _required_number(payload: dict[str, JsonValue], field: str, *, path: Path) -> float:
    value = payload.get(field)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AdapterLayoutError(
            "boltz_invalid_field",
            f"Boltz output field {field!r} in {path} must be a finite number",
        )
    normalized = float(value)
    if not math.isfinite(normalized):
        raise AdapterLayoutError(
            "boltz_invalid_field",
            f"Boltz output field {field!r} in {path} must be a finite number",
        )
    return normalized


def _semantic_artifact(
    artifact: Artifact,
    *,
    logical_name: str,
    artifact_type: str,
    semantic_role: str,
    derived_from_artifact_ids: tuple[str, ...] = (),
) -> SemanticArtifact:
    return SemanticArtifact.model_validate(
        {
            "artifact_id": artifact.id,
            "logical_name": logical_name,
            "artifact_type": artifact_type,
            "schema_version": None,
            "semantic_role": semantic_role,
            "media_type": artifact.media_type,
            "path_or_uri": artifact.path_or_uri,
            "content_digest": f"sha256:{artifact.sha256}",
            "size_bytes": artifact.size_bytes,
            "derived_from_artifact_ids": derived_from_artifact_ids,
            "domain_metadata": artifact.metadata,
            "preview_metadata": {},
        },
        strict=True,
    )


class BoltzAdapter:
    """Offline normalizer for the documented Boltz 2.2.1 output layout."""

    @property
    def metadata(self) -> AdapterMetadata:
        return _METADATA

    def import_evidence(self, request: AdapterImportRequest) -> AdapterImportResultV020:
        source_root = request.source_path
        target, target_directory = _prediction_target(source_root)

        structure_paths: dict[int, Path] = {}
        confidence_paths: dict[int, Path] = {}
        array_paths: dict[tuple[str, int], Path] = {}
        affinity_path: Path | None = None
        for path in sorted(target_directory.iterdir()):
            if not path.is_file():
                continue
            if match := _MODEL_FILE_PATTERN.fullmatch(path.name):
                if match.group("target") == target:
                    structure_paths[int(match.group("rank"))] = path
                continue
            if match := _CONFIDENCE_FILE_PATTERN.fullmatch(path.name):
                if match.group("target") == target:
                    confidence_paths[int(match.group("rank"))] = path
                continue
            if match := _ARRAY_FILE_PATTERN.fullmatch(path.name):
                if match.group("target") == target:
                    array_paths[(match.group("kind"), int(match.group("rank")))] = path
                continue
            if path.name == f"affinity_{target}.json":
                affinity_path = path

        if (
            not structure_paths
            and not confidence_paths
            and not array_paths
            and affinity_path is None
        ):
            raise AdapterLayoutError(
                "boltz_no_supported_outputs",
                f"Prediction target {target!r} contains no supported Boltz outputs",
            )

        array_ranks = {rank for _, rank in array_paths}
        ranks = tuple(sorted(structure_paths.keys() | confidence_paths.keys() | array_ranks))
        expected_outputs: list[str] = []
        missing_outputs: list[str] = []
        for rank in ranks:
            expected_outputs.extend((f"predicted complex model {rank}", f"confidence model {rank}"))
            if rank not in structure_paths:
                missing_outputs.append(f"predicted complex model {rank}")
            if rank not in confidence_paths:
                missing_outputs.append(f"confidence model {rank}")
        if affinity_path is not None:
            expected_outputs.append("affinity")

        artifacts: list[Artifact] = []
        semantic_artifacts: list[SemanticArtifact] = []
        predictions: list[Prediction] = []
        method_id = "boltz-method"

        for rank in ranks:
            structure_path = structure_paths.get(rank)
            structure_artifact_id: str | None = None
            if structure_path is not None:
                structure_artifact_id = f"boltz-predicted-complex-model-{rank}"
                media_type = (
                    "chemical/x-mmcif" if structure_path.suffix == ".cif" else "chemical/x-pdb"
                )
                artifact = inventory_artifact(
                    structure_path,
                    root=source_root,
                    artifact_id=structure_artifact_id,
                    role="predicted_complex",
                    media_type=media_type,
                    created_by_stage="boltz_prediction",
                    metadata={"model_rank": rank, "prediction_target": target},
                )
                artifacts.append(artifact)
                semantic_artifacts.append(
                    _semantic_artifact(
                        artifact,
                        logical_name=f"predicted_complex_model_{rank}",
                        artifact_type="predicted-complex",
                        semantic_role="primary_output",
                    )
                )

            confidence_path = confidence_paths.get(rank)
            if confidence_path is not None:
                confidence_artifact_id = f"boltz-confidence-model-{rank}"
                artifact = inventory_artifact(
                    confidence_path,
                    root=source_root,
                    artifact_id=confidence_artifact_id,
                    role="raw_score_output",
                    media_type="application/json",
                    created_by_stage="boltz_prediction",
                    metadata={"model_rank": rank, "prediction_target": target},
                )
                artifacts.append(artifact)
                semantic_artifacts.append(
                    _semantic_artifact(
                        artifact,
                        logical_name=f"confidence_model_{rank}",
                        artifact_type="raw-prediction-output",
                        semantic_role="raw_output",
                        derived_from_artifact_ids=(
                            (structure_artifact_id,) if structure_artifact_id else ()
                        ),
                    )
                )
                confidence = _required_number(
                    _json_object(confidence_path),
                    "confidence_score",
                    path=confidence_path,
                )
                predictions.append(
                    StructureConfidencePrediction(
                        id=f"boltz-structure-confidence-model-{rank}",
                        value=confidence,
                        scope="complex",
                        scope_id=f"complex-model-{rank}",
                        method_id=method_id,
                        raw_source=PredictionRawSource(
                            artifact_id=confidence_artifact_id,
                            field="confidence_score",
                            upstream_record_id=f"{target}_model_{rank}",
                        ),
                        uncertainty=None,
                        interpretation=(
                            "Boltz aggregate confidence for the predicted complex structure."
                        ),
                        caveats=(
                            "Structure confidence is not affinity, activity, selectivity, or "
                            "experimental validation.",
                        ),
                    )
                )

            for array_kind in ("plddt", "pae", "pde"):
                array_path = array_paths.get((array_kind, rank))
                if array_path is None:
                    continue
                array_artifact_id = f"boltz-{array_kind}-model-{rank}"
                artifact = inventory_artifact(
                    array_path,
                    root=source_root,
                    artifact_id=array_artifact_id,
                    role="raw_score_output",
                    media_type="application/x-npz",
                    created_by_stage="boltz_prediction",
                    metadata={
                        "array_type": array_kind,
                        "model_rank": rank,
                        "prediction_target": target,
                    },
                )
                artifacts.append(artifact)
                semantic_artifacts.append(
                    _semantic_artifact(
                        artifact,
                        logical_name=f"{array_kind}_model_{rank}",
                        artifact_type="raw-prediction-output",
                        semantic_role="raw_output",
                        derived_from_artifact_ids=(
                            (structure_artifact_id,) if structure_artifact_id else ()
                        ),
                    )
                )

        if affinity_path is not None:
            affinity_artifact_id = "boltz-affinity"
            artifact = inventory_artifact(
                affinity_path,
                root=source_root,
                artifact_id=affinity_artifact_id,
                role="raw_score_output",
                media_type="application/json",
                created_by_stage="boltz_prediction",
                metadata={"prediction_target": target},
            )
            artifacts.append(artifact)
            semantic_artifacts.append(
                _semantic_artifact(
                    artifact,
                    logical_name="affinity",
                    artifact_type="raw-prediction-output",
                    semantic_role="raw_output",
                )
            )
            affinity_payload = _json_object(affinity_path)
            binder_probability = _required_number(
                affinity_payload,
                "affinity_probability_binary",
                path=affinity_path,
            )
            predicted_affinity = _required_number(
                affinity_payload,
                "affinity_pred_value",
                path=affinity_path,
            )
            predictions.extend(
                (
                    BinderProbabilityPrediction(
                        id="boltz-binder-probability",
                        value=binder_probability,
                        scope="complex",
                        scope_id=target,
                        method_id=method_id,
                        raw_source=PredictionRawSource(
                            artifact_id=affinity_artifact_id,
                            field="affinity_probability_binary",
                            upstream_record_id=target,
                        ),
                        uncertainty=None,
                        interpretation="Boltz predicted probability of binary binding.",
                        caveats=(
                            "Binder probability is a model prediction and does not establish "
                            "biological activity.",
                        ),
                    ),
                    PredictedAffinityPrediction(
                        id="boltz-predicted-affinity",
                        value=predicted_affinity,
                        scope="complex",
                        scope_id=target,
                        method_id=method_id,
                        raw_source=PredictionRawSource(
                            artifact_id=affinity_artifact_id,
                            field="affinity_pred_value",
                            upstream_record_id=target,
                        ),
                        uncertainty=None,
                        interpretation=(
                            "Boltz predicted log10(IC50) based on IC50 expressed in micromolar."
                        ),
                        caveats=(
                            "This is not measured affinity and does not establish activity, "
                            "selectivity, safety, or synthesizability.",
                        ),
                        unit="log10(IC50/µM)",
                        optimization_direction="lower_is_better",
                    ),
                )
            )

        manifest = RunManifest(
            schema_version="0.1.0",
            run=RunMetadata(
                id=f"boltz-{target}",
                state="partial" if missing_outputs else "succeeded",
                started_at=None,
                finished_at=None,
                expected_outputs=tuple(expected_outputs),
                missing_outputs=tuple(missing_outputs),
                failure=None,
            ),
            method=MethodMetadata(
                id=method_id,
                adapter_id=self.metadata.adapter_id,
                adapter_version=self.metadata.adapter_version,
                upstream_tool="Boltz",
                upstream_version=None,
                source_commit=None,
                checkpoint_id=None,
                checkpoint_sha256=None,
                container_image=None,
                container_digest=None,
                command=(),
                random_seeds=(),
                metadata={
                    "layout_compatibility": self.metadata.source_format_version,
                    "prediction_target": target,
                },
            ),
            inputs=(),
            parameters={},
            environment=EnvironmentMetadata(
                operating_system=None,
                architecture=None,
                python_version=None,
                accelerator=None,
                hardware=None,
                dependencies={},
            ),
            artifacts=tuple(artifacts),
            predictions=tuple(predictions),
            validation_results=(),
            licenses=(),
            warnings=(
                ManifestWarning(
                    code="upstream_version_not_recorded",
                    message=(
                        "The files match the documented Boltz 2.2.1 layout, but the actual "
                        "generating version was not recorded in the output."
                    ),
                    path="method.upstream_version",
                ),
            ),
        )
        return AdapterImportResultV020(
            adapter_id=self.metadata.adapter_id,
            adapter_version=self.metadata.adapter_version,
            artifact_root=source_root,
            manifest=manifest,
            artifact_manifest=ArtifactManifest(
                schema_version="0.1.0",
                artifacts=tuple(semantic_artifacts),
            ),
        )
