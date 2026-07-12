import shutil
import stat
from collections.abc import Iterable
from io import BytesIO
from pathlib import Path, PurePosixPath
from threading import Lock
from uuid import uuid4
from zipfile import ZIP_DEFLATED, ZIP_STORED, BadZipFile, ZipFile, ZipInfo

from molecule_atlas.evidence.adapters.manifest import MANIFEST_FILENAME
from molecule_atlas.evidence.audit import audit_manifest
from molecule_atlas.evidence.models import RunManifest
from molecule_atlas.evidence.semantic_artifacts import (
    ArtifactManifest,
    validate_artifact_manifest_against_run,
)
from molecule_atlas.evidence.serialization import (
    load_artifact_manifest,
    load_manifest,
)

from app.application.evidence.ports import (
    EvidenceBundleConflictError,
    EvidenceBundleInputError,
    EvidenceBundleLimitError,
    StoredEvidenceRun,
)

ARTIFACT_MANIFEST_FILENAME = "molecule-atlas-artifacts.json"
MAX_BUNDLE_MEMBERS = 256
MAX_MEMBER_BYTES = 25 * 1024 * 1024
MAX_UNCOMPRESSED_BYTES = 100 * 1024 * 1024
_ALLOWED_COMPRESSIONS = frozenset({ZIP_STORED, ZIP_DEFLATED})
_INVALID_ARTIFACT_STATUSES = frozenset({"missing", "mismatch", "unsafe_path", "unreadable"})


