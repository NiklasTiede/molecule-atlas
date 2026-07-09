from rdkit import Chem

from app.chem.fingerprints import morgan_fingerprint, tanimoto_similarity


def test_tanimoto_similarity_self_is_one() -> None:
    aspirin = Chem.MolFromSmiles("CC(=O)Oc1ccccc1C(=O)O")
    assert aspirin is not None

    fingerprint = morgan_fingerprint(aspirin)

    assert tanimoto_similarity(fingerprint, fingerprint) == 1.0


def test_related_aromatic_molecules_are_more_similar_than_caffeine() -> None:
    aspirin_mol = Chem.MolFromSmiles("CC(=O)Oc1ccccc1C(=O)O")
    acetaminophen_mol = Chem.MolFromSmiles("CC(=O)Nc1ccc(O)cc1")
    caffeine_mol = Chem.MolFromSmiles("Cn1cnc2c1c(=O)n(C)c(=O)n2C")
    assert aspirin_mol is not None
    assert acetaminophen_mol is not None
    assert caffeine_mol is not None

    aspirin = morgan_fingerprint(aspirin_mol)
    acetaminophen = morgan_fingerprint(acetaminophen_mol)
    caffeine = morgan_fingerprint(caffeine_mol)

    assert tanimoto_similarity(aspirin, acetaminophen) > tanimoto_similarity(aspirin, caffeine)
