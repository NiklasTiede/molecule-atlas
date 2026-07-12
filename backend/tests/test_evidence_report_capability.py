from pathlib import Path

import pytest

from app.application.capabilities.models import ActorContext, CapabilityContext
from app.application.evidence.contracts import (
    EvidenceReportFormat,
    GenerateEvidenceReportInput,
)
from app.application.evidence.report_generation import GenerateEvidenceReportCapability
from app.application.evidence.run_summary import EvidenceRunNotFoundError
from app.infrastructure.evidence.local_repository import LocalEvidenceRunRepository

FIXTURE_ROOT = Path(__file__).parents[2] / "data" / "evidence-fixtures"


def _context() -> CapabilityContext:
    return CapabilityContext(
        actor=ActorContext(
            actor_id="test-suite",
            actor_type="service",
            permissions=("evidence:read",),
        ),
        correlation_id="corr-report",
        causation_id=None,
    )


@pytest.mark.parametrize(
    ("report_format", "media_type", "suffix", "marker"),
    (
        ("markdown", "text/markdown; charset=utf-8", ".md", "# Molecule Atlas Evidence Report"),
        ("html", "text/html; charset=utf-8", ".html", "<!doctype html>"),
    ),
)
def test_generate_evidence_report_returns_deterministic_typed_content(
    report_format: EvidenceReportFormat,
    media_type: str,
    suffix: str,
    marker: str,
) -> None:
    capability = GenerateEvidenceReportCapability(LocalEvidenceRunRepository((FIXTURE_ROOT,)))

    first = capability.execute(
        GenerateEvidenceReportInput(
            run_id="fixture-succeeded",
            report_format=report_format,
        ),
        context=_context(),
    )
    second = capability.execute(
        GenerateEvidenceReportInput(
            run_id="fixture-succeeded",
            report_format=report_format,
        ),
        context=_context(),
    )

    assert first == second
    assert first.capability_id == "generate_evidence_report"
    assert first.media_type == media_type
    assert first.filename.endswith(suffix)
    assert marker in first.content
    assert "fixture-succeeded" in first.content
    assert "not experimental conclusions" in first.content


def test_generate_evidence_report_rejects_unknown_run() -> None:
    capability = GenerateEvidenceReportCapability(LocalEvidenceRunRepository((FIXTURE_ROOT,)))

    with pytest.raises(EvidenceRunNotFoundError, match="unknown-run"):
        capability.execute(
            GenerateEvidenceReportInput(run_id="unknown-run", report_format="html"),
            context=_context(),
        )
