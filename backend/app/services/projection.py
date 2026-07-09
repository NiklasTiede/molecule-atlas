from sklearn.decomposition import PCA

from app.chem.fingerprints import FingerprintArray, fingerprint_to_array, morgan_fingerprint
from app.chem.standardization import InvalidParsedMolecule, parse_smiles
from app.models.api import ProjectionPoint
from app.models.candidate import CandidateSet, ValidCandidate, is_valid_candidate


def _valid_candidates(candidate_set: CandidateSet) -> tuple[ValidCandidate, ...]:
    return tuple(filter(is_valid_candidate, candidate_set.candidates))


def project_candidate_set(candidate_set: CandidateSet) -> tuple[ProjectionPoint, ...]:
    valid_candidates = _valid_candidates(candidate_set)
    if len(valid_candidates) < 2:
        return ()

    vectors: list[FingerprintArray] = []
    for candidate in valid_candidates:
        parsed = parse_smiles(candidate.canonical_smiles)
        if isinstance(parsed, InvalidParsedMolecule):
            raise ValueError(f"Stored canonical SMILES is invalid: {candidate.id}")
        fingerprint = morgan_fingerprint(parsed.mol)
        vectors.append(fingerprint_to_array(fingerprint))

    coordinates = PCA(n_components=2, random_state=61453).fit_transform(vectors)
    return tuple(
        ProjectionPoint(
            candidate_id=candidate.id,
            name=candidate.name,
            x=float(coordinates[index][0]),
            y=float(coordinates[index][1]),
        )
        for index, candidate in enumerate(valid_candidates)
    )
