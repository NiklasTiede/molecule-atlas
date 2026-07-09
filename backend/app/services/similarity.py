from app.chem.fingerprints import Fingerprint, morgan_fingerprint, tanimoto_similarity
from app.chem.standardization import InvalidParsedMolecule, parse_smiles
from app.models.candidate import (
    Candidate,
    CandidateSet,
    SimilarityNeighbor,
    ValidCandidate,
    is_valid_candidate,
)


class CandidateNotFoundError(LookupError):
    pass


def find_candidate(candidate_set: CandidateSet, candidate_id: str) -> Candidate | None:
    return next(
        (candidate for candidate in candidate_set.candidates if candidate.id == candidate_id),
        None,
    )


def _fingerprint(candidate: ValidCandidate) -> Fingerprint:
    parsed = parse_smiles(candidate.canonical_smiles)
    if isinstance(parsed, InvalidParsedMolecule):
        raise ValueError(f"Stored canonical SMILES is invalid: {candidate.id}")
    return morgan_fingerprint(parsed.mol)


def nearest_neighbors(
    candidate_set: CandidateSet,
    query_candidate_id: str,
    limit: int = 5,
) -> tuple[SimilarityNeighbor, ...]:
    if limit < 0:
        raise ValueError("limit must be non-negative")

    query = find_candidate(candidate_set, query_candidate_id)
    if query is None:
        raise CandidateNotFoundError(query_candidate_id)
    if not is_valid_candidate(query):
        return ()

    query_fp = _fingerprint(query)
    neighbors: list[SimilarityNeighbor] = []

    for candidate in candidate_set.candidates:
        if candidate.id == query_candidate_id or not is_valid_candidate(candidate):
            continue
        similarity = tanimoto_similarity(query_fp, _fingerprint(candidate))
        neighbors.append(
            SimilarityNeighbor(
                candidate_id=candidate.id,
                name=candidate.name,
                similarity=similarity,
            )
        )

    sorted_neighbors = sorted(
        neighbors,
        key=lambda neighbor: neighbor.similarity,
        reverse=True,
    )
    return tuple(sorted_neighbors[:limit])
