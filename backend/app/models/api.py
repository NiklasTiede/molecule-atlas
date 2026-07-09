from typing import Literal

from pydantic import Field

from app.models.base import ApiModel


class HealthResponse(ApiModel):
    status: Literal["ok"] = "ok"


class ProjectionPoint(ApiModel):
    candidate_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    x: float
    y: float


class ConformerResponse(ApiModel):
    candidate_id: str = Field(min_length=1)
    mol_block: str = Field(min_length=1)


class ErrorResponse(ApiModel):
    detail: str = Field(min_length=1)
