from rdkit import Chem

from app.chem.rendering import mol_to_sdf_block, mol_to_svg


def test_mol_to_svg_returns_svg_markup() -> None:
    mol = Chem.MolFromSmiles("CC(=O)Oc1ccccc1C(=O)O")
    assert mol is not None

    svg = mol_to_svg(mol)

    assert "<svg" in svg
    assert "</svg>" in svg


def test_mol_to_sdf_block_returns_3d_structure_block() -> None:
    mol = Chem.MolFromSmiles("CC(=O)Oc1ccccc1C(=O)O")
    assert mol is not None

    sdf = mol_to_sdf_block(mol)

    assert "M  END" in sdf
    assert "RDKit" in sdf
