from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.models.api import ConformerResponse, ErrorResponse, ProjectionPoint
from app.models.candidate import Candidate, CandidateSet, SimilarityNeighbor, is_valid_candidate
from app.services.candidate_repository import load_candidate_set
from app.services.conformers import (
    ConformerUnavailableError,
    InvalidCandidateForConformerError,
    StoredCandidateDataError,
    generate_candidate_conformer,
)
from app.services.projection import project_candidate_set
from app.services.similarity import CandidateNotFoundError, find_candidate, nearest_neighbors

router = APIRouter(prefix="/api/candidate-sets", tags=["candidate-sets"])

DATA_PATH = Path(__file__).resolve().parents[3] / "data" / "demo_candidates.csv"


def _demo_candidate_set() -> CandidateSet:
    candidate_set = load_candidate_set(DATA_PATH)
    enriched_candidates: list[Candidate] = []
    for candidate in candidate_set.candidates:
        if is_valid_candidate(candidate):
            neighbors = nearest_neighbors(candidate_set, candidate.id, limit=5)
            enriched_candidates.append(candidate.with_neighbors(neighbors))
        else:
            enriched_candidates.append(candidate)
    return CandidateSet(
        id=candidate_set.id,
        name=candidate_set.name,
        candidates=tuple(enriched_candidates),
    )


@router.get("/demo")
def get_demo_candidate_set() -> CandidateSet:
    return _demo_candidate_set()


@router.get(
    "/demo/candidates/{candidate_id}/neighbors",
    responses={404: {"model": ErrorResponse, "description": "Candidate not found"}},
)
def get_candidate_neighbors(candidate_id: str) -> tuple[SimilarityNeighbor, ...]:
    candidate_set = _demo_candidate_set()
    if find_candidate(candidate_set, candidate_id) is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return nearest_neighbors(candidate_set, candidate_id, limit=5)


@router.get("/demo/projection")
def get_demo_projection() -> tuple[ProjectionPoint, ...]:
    return project_candidate_set(_demo_candidate_set())


@router.get(
    "/demo/candidates/{candidate_id}/conformer",
    responses={
        404: {"model": ErrorResponse, "description": "Candidate not found"},
        422: {"model": ErrorResponse, "description": "Conformer cannot be generated"},
        500: {"model": ErrorResponse, "description": "Stored candidate data is inconsistent"},
    },
)
def get_candidate_conformer(candidate_id: str) -> ConformerResponse:
    try:
        return generate_candidate_conformer(_demo_candidate_set(), candidate_id)
    except CandidateNotFoundError as error:
        raise HTTPException(status_code=404, detail="Candidate not found") from error
    except InvalidCandidateForConformerError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except ConformerUnavailableError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except StoredCandidateDataError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
