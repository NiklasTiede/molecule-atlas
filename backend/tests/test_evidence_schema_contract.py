import json
from pathlib import Path

from molecule_atlas.evidence import artifact_manifest_schema, manifest_schema

SCHEMA_PATH = Path(__file__).parents[2] / "schemas" / "run-manifest" / "0.1.0.schema.json"
ARTIFACT_SCHEMA_PATH = (
    Path(__file__).parents[2] / "schemas" / "artifact-manifest" / "0.1.0.schema.json"
)


def test_checked_in_run_manifest_schema_matches_core_models() -> None:
    checked_in_schema: object = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    assert checked_in_schema == manifest_schema()


def test_checked_in_artifact_manifest_schema_matches_core_models() -> None:
    checked_in_schema: object = json.loads(ARTIFACT_SCHEMA_PATH.read_text(encoding="utf-8"))

    assert checked_in_schema == artifact_manifest_schema()
