from rdkit.DataStructs.cDataStructs import ExplicitBitVect

from . import Mol

class FingerprintGenerator:
    def GetFingerprint(self, mol: Mol) -> ExplicitBitVect: ...

def GetMorganGenerator(radius: int, fpSize: int) -> FingerprintGenerator: ...
