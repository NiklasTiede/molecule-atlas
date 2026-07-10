import math
import re
from pathlib import Path

from molecule_atlas.evidence.adapters.contracts import (
    AdapterImportRequest,
    AdapterImportResultV020,
    AdapterLayoutError,
    AdapterMetadata,
)
from molecule_atlas.evidence.artifacts import inventory_artifact
from molecule_atlas.evidence.models import (
    Artifact,
    EnvironmentMetadata,
    ManifestWarning,
    MethodMetadata,
    PoseConfidencePrediction,
    PredictionRawSource,
    RunManifest,
    RunMetadata,
)
from molecule_atlas.evidence.semantic_artifacts import ArtifactManifest, SemanticArtifact

_RANKED_POSE_PATTERN = re.compile(
    r"^rank(?P<rank>[1-9]\d*)_confidence"
    r"(?P<confidence>-?(?:\d+(?:\.\d*)?|\.\d+))\.sdf$"
)
_TOP_POSE_ALIAS = "rank1.sdf"

_METADATA = AdapterMetadata(
    adapter_id="diffdock",
    adapter_version="0.1.0",
    title="DiffDock complex directory",
    description=(
        "Normalizes documented DiffDock 1.1.3 ranked ligand poses and pose-confidence "
        "values without importing or executing DiffDock."
    ),
    upstream_tool="DiffDock",
    source_format="diffdock-complex-directory",
    source_format_version="1.1.3",
    verified_upstream_versions=("1.1.3",),
    supported_manifest_versions=("0.1.0",),
)


def _contains_ranked_pose(path: Path) -> bool:
    return path.is_dir() and any(
        candidate.is_file() and _RANKED_POSE_PATTERN.fullmatch(candidate.name)
        for candidate in path.iterdir()
    )


def _complex_directory(source_root: Path) -> tuple[str, Path]:
    if not source_root.is_dir():
        raise AdapterLayoutError(
            "diffdock_input_not_directory",
            f"DiffDock input is not a directory: {source_root}",
        )
    if _contains_ranked_pose(source_root):
        return source_root.name, source_root

    complex_directories = sorted(path for path in source_root.iterdir() if path.is_dir())
    if not complex_directories:
        raise AdapterLayoutError(
            "diffdock_complex_missing",
            f"DiffDock output has no complex directory: {source_root}",
        )
    if len(complex_directories) > 1:
        names = ", ".join(path.name for path in complex_directories)
        raise AdapterLayoutError(
            "diffdock_ambiguous_complex",
            f"DiffDock output contains multiple complex directories: {names}",
        )
    return complex_directories[0].name, complex_directories[0]


def _semantic_artifact(
    artifact: Artifact,
    *,
    logical_name: str,
    semantic_role: str,
) -> SemanticArtifact:
    return SemanticArtifact.model_validate(
        {
            "artifact_id": artifact.id,
            "logical_name": logical_name,
            "artifact_type": "ligand-structure",
            "schema_version": None,
            "semantic_role": semantic_role,
            "media_type": artifact.media_type,
            "path_or_uri": artifact.path_or_uri,
            "content_digest": f"sha256:{artifact.sha256}",
            "size_bytes": artifact.size_bytes,
            "derived_from_artifact_ids": (),
            "domain_metadata": artifact.metadata,
            "preview_metadata": {},
        },
        strict=True,
    )


