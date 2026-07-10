from pathlib import Path

from molecule_atlas.evidence.artifacts import ArtifactCheck, verify_artifacts
from molecule_atlas.evidence.models import EvidenceModel, ManifestWarning, RunManifest


class ManifestAudit(EvidenceModel):
    manifest: RunManifest
    artifact_checks: tuple[ArtifactCheck, ...]


def _warning(code: str, message: str, path: str) -> ManifestWarning:
    return ManifestWarning(code=code, message=message, path=path)


def provenance_warnings(manifest: RunManifest) -> tuple[ManifestWarning, ...]:
    warnings: list[ManifestWarning] = []
    method = manifest.method
    if method.upstream_tool is None:
        warnings.append(
            _warning(
                "missing_upstream_tool",
                "Upstream tool identity was not recorded.",
                "method.upstream_tool",
            )
        )
    if method.upstream_version is None and method.source_commit is None:
        warnings.append(
            _warning(
                "missing_upstream_version",
                "Neither an upstream version nor source commit was recorded.",
                "method.upstream_version",
            )
        )
    if method.checkpoint_id is not None and method.checkpoint_sha256 is None:
        warnings.append(
            _warning(
                "missing_checkpoint_hash",
                "Checkpoint identity is present, but its SHA-256 was not recorded.",
                "method.checkpoint_sha256",
            )
        )
    if method.container_image is not None and method.container_digest is None:
        warnings.append(
            _warning(
                "missing_container_digest",
                "Container image is present, but an immutable digest was not recorded.",
                "method.container_digest",
            )
        )
    if not method.command:
        warnings.append(
            _warning(
                "missing_command",
                "The upstream command and arguments were not recorded.",
                "method.command",
            )
        )
    if not method.random_seeds:
        warnings.append(
            _warning(
                "missing_random_seed",
                "No random seed was recorded; the method may or may not have used randomness.",
                "method.random_seeds",
            )
        )
    if manifest.environment.is_empty():
        warnings.append(
            _warning(
                "missing_environment",
                "Execution or import environment metadata was not recorded.",
                "environment",
            )
        )
    if not manifest.licenses:
        warnings.append(
            _warning(
                "missing_license_metadata",
                "No adapter, upstream, model-weight, or dataset license metadata was recorded.",
                "licenses",
            )
        )
    return tuple(warnings)


def _artifact_warning(check: ArtifactCheck) -> ManifestWarning | None:
    if check.status == "verified":
        return None
    codes = {
        "missing": "artifact_missing",
        "mismatch": "artifact_hash_mismatch",
        "external": "artifact_external_not_verified",
        "unsafe_path": "artifact_path_unsafe",
        "unreadable": "artifact_unreadable",
    }
    return _warning(
        codes[check.status],
        check.message,
        f"artifacts.{check.artifact_id}",
    )


def _merge_warnings(
    existing: tuple[ManifestWarning, ...],
    derived: tuple[ManifestWarning, ...],
) -> tuple[ManifestWarning, ...]:
    merged: list[ManifestWarning] = []
    seen: set[tuple[str, str]] = set()
    for warning in (*existing, *derived):
        identity = (warning.code, warning.path)
        if identity not in seen:
            merged.append(warning)
            seen.add(identity)
    return tuple(merged)


def audit_manifest(manifest: RunManifest, *, root: Path) -> ManifestAudit:
    artifact_checks = verify_artifacts(manifest.artifacts, root=root)
    artifact_warnings = tuple(
        warning for check in artifact_checks if (warning := _artifact_warning(check)) is not None
    )
    warnings = _merge_warnings(
        manifest.warnings,
        (*provenance_warnings(manifest), *artifact_warnings),
    )
    audited_manifest = manifest.model_copy(update={"warnings": warnings})
    return ManifestAudit(manifest=audited_manifest, artifact_checks=artifact_checks)
