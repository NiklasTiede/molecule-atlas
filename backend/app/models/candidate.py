from pydantic import BaseModel, Field


class ValidationNote(BaseModel):
    level: str = Field(pattern="^(info|warning|error)$")
    message: str


class DescriptorSet(BaseModel):
    molecular_weight: float
    logp: float
    tpsa: float
    hbond_donors: int
    hbond_acceptors: int
    rotatable_bonds: int
    ring_count: int
    heavy_atom_count: int
    fraction_csp3: float
    murcko_scaffold: str | None


class TriageFlags(BaseModel):
    lipinski_violations: int
    lipinski_notes: list[str]
    veber_violations: int
    veber_notes: list[str]


class SimilarityNeighbor(BaseModel):
    candidate_id: str
    name: str
    similarity: float


class CandidateInput(BaseModel):
    name: str
    smiles: str
    source: str | None = None
    external_id: str | None = None
    score: float | None = None
    target: str | None = None
    notes: str | None = None


class Candidate(BaseModel):
    id: str
    name: str
    smiles: str
    canonical_smiles: str | None
    source: str | None = None
    external_id: str | None = None
    score: float | None = None
    target: str | None = None
    notes: str | None = None
    is_valid: bool
    validation_notes: list[ValidationNote]
    descriptors: DescriptorSet | None
    triage_flags: TriageFlags | None
    structure_svg: str | None = None
    neighbors: list[SimilarityNeighbor] = []


class CandidateSet(BaseModel):
    id: str
    name: str
    candidates: list[Candidate]
