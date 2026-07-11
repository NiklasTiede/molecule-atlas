from molecule_atlas.evidence.artifacts import ArtifactCheck
from molecule_atlas.evidence.audit import audit_manifest
from molecule_atlas.evidence.models import Artifact
from molecule_atlas.evidence.semantic_artifacts import SemanticArtifact

from app.application.capabilities.catalog import (
    LIST_AVAILABLE_ARTIFACTS,
    VALIDATE_EVIDENCE_ARTIFACTS,
)
from app.application.capabilities.models import CapabilityContext, require_permissions
from app.application.evidence.contracts import (
    ArtifactCheckCounts,
    AvailableArtifact,
    ListAvailableArtifactsInput,
    ListAvailableArtifactsOutput,
    SemanticArtifactSummary,
    ValidateEvidenceArtifactsInput,
    ValidateEvidenceArtifactsOutput,
)
from app.application.evidence.ports import EvidenceRunRepository, StoredEvidenceRun
from app.application.evidence.run_summary import EvidenceRunNotFoundError


def _stored_run(repository: EvidenceRunRepository, run_id: str) -> StoredEvidenceRun:
    stored_run = repository.find(run_id)
    if stored_run is None:
        raise EvidenceRunNotFoundError(f"Evidence run not found: {run_id}")
    return stored_run


def _semantic_summary(semantic: SemanticArtifact | None) -> SemanticArtifactSummary | None:
    if semantic is None:
        return None
    return SemanticArtifactSummary(
        logical_name=semantic.logical_name,
        artifact_type=semantic.artifact_type,
        schema_version=semantic.schema_version,
        semantic_role=semantic.semantic_role,
        derived_from_artifact_ids=semantic.derived_from_artifact_ids,
        domain_metadata=semantic.domain_metadata,
        preview_metadata=semantic.preview_metadata,
    )


def _available_artifact(
    artifact: Artifact,
    *,
    check: ArtifactCheck,
    semantic: SemanticArtifact | None,
) -> AvailableArtifact:
    return AvailableArtifact(
        artifact_id=artifact.id,
        role=artifact.role,
        path_or_uri=artifact.path_or_uri,
        original_name=artifact.original_name,
        media_type=artifact.media_type,
        content_digest=f"sha256:{artifact.sha256}",
        size_bytes=artifact.size_bytes,
        created_by_stage=artifact.created_by_stage,
        source_metadata=artifact.metadata,
        verification=check,
        semantic=_semantic_summary(semantic),
    )


def _check_counts(checks: tuple[ArtifactCheck, ...]) -> ArtifactCheckCounts:
    statuses = tuple(check.status for check in checks)
    return ArtifactCheckCounts(
        verified_count=statuses.count("verified"),
        missing_count=statuses.count("missing"),
        mismatch_count=statuses.count("mismatch"),
        external_count=statuses.count("external"),
        unsafe_path_count=statuses.count("unsafe_path"),
        unreadable_count=statuses.count("unreadable"),
    )


class ListAvailableArtifactsCapability:
    definition = LIST_AVAILABLE_ARTIFACTS

    def __init__(self, repository: EvidenceRunRepository) -> None:
        self._repository = repository

    def execute(
        self,
        request: ListAvailableArtifactsInput,
        *,
        context: CapabilityContext,
    ) -> ListAvailableArtifactsOutput:
        require_permissions(self.definition, context)
        stored_run = _stored_run(self._repository, request.run_id)
        audit = audit_manifest(stored_run.manifest, root=stored_run.root)
        checks = {check.artifact_id: check for check in audit.artifact_checks}
        semantic_by_id = (
            {artifact.artifact_id: artifact for artifact in stored_run.artifact_manifest.artifacts}
            if stored_run.artifact_manifest is not None
            else {}
        )
        selected = stored_run.manifest.artifacts[request.offset : request.offset + request.limit]
        artifacts = tuple(
            _available_artifact(
                artifact,
                check=checks[artifact.id],
                semantic=semantic_by_id.get(artifact.id),
            )
            for artifact in selected
        )
        return ListAvailableArtifactsOutput(
            correlation_id=context.correlation_id,
            run_id=request.run_id,
            total=len(stored_run.manifest.artifacts),
            offset=request.offset,
            limit=request.limit,
            artifacts=artifacts,
        )


class ValidateEvidenceArtifactsCapability:
    definition = VALIDATE_EVIDENCE_ARTIFACTS

    def __init__(self, repository: EvidenceRunRepository) -> None:
        self._repository = repository

    def execute(
        self,
        request: ValidateEvidenceArtifactsInput,
        *,
        context: CapabilityContext,
    ) -> ValidateEvidenceArtifactsOutput:
        require_permissions(self.definition, context)
        stored_run = _stored_run(self._repository, request.run_id)
        audit = audit_manifest(stored_run.manifest, root=stored_run.root)
        return ValidateEvidenceArtifactsOutput(
            correlation_id=context.correlation_id,
            run_id=request.run_id,
            counts=_check_counts(audit.artifact_checks),
            artifact_checks=audit.artifact_checks,
            warnings=audit.manifest.warnings,
        )