def _member_path(info: ZipInfo) -> PurePosixPath:
    name = info.filename
    path = PurePosixPath(name)
    if (
        not name
        or "\x00" in name
        or "\\" in name
        or path.is_absolute()
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise EvidenceBundleInputError(f"Bundle member path is unsafe: {name}")
    mode = info.external_attr >> 16
    if stat.S_ISLNK(mode):
        raise EvidenceBundleInputError(f"Bundle member is a symbolic link: {name}")
    if info.flag_bits & 0x1:
        raise EvidenceBundleInputError(f"Bundle member is encrypted: {name}")
    if info.compress_type not in _ALLOWED_COMPRESSIONS:
        raise EvidenceBundleInputError(f"Bundle member uses unsupported compression: {name}")
    return path


def _validated_members(archive: ZipFile) -> tuple[tuple[ZipInfo, PurePosixPath], ...]:
    infos = tuple(archive.infolist())
    if len(infos) > MAX_BUNDLE_MEMBERS:
        raise EvidenceBundleLimitError(
            f"Bundle contains too many members: {len(infos)} > {MAX_BUNDLE_MEMBERS}"
        )

    members: list[tuple[ZipInfo, PurePosixPath]] = []
    names: set[str] = set()
    total_size = 0
    for info in infos:
        path = _member_path(info)
        normalized_name = path.as_posix()
        if normalized_name in names:
            raise EvidenceBundleInputError(f"Bundle contains duplicate member: {normalized_name}")
        names.add(normalized_name)
        if info.file_size > MAX_MEMBER_BYTES:
            raise EvidenceBundleLimitError(
                f"Bundle member exceeds the {MAX_MEMBER_BYTES}-byte limit: {normalized_name}"
            )
        total_size += info.file_size
        if total_size > MAX_UNCOMPRESSED_BYTES:
            raise EvidenceBundleLimitError(
                f"Bundle uncompressed contents exceed the {MAX_UNCOMPRESSED_BYTES}-byte limit"
            )
        members.append((info, path))
    return tuple(members)


def _extract_bundle(archive_bytes: bytes, destination: Path) -> None:
    try:
        with ZipFile(BytesIO(archive_bytes)) as archive:
            members = _validated_members(archive)
            actual_total = 0
            for info, relative_path in members:
                target = destination.joinpath(*relative_path.parts)
                if info.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                actual_member_size = 0
                with archive.open(info) as source, target.open("xb") as output:
                    while chunk := source.read(64 * 1024):
                        actual_member_size += len(chunk)
                        actual_total += len(chunk)
                        if actual_member_size > MAX_MEMBER_BYTES:
                            raise EvidenceBundleLimitError(
                                f"Bundle member exceeds the {MAX_MEMBER_BYTES}-byte limit: "
                                f"{relative_path.as_posix()}"
                            )
                        if actual_total > MAX_UNCOMPRESSED_BYTES:
                            raise EvidenceBundleLimitError(
                                "Bundle uncompressed contents exceed the "
                                f"{MAX_UNCOMPRESSED_BYTES}-byte limit"
                            )
                        output.write(chunk)
    except EvidenceBundleInputError:
        raise
    except (BadZipFile, OSError, RuntimeError, ValueError) as error:
        raise EvidenceBundleInputError(f"Evidence bundle is not a readable ZIP: {error}") from error


def _load_and_validate_bundle(root: Path) -> StoredEvidenceRun:
    manifest_path = root / MANIFEST_FILENAME
    if not manifest_path.is_file():
        raise EvidenceBundleInputError(f"Bundle root must contain {MANIFEST_FILENAME}")
    try:
        manifest = load_manifest(manifest_path)
    except (OSError, ValueError) as error:
        raise EvidenceBundleInputError(f"Run manifest validation failed: {error}") from error

    artifact_manifest = _load_artifact_manifest(root, run_manifest=manifest)

    audit = audit_manifest(manifest, root=root)
    invalid_checks = tuple(
        check for check in audit.artifact_checks if check.status in _INVALID_ARTIFACT_STATUSES
    )
    if invalid_checks:
        details = ", ".join(f"{check.artifact_id}={check.status}" for check in invalid_checks)
        raise EvidenceBundleInputError(f"Declared artifact validation failed: {details}")
    return StoredEvidenceRun(
        root=root,
        manifest=manifest,
        artifact_manifest=artifact_manifest,
    )


def _load_artifact_manifest(
    root: Path,
    *,
    run_manifest: RunManifest,
) -> ArtifactManifest | None:
    artifact_manifest_path = root / ARTIFACT_MANIFEST_FILENAME
    if not artifact_manifest_path.exists():
        return None
    try:
        artifact_manifest = load_artifact_manifest(artifact_manifest_path)
        validate_artifact_manifest_against_run(
            artifact_manifest,
            run_manifest=run_manifest,
        )
    except (OSError, ValueError) as error:
        raise EvidenceBundleInputError(
            f"Semantic artifact manifest validation failed: {error}"
        ) from error
    return artifact_manifest


class LocalEvidenceRunRepository:
    """Local manifest index with optional bounded temporary bundle publication."""

    def __init__(self, roots: Iterable[Path], *, upload_root: Path | None = None) -> None:
        by_run_id: dict[str, StoredEvidenceRun] = {}
        for root in roots:
            if not root.is_dir():
                continue
            for manifest_path in sorted(root.rglob(MANIFEST_FILENAME)):
                manifest = load_manifest(manifest_path)
                run_id = manifest.run.id
                if run_id in by_run_id:
                    raise ValueError(f"duplicate local evidence run ID: {run_id}")
                by_run_id[run_id] = StoredEvidenceRun(
                    root=manifest_path.parent,
                    manifest=manifest,
                    artifact_manifest=_load_artifact_manifest(
                        manifest_path.parent,
                        run_manifest=manifest,
                    ),
                )
        if upload_root is not None:
            upload_root.mkdir(parents=True, exist_ok=True)
        self._upload_root = upload_root
        self._by_run_id = by_run_id
        self._lock = Lock()

    def find(self, run_id: str) -> StoredEvidenceRun | None:
        with self._lock:
            return self._by_run_id.get(run_id)

    def list_runs(self) -> tuple[StoredEvidenceRun, ...]:
        with self._lock:
            return tuple(self._by_run_id.values())

    def import_bundle(self, archive_bytes: bytes) -> StoredEvidenceRun:
        if self._upload_root is None:
            raise EvidenceBundleInputError("Local evidence imports are not configured")

        import_id = uuid4().hex
        staging_root = self._upload_root / f".staging-{import_id}"
        published_root = self._upload_root / import_id
        staging_root.mkdir()
        try:
            _extract_bundle(archive_bytes, staging_root)
            staged_run = _load_and_validate_bundle(staging_root)
            with self._lock:
                if staged_run.manifest.run.id in self._by_run_id:
                    raise EvidenceBundleConflictError(
                        f"Evidence run already exists: {staged_run.manifest.run.id}"
                    )
                staging_root.rename(published_root)
                stored_run = StoredEvidenceRun(
                    root=published_root,
                    manifest=staged_run.manifest,
                    artifact_manifest=staged_run.artifact_manifest,
                )
                self._by_run_id[stored_run.manifest.run.id] = stored_run
                return stored_run
        except Exception:
            shutil.rmtree(staging_root, ignore_errors=True)
            raise
