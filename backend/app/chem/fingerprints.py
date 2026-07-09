import numpy as np
import numpy.typing as npt
from rdkit import Chem, DataStructs
from rdkit.Chem import rdFingerprintGenerator
from rdkit.DataStructs.cDataStructs import ExplicitBitVect

_MORGAN_GENERATOR = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)

type Fingerprint = ExplicitBitVect
type FingerprintArray = npt.NDArray[np.int_]


def morgan_fingerprint(mol: Chem.Mol) -> Fingerprint:
    return _MORGAN_GENERATOR.GetFingerprint(mol)


def fingerprint_to_array(fingerprint: Fingerprint) -> FingerprintArray:
    vector = np.zeros((fingerprint.GetNumBits(),), dtype=int)
    DataStructs.ConvertToNumpyArray(fingerprint, vector)
    return vector


def tanimoto_similarity(left: Fingerprint, right: Fingerprint) -> float:
    return float(DataStructs.TanimotoSimilarity(left, right))
