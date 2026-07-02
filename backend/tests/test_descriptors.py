from rdkit import Chem

from app.chem.descriptors import calculate_descriptors


def test_calculate_descriptors_for_aspirin() -> None:
    mol = Chem.MolFromSmiles("CC(=O)Oc1ccccc1C(=O)O")

    descriptors = calculate_descriptors(mol)

    assert round(descriptors.molecular_weight, 1) == 180.2
    assert round(descriptors.tpsa, 1) == 63.6
    assert descriptors.hbond_donors == 1
    assert descriptors.hbond_acceptors == 3
    assert descriptors.ring_count == 1
    assert descriptors.heavy_atom_count == 13
    assert descriptors.murcko_scaffold == "c1ccccc1"
