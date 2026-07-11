from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Response

from app.application.capabilities.models import ActorContext, CapabilityContext
from app.application.evidence.contracts import GetRunSummaryInput, GetRunSummaryOutput
from app.application.evidence.run_summary import (
    EvidenceRunNotFoundError,
    GetRunSummaryCapability,
)
from app.infrastructure.evidence.local_repository import LocalEvidenceRunRepository
from app.models.api import ErrorResponse

router = APIRouter(prefix="/api/evidence", tags=["evidence"])

DATA_ROOT = Path(__file__).resolve().parents[3] / "data" / "evidence-fixtures"
_RUN_SUMMARY_CAPABILITY = GetRunSummaryCapability(LocalEvidenceRunRepository((DATA_ROOT,)))

CorrelationHeader = Annotated[
    str | None,
    Header(
        alias="X-Correlation-ID",
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$",
    ),
]


def get_run_summary_capability() -> GetRunSummaryCapability:
    return _RUN_SUMMARY_CAPABILITY


def _local_context(correlation_id: str | None) -> CapabilityContext:
    return CapabilityContext(
        actor=ActorContext(
            actor_id="local-anonymous-browser",
            actor_type="human",
            permissions=("evidence:read",),
        ),
        correlation_id=correlation_id or f"corr-{uuid4().hex}",
        causation_id=None,
    )


@router.get(
    "/runs/{run_id}",
    operation_id="get_run_summary",
    response_model=GetRunSummaryOutput,
    responses={404: {"model": ErrorResponse, "description": "Evidence run not found"}},
)
def get_run_summary(
    run_id: str,
    response: Response,
    capability: Annotated[GetRunSummaryCapability, Depends(get_run_summary_capability)],
    x_correlation_id: CorrelationHeader = None,
) -> GetRunSummaryOutput:
    context = _local_context(x_correlation_id)
    try:
        result = capability.execute(GetRunSummaryInput(run_id=run_id), context=context)
    except EvidenceRunNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    response.headers["X-Correlation-ID"] = result.correlation_id
    return result
