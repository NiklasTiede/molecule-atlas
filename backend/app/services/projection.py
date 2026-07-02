import numpy as np
from rdkit import Chem, DataStructs
from sklearn.decomposition import PCA

from app.chem.fingerprints import morgan_fingerprint
from app.models.candidate import CandidateSet


def project_candidate_set(candidate_set: CandidateSet) -> list[dict[str, float | str]]:
    valid_candidates = [candidate for candidate in candidate_set.candidates if candidate.is_valid]
    if len(valid_candidates) < 2:
        return []

    vectors: list[np.ndarray] = []
    for candidate in valid_candidates:
        mol = Chem.MolFromSmiles(candidate.canonical_smiles or candidate.smiles)
        fingerprint = morgan_fingerprint(mol)
        vector = np.zeros((fingerprint.GetNumBits(),), dtype=int)
        DataStructs.ConvertToNumpyArray(fingerprint, vector)
        vectors.append(vector)

    coordinates = PCA(n_components=2, random_state=61453).fit_transform(vectors)
    return [
        {
            "candidate_id": candidate.id,
            "name": candidate.name,
            "x": float(coordinates[index][0]),
            "y": float(coordinates[index][1]),
        }
        for index, candidate in enumerate(valid_candidates)
    ]
