from pathlib import Path

import pytest
from molecule_atlas.evidence import (
    Artifact,
    ArtifactManifest,
    ArtifactSemanticRole,
    ArtifactType,
    RunManifest,
    SemanticArtifact,
    canonical_artifact_manifest_json_bytes,
    load_artifact_manifest,
    load_manifest,
    validate_artifact_manifest_against_run,
)
from pydantic import ValidationError

FIXTURE_ROOT = Path("../data/evidence-fixtures/succeeded")


def _semantic_artifact(
    artifact: Artifact,
    *,
    logical_name: str,
    artifact_type: ArtifactType,
    semantic_role: ArtifactSemanticRole,
    derived_from: tuple[str, ...] = (),
) -> SemanticArtifact:
    return SemanticArtifact(
        artifact_id=artifact.id,
        logical_name=logical_name,
        artifact_type=artifact_type,
        schema_version=None,
        semantic_role=semantic_role,
        media_type=artifact.media_type,
        path_or_uri=artifact.path_or_uri,
        content_digest=f"sha256:{artifact.sha256}",
        size_bytes=artifact.size_bytes,
        derived_from_artifact_ids=derived_from,
        domain_metadata={},
        preview_metadata={},
    )


def _artifact_manifest(run_manifest: RunManifest) -> ArtifactManifest:
    artifacts = {artifact.id: artifact for artifact in run_manifest.artifacts}
    return ArtifactManifest(
        schema_version="0.1.0",
        artifacts=(
            _semantic_artifact(
                artifacts["ligand"],
                logical_name="ligand_input",
                artifact_type="ligand-structure",
                semantic_role="input",
            ),
            _semantic_artifact(
                artifacts["predicted-pose"],
                logical_name="predicted_poses",
                artifact_type="docking-pose-set",
                semantic_role="primary_output",
                derived_from=("ligand",),
            ),
            _semantic_artifact(
                artifacts["raw-predictions"],
                logical_name="raw_predictions",
                artifact_type="raw-prediction-output",
                semantic_role="raw_output",
                derived_from=("ligand",),
            ),
            _semantic_artifact(
                artifacts["validation-output"],
                logical_name="validation_results",
                artifact_type="validation-report",
                semantic_role="validation_output",
                derived_from=("predicted-pose",),
            ),
        ),
    )


def test_artifact_manifest_round_trips_strictly() -> None:
    artifact_manifest = _artifact_manifest(load_manifest(FIXTURE_ROOT / "molecule-atlas-run.json"))

    reparsed = ArtifactManifest.model_validate_json(artifact_manifest.model_dump_json())

    assert reparsed == artifact_manifest
    assert reparsed.artifacts[1].artifact_type == "docking-pose-set"


def test_artifact_manifest_rejects_duplicate_ids_and_logical_names() -> None:
    artifact_manifest = _artifact_manifest(load_manifest(FIXTURE_ROOT / "molecule-atlas-run.json"))
    first, second = artifact_manifest.artifacts[:2]

    with pytest.raises(ValidationError, match="duplicate artifact IDs: ligand"):
        ArtifactManifest(
            schema_version="0.1.0",
            artifacts=(first, second.model_copy(update={"artifact_id": "ligand"})),
        )

    with pytest.raises(ValidationError, match="duplicate logical names: ligand_input"):
        ArtifactManifest(
            schema_version="0.1.0",
            artifacts=(first, second.model_copy(update={"logical_name": "ligand_input"})),
        )


def test_artifact_manifest_rejects_unresolved_and_self_derivation() -> None:
    artifact_manifest = _artifact_manifest(load_manifest(FIXTURE_ROOT / "molecule-atlas-run.json"))
    first = artifact_manifest.artifacts[0]

    with pytest.raises(ValidationError, match="derives from unknown artifact missing"):
        ArtifactManifest(
            schema_version="0.1.0",
            artifacts=(first.model_copy(update={"derived_from_artifact_ids": ("missing",)}),),
        )

    with pytest.raises(ValidationError, match="artifact ligand cannot derive from itself"):
        ArtifactManifest(
            schema_version="0.1.0",
            artifacts=(first.model_copy(update={"derived_from_artifact_ids": ("ligand",)}),),
        )

    with pytest.raises(ValidationError, match="repeats derivation sources: ligand"):
        ArtifactManifest(
            schema_version="0.1.0",
            artifacts=(
                first,
                artifact_manifest.artifacts[1].model_copy(
                    update={"derived_from_artifact_ids": ("ligand", "ligand")}
                ),
            ),
        )


