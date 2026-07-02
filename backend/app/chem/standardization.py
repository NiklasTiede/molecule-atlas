from dataclasses import dataclass

from rdkit import Chem

from app.models.candidate import ValidationNote


@dataclass(frozen=True)
class ParsedMolecule:
    mol: Chem.Mol | None
    canonical_smiles: str | None
    is_valid: bool
    validation_notes: list[ValidationNote]


def parse_smiles(smiles: str) -> ParsedMolecule:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return ParsedMolecule(
            mol=None,
            canonical_smiles=None,
            is_valid=False,
            validation_notes=[
                ValidationNote(level="error", message=f"Invalid SMILES: {smiles}")
            ],
        )

    canonical = Chem.MolToSmiles(mol, canonical=True)
    return ParsedMolecule(
        mol=mol,
        canonical_smiles=canonical,
        is_valid=True,
        validation_notes=[],
    )
