import json
from pathlib import Path
from typing import cast

from molecule_atlas.evidence.models import RunManifest


def canonical_json_bytes(manifest: RunManifest) -> bytes:
    """Serialize a manifest into the stable Molecule Atlas JSON representation."""

    payload = manifest.model_dump(mode="json")
    serialized = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return f"{serialized}\n".encode()


def load_manifest(path: Path) -> RunManifest:
    return RunManifest.model_validate_json(path.read_bytes())


def write_manifest(path: Path, manifest: RunManifest) -> None:
    path.write_bytes(canonical_json_bytes(manifest))


def manifest_schema() -> dict[str, object]:
    return cast(dict[str, object], RunManifest.model_json_schema(mode="validation"))


def manifest_schema_json() -> str:
    return f"{json.dumps(manifest_schema(), ensure_ascii=False, indent=2, sort_keys=True)}\n"


def write_manifest_schema(path: Path) -> None:
    path.write_text(manifest_schema_json(), encoding="utf-8")
