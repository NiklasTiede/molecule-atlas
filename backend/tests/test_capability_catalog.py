import pytest
from pydantic import ValidationError

from app.application.capabilities.catalog import (
    GET_RUN_SUMMARY,
    IMPORT_EVIDENCE_BUNDLE,
    LIST_AVAILABLE_ARTIFACTS,
    VALIDATE_EVIDENCE_ARTIFACTS,
    CapabilityCatalog,
)
from app.application.capabilities.models import (
    ActorContext,
    CapabilityContext,
    CapabilityDefinition,
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


@pytest.mark.parametrize(
    ("definition", "expected"),
    (
        (
            LIST_AVAILABLE_ARTIFACTS,
            {
                "capability_id": "list_available_artifacts",
                "capability_version": "0.1.0",
                "title": "List available evidence artifacts",
                "description": "Read a bounded semantic artifact inventory for one imported run.",
                "kind": "query",
                "input_schema": "ListAvailableArtifactsInput.0.1.0",
                "output_schema": "ListAvailableArtifactsOutput.0.1.0",
                "required_permissions": ["evidence:read"],
                "risk_level": "low",
                "side_effects": [],
                "cost_class": "small_cpu",
                "runtime_class": "interactive",
                "supports_idempotency": False,
                "supports_cancellation": False,
                "supports_dry_run": False,
            },
        ),
        (
            VALIDATE_EVIDENCE_ARTIFACTS,
            {
                "capability_id": "validate_evidence_artifacts",
                "capability_version": "0.1.0",
                "title": "Validate evidence artifacts",
                "description": (
                    "Recheck artifact integrity and provenance for one imported run without "
                    "executing plugins."
                ),
                "kind": "query",
                "input_schema": "ValidateEvidenceArtifactsInput.0.1.0",
                "output_schema": "ValidateEvidenceArtifactsOutput.0.1.0",
                "required_permissions": ["evidence:read"],
                "risk_level": "low",
                "side_effects": [],
                "cost_class": "small_cpu",
                "runtime_class": "interactive",
                "supports_idempotency": False,
                "supports_cancellation": False,
                "supports_dry_run": False,
            },
        ),
    ),
)
def test_artifact_capabilities_have_stable_complete_metadata(
    definition: CapabilityDefinition,
    expected: dict[str, object],
) -> None:
    assert definition.model_dump(mode="json") == expected


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
