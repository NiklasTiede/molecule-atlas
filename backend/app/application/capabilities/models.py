from typing import Literal

from pydantic import Field

from app.models.base import ApiModel

CapabilityKind = Literal["query", "command", "job", "proposal"]
ActorType = Literal["human", "service", "plugin", "agent"]
RiskLevel = Literal["low", "medium", "high", "critical"]
CostClass = Literal["negligible", "small_cpu", "large_cpu", "gpu", "external_paid"]
RuntimeClass = Literal["instant", "interactive", "batch", "long_running"]

_IDENTIFIER_PATTERN = r"^[a-z][a-z0-9]*(?:[_:-][a-z0-9]+)*$"
_SEMVER_PATTERN = (
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$"
)
_TRACE_ID_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$"


class CapabilityDefinition(ApiModel):
    """Stable machine-readable policy and contract metadata for one operation."""

    capability_id: str = Field(pattern=_IDENTIFIER_PATTERN)
    capability_version: str = Field(pattern=_SEMVER_PATTERN)
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    kind: CapabilityKind
    input_schema: str = Field(min_length=1)
    output_schema: str = Field(min_length=1)
    required_permissions: tuple[str, ...]
    risk_level: RiskLevel
    side_effects: tuple[str, ...]
    cost_class: CostClass
    runtime_class: RuntimeClass
    supports_idempotency: bool
    supports_cancellation: bool
    supports_dry_run: bool


class ActorContext(ApiModel):
    actor_id: str = Field(min_length=1)
    actor_type: ActorType
    permissions: tuple[str, ...]


class CapabilityContext(ApiModel):
    """Ephemeral invocation identity; persistence is deliberately deferred to Milestone 5."""

    actor: ActorContext
    correlation_id: str = Field(pattern=_TRACE_ID_PATTERN)
    causation_id: str | None = Field(default=None, pattern=_TRACE_ID_PATTERN)


class CapabilityPermissionError(PermissionError):
    """Raised when the invoking actor lacks a declared capability permission."""


def require_permissions(
    definition: CapabilityDefinition,
    context: CapabilityContext,
) -> None:
    missing = tuple(
        permission
        for permission in definition.required_permissions
        if permission not in context.actor.permissions
    )
    if missing:
        raise CapabilityPermissionError(
            f"Actor {context.actor.actor_id} lacks required permissions: {', '.join(missing)}"
        )