class DiffDockAdapter:
    """Offline normalizer for the documented DiffDock 1.1.3 output layout."""

    @property
    def metadata(self) -> AdapterMetadata:
        return _METADATA

    def import_evidence(self, request: AdapterImportRequest) -> AdapterImportResultV020:
        source_root = request.source_path
        complex_name, complex_directory = _complex_directory(source_root)

        ranked_paths: dict[int, tuple[Path, float]] = {}
        for path in sorted(complex_directory.iterdir()):
            if not path.is_file() or not (match := _RANKED_POSE_PATTERN.fullmatch(path.name)):
                continue
            rank = int(match.group("rank"))
            if rank in ranked_paths:
                raise AdapterLayoutError(
                    "diffdock_duplicate_rank",
                    f"DiffDock output contains multiple files for pose rank {rank}",
                )
            confidence = float(match.group("confidence"))
            if not math.isfinite(confidence):
                raise AdapterLayoutError(
                    "diffdock_invalid_confidence",
                    f"DiffDock pose rank {rank} has a non-finite filename confidence",
                )
            ranked_paths[rank] = (path, confidence)

        if not ranked_paths:
            raise AdapterLayoutError(
                "diffdock_no_supported_outputs",
                f"Complex {complex_name!r} contains no supported ranked pose outputs",
            )

        maximum_rank = max(ranked_paths)
        expected_outputs = tuple(f"pose rank {rank}" for rank in range(1, maximum_rank + 1))
        missing_outputs = tuple(
            f"pose rank {rank}" for rank in range(1, maximum_rank + 1) if rank not in ranked_paths
        )
        artifacts: list[Artifact] = []
        semantic_artifacts: list[SemanticArtifact] = []
        predictions: list[PoseConfidencePrediction] = []
        method_id = "diffdock-method"

        for rank, (path, confidence) in sorted(ranked_paths.items()):
            artifact_id = f"diffdock-pose-rank-{rank}"
            artifact = inventory_artifact(
                path,
                root=source_root,
                artifact_id=artifact_id,
                role="pose_set",
                media_type="chemical/x-mdl-sdfile",
                created_by_stage="diffdock_prediction",
                metadata={
                    "pose_confidence": confidence,
                    "rank": rank,
                    "representation": "predicted_pose",
                    "complex_name": complex_name,
                },
            )
            artifacts.append(artifact)
            semantic_artifacts.append(
                _semantic_artifact(
                    artifact,
                    logical_name=f"pose_rank_{rank}",
                    semantic_role="primary_output",
                )
            )
            predictions.append(
                PoseConfidencePrediction(
                    id=f"diffdock-pose-confidence-rank-{rank}",
                    value=confidence,
                    scope="pose",
                    scope_id=f"pose-rank-{rank}",
                    method_id=method_id,
                    raw_source=PredictionRawSource(
                        artifact_id=artifact_id,
                        field="filename.confidence",
                        upstream_record_id=path.name,
                    ),
                    uncertainty=None,
                    interpretation=(
                        "DiffDock confidence in the quality of this predicted binding pose."
                    ),
                    caveats=(
                        "DiffDock pose confidence is not binding affinity and is not directly "
                        "comparable across arbitrary complexes or protein conformations.",
                    ),
                )
            )

        top_pose_alias = complex_directory / _TOP_POSE_ALIAS
        if top_pose_alias.is_file():
            artifact = inventory_artifact(
                top_pose_alias,
                root=source_root,
                artifact_id="diffdock-top-pose-alias",
                role="pose_set",
                media_type="chemical/x-mdl-sdfile",
                created_by_stage="diffdock_prediction",
                metadata={
                    "rank": 1,
                    "representation": "predicted_pose",
                    "complex_name": complex_name,
                    "upstream_alias": True,
                },
            )
            artifacts.append(artifact)
            semantic_artifacts.append(
                _semantic_artifact(
                    artifact,
                    logical_name="top_pose_alias",
                    semantic_role="raw_output",
                )
            )

        manifest = RunManifest(
            schema_version="0.1.0",
            run=RunMetadata(
                id=f"diffdock-{complex_name}",
                state="partial" if missing_outputs else "succeeded",
                started_at=None,
                finished_at=None,
                expected_outputs=expected_outputs,
                missing_outputs=missing_outputs,
                failure=None,
            ),
            method=MethodMetadata(
                id=method_id,
                adapter_id=self.metadata.adapter_id,
                adapter_version=self.metadata.adapter_version,
                upstream_tool="DiffDock",
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
                    "complex_name": complex_name,
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
                        "The files match the documented DiffDock 1.1.3 layout, but the actual "
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
