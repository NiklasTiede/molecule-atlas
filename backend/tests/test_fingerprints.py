from rdkit import Chem

from app.chem.fingerprints import morgan_fingerprint, tanimoto_similarity


def test_tanimoto_similarity_self_is_one() -> None:
    aspirin = Chem.MolFromSmiles("CC(=O)Oc1ccccc1C(=O)O")

    fingerprint = morgan_fingerprint(aspirin)

    assert tanimoto_similarity(fingerprint, fingerprint) == 1.0


def test_related_aromatic_molecules_are_more_similar_than_caffeine() -> None:
    aspirin = morgan_fingerprint(Chem.MolFromSmiles("CC(=O)Oc1ccccc1C(=O)O"))
    acetaminophen = morgan_fingerprint(Chem.MolFromSmiles("CC(=O)Nc1ccc(O)cc1"))
    caffeine = morgan_fingerprint(Chem.MolFromSmiles("Cn1cnc2c1c(=O)n(C)c(=O)n2C"))

    assert tanimoto_similarity(aspirin, acetaminophen) > tanimoto_similarity(aspirin, caffeine)
