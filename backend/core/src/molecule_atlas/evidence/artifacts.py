from hashlib import sha256
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, JsonValue

from molecule_atlas.evidence.models import Artifact, ArtifactRole, EvidenceModel

ArtifactVerificationStatus = Literal[
    "verified",
    "missing",
    "mismatch",
    "external",
    "unsafe_path",
    "unreadable",
]


class ArtifactInventoryError(ValueError):
    """Raised when a local artifact cannot be safely inventoried."""


class ArtifactDigest(EvidenceModel):
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(ge=0)


class ArtifactCheck(EvidenceModel):
    artifact_id: str = Field(min_length=1)
    status: ArtifactVerificationStatus
    actual_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    actual_size_bytes: int | None = Field(default=None, ge=0)
    message: str = Field(min_length=1)


def hash_file(path: Path, *, chunk_size: int = 1024 * 1024) -> ArtifactDigest:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if not path.is_file():
        raise ArtifactInventoryError(f"Artifact is not a regular file: {path}")

    digest = sha256()
    size_bytes = 0
    try:
        with path.open("rb") as stream:
            while chunk := stream.read(chunk_size):
                digest.update(chunk)
                size_bytes += len(chunk)
    except OSError as error:
        raise ArtifactInventoryError(f"Could not read artifact {path}: {error}") from error
    return ArtifactDigest(sha256=digest.hexdigest(), size_bytes=size_bytes)


def _contained_path(path: Path, root: Path) -> tuple[Path, Path]:
    try:
        resolved_root = root.resolve(strict=True)
    except OSError as error:
        raise ArtifactInventoryError(f"Run root does not exist: {root}") from error
    try:
        resolved_path = path.resolve(strict=True)
    except OSError as error:
        raise ArtifactInventoryError(f"Artifact does not exist: {path}") from error
    if not resolved_root.is_dir():
        raise ArtifactInventoryError(f"Run root is not a directory: {root}")
    if not resolved_path.is_relative_to(resolved_root):
        raise ArtifactInventoryError(f"Artifact is outside the run root: {path}")
    return resolved_path, resolved_root


def inventory_artifact(
    path: Path,
    *,
    root: Path,
    artifact_id: str,
    role: ArtifactRole,
    media_type: str,
    created_by_stage: str,
    metadata: dict[str, JsonValue],
) -> Artifact:
    resolved_path, resolved_root = _contained_path(path, root)
    digest = hash_file(resolved_path)
    return Artifact(
        id=artifact_id,
        role=role,
        path_or_uri=resolved_path.relative_to(resolved_root).as_posix(),
        media_type=media_type,
        sha256=digest.sha256,
        size_bytes=digest.size_bytes,
        created_by_stage=created_by_stage,
        original_name=resolved_path.name,
        metadata=metadata,
    )


def _artifact_local_path(artifact: Artifact, root: Path) -> Path | None:
    parsed = urlsplit(artifact.path_or_uri)
    if parsed.scheme or parsed.netloc:
        return None
    candidate = Path(artifact.path_or_uri)
    if not candidate.is_absolute():
        candidate = root / candidate
    return candidate


def verify_artifact(artifact: Artifact, *, root: Path) -> ArtifactCheck:
    path = _artifact_local_path(artifact, root)
    if path is None:
        return ArtifactCheck(
            artifact_id=artifact.id,
            status="external",
            actual_sha256=None,
            actual_size_bytes=None,
            message="External artifact was not fetched during the offline audit.",
        )

    resolved_root = root.resolve()
    resolved_path = path.resolve()
    if not resolved_path.is_relative_to(resolved_root):
        return ArtifactCheck(
            artifact_id=artifact.id,
            status="unsafe_path",
            actual_sha256=None,
            actual_size_bytes=None,
            message="Artifact path resolves outside the run root.",
        )
    if not resolved_path.exists():
        return ArtifactCheck(
            artifact_id=artifact.id,
            status="missing",
            actual_sha256=None,
            actual_size_bytes=None,
            message="Artifact file is missing.",
        )

    try:
        digest = hash_file(resolved_path)
    except ArtifactInventoryError as error:
        return ArtifactCheck(
            artifact_id=artifact.id,
            status="unreadable",
            actual_sha256=None,
            actual_size_bytes=None,
            message=str(error),
        )
    if digest.sha256 != artifact.sha256 or digest.size_bytes != artifact.size_bytes:
        return ArtifactCheck(
            artifact_id=artifact.id,
            status="mismatch",
            actual_sha256=digest.sha256,
            actual_size_bytes=digest.size_bytes,
            message="Artifact bytes do not match the declared SHA-256 and size.",
        )
    return ArtifactCheck(
        artifact_id=artifact.id,
        status="verified",
        actual_sha256=digest.sha256,
        actual_size_bytes=digest.size_bytes,
        message="Artifact SHA-256 and size are verified.",
    )


def verify_artifacts(
    artifacts: tuple[Artifact, ...],
    *,
    root: Path,
) -> tuple[ArtifactCheck, ...]:
    return tuple(verify_artifact(artifact, root=root) for artifact in artifacts)
