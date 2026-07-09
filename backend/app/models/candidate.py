from typing import Annotated, Literal, Self, TypeIs

from pydantic import Field

from app.models.base import ApiModel

ValidationLevel = Literal["info", "warning", "error"]


class ValidationNote(ApiModel):
    level: ValidationLevel
    message: str = Field(min_length=1)


class DescriptorSet(ApiModel):
    molecular_weight: float = Field(ge=0)
    logp: float
    tpsa: float = Field(ge=0)
    hbond_donors: int = Field(ge=0)
    hbond_acceptors: int = Field(ge=0)
    rotatable_bonds: int = Field(ge=0)
    ring_count: int = Field(ge=0)
    heavy_atom_count: int = Field(ge=0)
    fraction_csp3: float = Field(ge=0, le=1)
    murcko_scaffold: str | None


class TriageFlags(ApiModel):
    lipinski_violations: int = Field(ge=0)
    lipinski_notes: tuple[str, ...]
    veber_violations: int = Field(ge=0)
    veber_notes: tuple[str, ...]


class SimilarityNeighbor(ApiModel):
    candidate_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    similarity: float = Field(ge=0, le=1)


class CandidateInput(ApiModel):
    name: str = Field(min_length=1)
    smiles: str = Field(min_length=1)
    source: str | None = None
    external_id: str | None = None
    score: float | None = None
    target: str | None = None
    notes: str | None = None


class _CandidateBase(ApiModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    smiles: str = Field(min_length=1)
    source: str | None = None
    external_id: str | None = None
    score: float | None = None
    target: str | None = None
    notes: str | None = None
    validation_notes: tuple[ValidationNote, ...]
    neighbors: tuple[SimilarityNeighbor, ...] = ()

    def with_neighbors(self, neighbors: tuple[SimilarityNeighbor, ...]) -> Self:
        return self.model_copy(update={"neighbors": neighbors})


class ValidCandidate(_CandidateBase):
    status: Literal["valid"] = "valid"
    is_valid: Literal[True] = True
    canonical_smiles: str = Field(min_length=1)
    descriptors: DescriptorSet
    triage_flags: TriageFlags
    structure_svg: str = Field(min_length=1)


class InvalidCandidate(_CandidateBase):
    status: Literal["invalid"] = "invalid"
    is_valid: Literal[False] = False
    canonical_smiles: None = None
    descriptors: None = None
    triage_flags: None = None
    structure_svg: None = None


Candidate = Annotated[ValidCandidate | InvalidCandidate, Field(discriminator="status")]


def is_valid_candidate(candidate: Candidate) -> TypeIs[ValidCandidate]:
    return isinstance(candidate, ValidCandidate)


class CandidateSet(ApiModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    candidates: tuple[Candidate, ...]