def test_artifact_manifest_rejects_derivation_cycles() -> None:
    artifact_manifest = _artifact_manifest(load_manifest(FIXTURE_ROOT / "molecule-atlas-run.json"))
    first, second = artifact_manifest.artifacts[:2]

    with pytest.raises(
        ValidationError,
        match="derivation cycle: ligand -> predicted-pose -> ligand",
    ):
        ArtifactManifest(
            schema_version="0.1.0",
            artifacts=(
                first.model_copy(update={"derived_from_artifact_ids": ("predicted-pose",)}),
                second.model_copy(update={"derived_from_artifact_ids": ("ligand",)}),
            ),
        )


def test_artifact_manifest_cross_checks_run_inventory() -> None:
    run_manifest = load_manifest(FIXTURE_ROOT / "molecule-atlas-run.json")
    artifact_manifest = _artifact_manifest(run_manifest)

    validate_artifact_manifest_against_run(artifact_manifest, run_manifest=run_manifest)


def test_artifact_manifest_requires_algorithm_qualified_content_digest() -> None:
    artifact_manifest = _artifact_manifest(load_manifest(FIXTURE_ROOT / "molecule-atlas-run.json"))
    payload = artifact_manifest.artifacts[0].model_dump()
    payload["content_digest"] = "a" * 64

    with pytest.raises(ValidationError, match="String should match pattern"):
        SemanticArtifact.model_validate(payload)


def test_artifact_manifest_cross_check_rejects_missing_record() -> None:
    run_manifest = load_manifest(FIXTURE_ROOT / "molecule-atlas-run.json")
    artifact_manifest = _artifact_manifest(run_manifest)

    with pytest.raises(ValueError, match="missing semantic artifacts: validation-output"):
        validate_artifact_manifest_against_run(
            artifact_manifest.model_copy(update={"artifacts": artifact_manifest.artifacts[:-1]}),
            run_manifest=run_manifest,
        )


@pytest.mark.parametrize(
    ("field", "value", "label"),
    [
        ("path_or_uri", "artifacts/other.sdf", "path"),
        ("media_type", "application/octet-stream", "media type"),
        ("content_digest", f"sha256:{'a' * 64}", "content digest"),
        ("size_bytes", 999, "size"),
    ],
)
def test_artifact_manifest_cross_check_rejects_mismatched_record(
    field: str,
    value: object,
    label: str,
) -> None:
    run_manifest = load_manifest(FIXTURE_ROOT / "molecule-atlas-run.json")
    artifact_manifest = _artifact_manifest(run_manifest)
    changed = artifact_manifest.artifacts[0].model_copy(update={field: value})

    with pytest.raises(ValueError, match=f"artifact ligand {label} does not match RunManifest"):
        validate_artifact_manifest_against_run(
            artifact_manifest.model_copy(
                update={"artifacts": (changed, *artifact_manifest.artifacts[1:])}
            ),
            run_manifest=run_manifest,
        )


def test_checked_in_artifact_manifest_is_canonical_and_bound_to_run() -> None:
    artifact_manifest_path = FIXTURE_ROOT / "molecule-atlas-artifacts.json"
    artifact_manifest = load_artifact_manifest(artifact_manifest_path)
    run_manifest = load_manifest(FIXTURE_ROOT / "molecule-atlas-run.json")

    assert artifact_manifest_path.read_bytes() == canonical_artifact_manifest_json_bytes(
        artifact_manifest
    )
    validate_artifact_manifest_against_run(artifact_manifest, run_manifest=run_manifest)
