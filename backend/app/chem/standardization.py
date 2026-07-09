from dataclasses import dataclass
from typing import Literal

from rdkit import Chem, rdBase

from app.models.candidate import ValidationNote


@dataclass(frozen=True, slots=True)
class ValidParsedMolecule:
    mol: Chem.Mol
    canonical_smiles: str
    validation_notes: tuple[ValidationNote, ...] = ()
    is_valid: Literal[True] = True


@dataclass(frozen=True, slots=True)
class InvalidParsedMolecule:
    validation_notes: tuple[ValidationNote, ...]
    mol: None = None
    canonical_smiles: None = None
    is_valid: Literal[False] = False


ParsedMolecule = ValidParsedMolecule | InvalidParsedMolecule


def parse_smiles(smiles: str) -> ParsedMolecule:
    with rdBase.BlockLogs():
        mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return InvalidParsedMolecule(
            validation_notes=(ValidationNote(level="error", message=f"Invalid SMILES: {smiles}"),)
        )

    canonical = Chem.MolToSmiles(mol, canonical=True)
    return ValidParsedMolecule(mol=mol, canonical_smiles=canonical)
