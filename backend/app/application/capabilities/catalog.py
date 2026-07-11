from collections.abc import Iterable

from app.application.capabilities.models import CapabilityDefinition

LIST_AVAILABLE_ARTIFACTS = CapabilityDefinition(
    capability_id="list_available_artifacts",
    capability_version="0.1.0",
    title="List available evidence artifacts",
    description="Read a bounded semantic artifact inventory for one imported run.",
    kind="query",
    input_schema="ListAvailableArtifactsInput.0.1.0",
    output_schema="ListAvailableArtifactsOutput.0.1.0",
    required_permissions=("evidence:read",),
    risk_level="low",
    side_effects=(),
    cost_class="small_cpu",
    runtime_class="interactive",
    supports_idempotency=False,
    supports_cancellation=False,
    supports_dry_run=False,
)

VALIDATE_EVIDENCE_ARTIFACTS = CapabilityDefinition(
    capability_id="validate_evidence_artifacts",
    capability_version="0.1.0",
    title="Validate evidence artifacts",
    description=(
        "Recheck artifact integrity and provenance for one imported run without executing plugins."
    ),
    kind="query",
    input_schema="ValidateEvidenceArtifactsInput.0.1.0",
    output_schema="ValidateEvidenceArtifactsOutput.0.1.0",
    required_permissions=("evidence:read",),
    risk_level="low",
    side_effects=(),
    cost_class="small_cpu",
    runtime_class="interactive",
    supports_idempotency=False,
    supports_cancellation=False,
    supports_dry_run=False,
)

IMPORT_EVIDENCE_BUNDLE = CapabilityDefinition(
    capability_id="import_evidence_bundle",
    capability_version="0.1.0",
    title="Import portable evidence bundle",
    description="Validate and retain one bounded portable evidence ZIP for local review.",
    kind="command",
    input_schema="ImportEvidenceBundleInput.0.1.0",
    output_schema="ImportEvidenceBundleOutput.0.1.0",
    required_permissions=("evidence:import",),
    risk_level="medium",
    side_effects=("local_artifact_write", "local_run_create"),
    cost_class="small_cpu",
    runtime_class="interactive",
    supports_idempotency=True,
    supports_cancellation=False,
    supports_dry_run=False,
)

GET_RUN_SUMMARY = CapabilityDefinition(
    capability_id="get_run_summary",
    capability_version="0.1.0",
    title="Get evidence run summary",
    description="Read a bounded scientific and provenance summary for one imported run.",
    kind="query",
    input_schema="GetRunSummaryInput.0.1.0",
    output_schema="GetRunSummaryOutput.0.1.0",
    required_permissions=("evidence:read",),
    risk_level="low",
    side_effects=(),
    cost_class="small_cpu",
    runtime_class="interactive",
    supports_idempotency=False,
    supports_cancellation=False,
    supports_dry_run=False,
)


class CapabilityCatalog:
    """Small explicit catalog; internal helpers are not capabilities by default."""

    def __init__(self, definitions: Iterable[CapabilityDefinition]) -> None:
        by_identity: dict[tuple[str, str], CapabilityDefinition] = {}
        for definition in definitions:
            identity = (definition.capability_id, definition.capability_version)
            if identity in by_identity:
                raise ValueError(
                    "duplicate capability definition: "
                    f"{definition.capability_id}@{definition.capability_version}"
                )
            by_identity[identity] = definition
        self._by_identity = by_identity

    @property
    def definitions(self) -> tuple[CapabilityDefinition, ...]:
        return tuple(self._by_identity.values())

    def get(self, capability_id: str, capability_version: str) -> CapabilityDefinition:
        return self._by_identity[(capability_id, capability_version)]


CAPABILITY_CATALOG = CapabilityCatalog(
    (
        IMPORT_EVIDENCE_BUNDLE,
        GET_RUN_SUMMARY,
        LIST_AVAILABLE_ARTIFACTS,
        VALIDATE_EVIDENCE_ARTIFACTS,
    )
)
