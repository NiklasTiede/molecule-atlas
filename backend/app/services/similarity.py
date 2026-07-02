from rdkit import Chem

from app.chem.fingerprints import morgan_fingerprint, tanimoto_similarity
from app.models.candidate import CandidateSet, SimilarityNeighbor


def nearest_neighbors(
    candidate_set: CandidateSet,
    query_candidate_id: str,
    limit: int = 5,
) -> list[SimilarityNeighbor]:
    query = next(
        candidate for candidate in candidate_set.candidates if candidate.id == query_candidate_id
    )
    if not query.is_valid:
        return []

    query_mol = Chem.MolFromSmiles(query.canonical_smiles or query.smiles)
    query_fp = morgan_fingerprint(query_mol)
    neighbors: list[SimilarityNeighbor] = []

    for candidate in candidate_set.candidates:
        if candidate.id == query_candidate_id or not candidate.is_valid:
            continue
        mol = Chem.MolFromSmiles(candidate.canonical_smiles or candidate.smiles)
        similarity = tanimoto_similarity(query_fp, morgan_fingerprint(mol))
        neighbors.append(
            SimilarityNeighbor(
                candidate_id=candidate.id,
                name=candidate.name,
                similarity=similarity,
            )
        )

    return sorted(neighbors, key=lambda neighbor: neighbor.similarity, reverse=True)[:limit]
