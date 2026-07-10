from pathlib import Path

import pytest
from molecule_atlas.evidence import (
    ArtifactInventoryError,
    hash_file,
    inventory_artifact,
    verify_artifact,
)


def test_hash_file_returns_deterministic_sha256_and_size(tmp_path: Path) -> None:
    first = tmp_path / "first.bin"
    second = tmp_path / "second.bin"
    first.write_bytes(b"abc")
    second.write_bytes(b"abc")

    first_digest = hash_file(first)
    second_digest = hash_file(second)

    assert first_digest.sha256 == (
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )
    assert first_digest == second_digest
    assert first_digest.size_bytes == 3


def test_inventory_artifact_uses_portable_relative_path(tmp_path: Path) -> None:
    artifact_path = tmp_path / "artifacts" / "raw.json"
    artifact_path.parent.mkdir()
    artifact_path.write_text('{"value":0.8}\n', encoding="utf-8")

    artifact = inventory_artifact(
        artifact_path,
        root=tmp_path,
        artifact_id="raw-output",
        role="raw_score_output",
        media_type="application/json",
        created_by_stage="prediction",
        metadata={"upstream": True},
    )

    assert artifact.path_or_uri == "artifacts/raw.json"
    assert artifact.original_name == "raw.json"
    assert artifact.size_bytes == artifact_path.stat().st_size
    assert len(artifact.sha256) == 64


def test_inventory_artifact_rejects_path_outside_root(tmp_path: Path) -> None:
    root = tmp_path / "run"
    root.mkdir()
    outside = tmp_path / "outside.json"
    outside.write_text("{}\n", encoding="utf-8")

    with pytest.raises(ArtifactInventoryError, match="outside the run root"):
        inventory_artifact(
            outside,
            root=root,
            artifact_id="outside",
            role="other",
            media_type="application/json",
            created_by_stage="import",
            metadata={},
        )


def test_verify_artifact_detects_hash_mismatch(tmp_path: Path) -> None:
    artifact_path = tmp_path / "raw.txt"
    artifact_path.write_text("raw evidence\n", encoding="utf-8")
    artifact = inventory_artifact(
        artifact_path,
        root=tmp_path,
        artifact_id="raw",
        role="other",
        media_type="text/plain",
        created_by_stage="import",
        metadata={},
    ).model_copy(update={"sha256": "0" * 64})

    check = verify_artifact(artifact, root=tmp_path)

    assert check.status == "mismatch"
    assert check.actual_sha256 is not None
    assert check.actual_sha256 != artifact.sha256


def test_verify_artifact_reports_missing_file(tmp_path: Path) -> None:
    artifact_path = tmp_path / "raw.txt"
    artifact_path.write_text("raw evidence\n", encoding="utf-8")
    artifact = inventory_artifact(
        artifact_path,
        root=tmp_path,
        artifact_id="raw",
        role="other",
        media_type="text/plain",
        created_by_stage="import",
        metadata={},
    )
    artifact_path.unlink()

    check = verify_artifact(artifact, root=tmp_path)

    assert check.status == "missing"
    assert check.actual_sha256 is None
