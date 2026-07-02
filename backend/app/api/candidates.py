from pathlib import Path

from fastapi import APIRouter, HTTPException
from rdkit import Chem

from app.chem.rendering import mol_to_sdf_block
from app.models.candidate import CandidateSet, SimilarityNeighbor
from app.services.candidate_repository import load_candidate_set
from app.services.projection import project_candidate_set
from app.services.similarity import nearest_neighbors

router = APIRouter(prefix="/api/candidate-sets", tags=["candidate-sets"])

DATA_PATH = Path(__file__).resolve().parents[3] / "data" / "demo_candidates.csv"


def _demo_candidate_set() -> CandidateSet:
    candidate_set = load_candidate_set(DATA_PATH)
    for candidate in candidate_set.candidates:
        if candidate.is_valid:
            candidate.neighbors = nearest_neighbors(candidate_set, candidate.id, limit=5)
    return candidate_set


@router.get("/demo")
def get_demo_candidate_set() -> CandidateSet:
    return _demo_candidate_set()


@router.get("/demo/candidates/{candidate_id}/neighbors")
def get_candidate_neighbors(candidate_id: str) -> list[SimilarityNeighbor]:
    candidate_set = _demo_candidate_set()
    if not any(candidate.id == candidate_id for candidate in candidate_set.candidates):
        raise HTTPException(status_code=404, detail="Candidate not found")
    return nearest_neighbors(candidate_set, candidate_id, limit=5)


@router.get("/demo/projection")
def get_demo_projection() -> list[dict[str, float | str]]:
    return project_candidate_set(_demo_candidate_set())


@router.get("/demo/candidates/{candidate_id}/conformer")
def get_candidate_conformer(candidate_id: str) -> dict[str, str]:
    candidate_set = _demo_candidate_set()
    candidate = next(
        (candidate for candidate in candidate_set.candidates if candidate.id == candidate_id),
        None,
    )
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    if not candidate.is_valid:
        raise HTTPException(
            status_code=422,
            detail="Cannot generate conformer for invalid molecule",
        )

    mol = Chem.MolFromSmiles(candidate.canonical_smiles or candidate.smiles)
    return {"candidate_id": candidate.id, "mol_block": mol_to_sdf_block(mol)}
