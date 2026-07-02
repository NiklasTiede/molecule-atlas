from rdkit import Chem, DataStructs
from rdkit.Chem import rdFingerprintGenerator
from rdkit.DataStructs.cDataStructs import ExplicitBitVect

_MORGAN_GENERATOR = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)


def morgan_fingerprint(mol: Chem.Mol) -> ExplicitBitVect:
    return _MORGAN_GENERATOR.GetFingerprint(mol)


def tanimoto_similarity(left: ExplicitBitVect, right: ExplicitBitVect) -> float:
    return float(DataStructs.TanimotoSimilarity(left, right))
