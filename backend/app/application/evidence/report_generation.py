import re

from molecule_atlas.evidence.audit import audit_manifest
from molecule_atlas.evidence.reports import render_markdown_report
from molecule_atlas.evidence.reports_html import render_html_report

from app.application.capabilities.catalog import GENERATE_EVIDENCE_REPORT
from app.application.capabilities.models import CapabilityContext, require_permissions
from app.application.evidence.contracts import (
    GenerateEvidenceReportInput,
    GenerateEvidenceReportOutput,
)
from app.application.evidence.ports import EvidenceRunRepository
from app.application.evidence.run_summary import EvidenceRunNotFoundError


def _safe_name(run_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", run_id).strip("-.") or "evidence-run"


class GenerateEvidenceReportCapability:
    definition = GENERATE_EVIDENCE_REPORT

    def __init__(self, repository: EvidenceRunRepository) -> None:
        self._repository = repository

    def execute(
        self,
        request: GenerateEvidenceReportInput,
        *,
        context: CapabilityContext,
    ) -> GenerateEvidenceReportOutput:
        require_permissions(self.definition, context)
        stored_run = self._repository.find(request.run_id)
        if stored_run is None:
            raise EvidenceRunNotFoundError(f"Evidence run not found: {request.run_id}")
        audit = audit_manifest(stored_run.manifest, root=stored_run.root)
        if request.report_format == "markdown":
            content = render_markdown_report(
                audit.manifest,
                artifact_checks=audit.artifact_checks,
            )
            media_type = "text/markdown; charset=utf-8"
            suffix = "md"
        else:
            content = render_html_report(
                audit.manifest,
                artifact_checks=audit.artifact_checks,
            )
            media_type = "text/html; charset=utf-8"
            suffix = "html"
        return GenerateEvidenceReportOutput(
            correlation_id=context.correlation_id,
            run_id=request.run_id,
            report_format=request.report_format,
            media_type=media_type,
            filename=f"molecule-atlas-{_safe_name(request.run_id)}.{suffix}",
            content=content,
        )
