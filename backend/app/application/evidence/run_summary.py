from molecule_atlas.evidence.audit import audit_manifest
from molecule_atlas.evidence.models import RunManifest

from app.application.capabilities.catalog import GET_RUN_SUMMARY
from app.application.capabilities.models import CapabilityContext, require_permissions
from app.application.evidence.contracts import (
    GetRunSummaryInput,
    GetRunSummaryOutput,
    MethodSummary,
    RunSummary,
    ValidationCounts,
)
from app.application.evidence.ports import EvidenceRunRepository, StoredEvidenceRun


class EvidenceRunNotFoundError(LookupError):
    """Raised when a bounded evidence query cannot find its requested run."""


def _validation_counts(manifest: RunManifest) -> ValidationCounts:
    statuses = tuple(result.status for result in manifest.validation_results)
    return ValidationCounts(
        pass_count=statuses.count("pass"),
        fail_count=statuses.count("fail"),
        warning_count=statuses.count("warning"),
        unavailable_count=statuses.count("unavailable"),
        error_count=statuses.count("error"),
    )


def _summary(manifest: RunManifest) -> RunSummary:
    method = manifest.method
    return RunSummary(
        run_id=manifest.run.id,
        schema_version=manifest.schema_version,
        state=manifest.run.state,
        started_at=manifest.run.started_at,
        finished_at=manifest.run.finished_at,
        expected_outputs=manifest.run.expected_outputs,
        missing_outputs=manifest.run.missing_outputs,
        failure=manifest.run.failure,
        method=MethodSummary(
            method_id=method.id,
            adapter_id=method.adapter_id,
            adapter_version=method.adapter_version,
            upstream_tool=method.upstream_tool,
            upstream_version=method.upstream_version,
            source_commit=method.source_commit,
            checkpoint_id=method.checkpoint_id,
            checkpoint_sha256=method.checkpoint_sha256,
            container_image=method.container_image,
            container_digest=method.container_digest,
            command=method.command,
            random_seeds=method.random_seeds,
        ),
        artifact_count=len(manifest.artifacts),
        prediction_count=len(manifest.predictions),
        validation_counts=_validation_counts(manifest),
        warnings=manifest.warnings,
    )


def build_run_summary(stored_run: StoredEvidenceRun) -> RunSummary:
    """Audit and project a stored portable run without mutating its source manifest."""

    audit = audit_manifest(stored_run.manifest, root=stored_run.root)
    return _summary(audit.manifest)


class GetRunSummaryCapability:
    definition = GET_RUN_SUMMARY

    def __init__(self, repository: EvidenceRunRepository) -> None:
        self._repository = repository

    def execute(
        self,
        request: GetRunSummaryInput,
        *,
        context: CapabilityContext,
    ) -> GetRunSummaryOutput:
        require_permissions(self.definition, context)
        stored_run = self._repository.find(request.run_id)
        if stored_run is None:
            raise EvidenceRunNotFoundError(f"Evidence run not found: {request.run_id}")
        return GetRunSummaryOutput(
            correlation_id=context.correlation_id,
            run=build_run_summary(stored_run),
        )
