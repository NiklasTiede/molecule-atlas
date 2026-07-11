import pytest
from pydantic import ValidationError

from app.application.capabilities.catalog import (
    GET_RUN_SUMMARY,
    IMPORT_EVIDENCE_BUNDLE,
    CapabilityCatalog,
)
from app.application.capabilities.models import (
    ActorContext,
    CapabilityContext,
    CapabilityPermissionError,
    require_permissions,
)


def test_get_run_summary_has_stable_complete_metadata() -> None:
    assert GET_RUN_SUMMARY.model_dump(mode="json") == {
        "capability_id": "get_run_summary",
        "capability_version": "0.1.0",
        "title": "Get evidence run summary",
        "description": "Read a bounded scientific and provenance summary for one imported run.",
        "kind": "query",
        "input_schema": "GetRunSummaryInput.0.1.0",
        "output_schema": "GetRunSummaryOutput.0.1.0",
        "required_permissions": ["evidence:read"],
        "risk_level": "low",
        "side_effects": [],
        "cost_class": "small_cpu",
        "runtime_class": "interactive",
        "supports_idempotency": False,
        "supports_cancellation": False,
        "supports_dry_run": False,
    }


def test_import_evidence_bundle_has_stable_complete_metadata() -> None:
    assert IMPORT_EVIDENCE_BUNDLE.model_dump(mode="json") == {
        "capability_id": "import_evidence_bundle",
        "capability_version": "0.1.0",
        "title": "Import portable evidence bundle",
        "description": "Validate and retain one bounded portable evidence ZIP for local review.",
        "kind": "command",
        "input_schema": "ImportEvidenceBundleInput.0.1.0",
        "output_schema": "ImportEvidenceBundleOutput.0.1.0",
        "required_permissions": ["evidence:import"],
        "risk_level": "medium",
        "side_effects": ["local_artifact_write", "local_run_create"],
        "cost_class": "small_cpu",
        "runtime_class": "interactive",
        "supports_idempotency": True,
        "supports_cancellation": False,
        "supports_dry_run": False,
    }


def test_capability_catalog_rejects_duplicate_ids_and_versions() -> None:
    with pytest.raises(ValueError, match="duplicate capability definition"):
        CapabilityCatalog((GET_RUN_SUMMARY, GET_RUN_SUMMARY))


def test_capability_permission_is_enforced_inside_boundary() -> None:
    context = CapabilityContext(
        actor=ActorContext(actor_id="local-browser", actor_type="human", permissions=()),
        correlation_id="corr-test-1",
        causation_id=None,
    )

    with pytest.raises(CapabilityPermissionError, match="evidence:read"):
        require_permissions(GET_RUN_SUMMARY, context)


def test_capability_context_rejects_unstructured_correlation_id() -> None:
    with pytest.raises(ValidationError):
        CapabilityContext(
            actor=ActorContext(
                actor_id="local-browser",
                actor_type="human",
                permissions=("evidence:read",),
            ),
            correlation_id="spaces are not allowed",
            causation_id=None,
        )
