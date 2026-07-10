import json
from pathlib import Path
from typing import cast

from molecule_atlas.evidence.models import EvidenceModel, RunManifest
from molecule_atlas.evidence.semantic_artifacts import ArtifactManifest


def _canonical_model_json_bytes(model: EvidenceModel) -> bytes:
    payload = model.model_dump(mode="json")
    serialized = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return f"{serialized}\n".encode()


def canonical_json_bytes(manifest: RunManifest) -> bytes:
    """Serialize a run manifest into the stable Molecule Atlas JSON representation."""

    return _canonical_model_json_bytes(manifest)


def canonical_artifact_manifest_json_bytes(manifest: ArtifactManifest) -> bytes:
    """Serialize an artifact manifest into the stable Molecule Atlas representation."""

    return _canonical_model_json_bytes(manifest)


def load_manifest(path: Path) -> RunManifest:
    return RunManifest.model_validate_json(path.read_bytes())


def load_artifact_manifest(path: Path) -> ArtifactManifest:
    return ArtifactManifest.model_validate_json(path.read_bytes())


def write_manifest(path: Path, manifest: RunManifest) -> None:
    path.write_bytes(canonical_json_bytes(manifest))


def write_artifact_manifest(path: Path, manifest: ArtifactManifest) -> None:
    path.write_bytes(canonical_artifact_manifest_json_bytes(manifest))


def manifest_schema() -> dict[str, object]:
    return cast(dict[str, object], RunManifest.model_json_schema(mode="validation"))


def manifest_schema_json() -> str:
    return f"{json.dumps(manifest_schema(), ensure_ascii=False, indent=2, sort_keys=True)}\n"


def artifact_manifest_schema() -> dict[str, object]:
    return cast(dict[str, object], ArtifactManifest.model_json_schema(mode="validation"))


def artifact_manifest_schema_json() -> str:
    serialized = json.dumps(
        artifact_manifest_schema(),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
    return f"{serialized}\n"


def write_manifest_schema(path: Path) -> None:
    path.write_text(manifest_schema_json(), encoding="utf-8")


def write_artifact_manifest_schema(path: Path) -> None:
    path.write_text(artifact_manifest_schema_json(), encoding="utf-8")
