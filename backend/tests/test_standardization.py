from app.chem.standardization import parse_smiles


def test_parse_smiles_returns_canonical_smiles_for_valid_input() -> None:
    result = parse_smiles("CC(=O)Oc1ccccc1C(=O)O")

    assert result.is_valid is True
    assert result.canonical_smiles == "CC(=O)Oc1ccccc1C(=O)O"
    assert result.mol is not None
    assert result.validation_notes == []


def test_parse_smiles_returns_error_note_for_invalid_input() -> None:
    result = parse_smiles("not_a_smiles")

    assert result.is_valid is False
    assert result.canonical_smiles is None
    assert result.mol is None
    assert result.validation_notes[0].level == "error"
    assert "Invalid SMILES" in result.validation_notes[0].message


def test_parse_smiles_does_not_write_rdkit_parse_errors_to_stderr(capfd) -> None:
    parse_smiles("not_a_smiles")

    captured = capfd.readouterr()
    assert "SMILES Parse Error" not in captured.err
