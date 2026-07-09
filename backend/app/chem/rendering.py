from rdkit import Chem
from rdkit.Chem import AllChem, Draw


class ConformerGenerationError(RuntimeError):
    """Raised when RDKit cannot generate a conformer for a valid molecule."""


def mol_to_svg(mol: Chem.Mol, width: int = 280, height: int = 200) -> str:
    drawer = Draw.MolDraw2DSVG(width, height)
    drawer.DrawMolecule(mol)
    drawer.FinishDrawing()
    return drawer.GetDrawingText()


def mol_to_sdf_block(mol: Chem.Mol) -> str:
    mol_with_h = Chem.AddHs(mol)
    embedded = AllChem.EmbedMolecule(mol_with_h, randomSeed=61453)
    if embedded != 0:
        raise ConformerGenerationError("Could not generate a 3D conformer for this molecule.")
    AllChem.UFFOptimizeMolecule(mol_with_h, maxIters=200)
    return Chem.MolToMolBlock(mol_with_h)
