from pathlib import Path

import pytest

from app.adapters.candidate_csv import CandidateCsvError
from app.services.candidate_repository import load_candidate_set


def test_load_candidate_set_processes_valid_and_invalid_rows() -> None:
    path = Path("tests/fixtures/tiny_candidates.csv")

    candidate_set = load_candidate_set(path, candidate_set_id="test", name="Test Set")

    assert candidate_set.id == "test"
    assert len(candidate_set.candidates) == 6
    aspirin = candidate_set.candidates[0]
    invalid = candidate_set.candidates[-1]
    assert aspirin.is_valid is True
    assert aspirin.descriptors is not None
    assert aspirin.structure_svg is not None
    assert invalid.is_valid is False
    assert invalid.descriptors is None
    assert invalid.validation_notes[0].level == "error"


def test_load_candidate_set_rejects_non_numeric_score(tmp_path: Path) -> None:
    path = tmp_path / "invalid_score.csv"
    path.write_text("name,smiles,score\nAspirin,CCO,not-a-number\n", encoding="utf-8")

    with pytest.raises(CandidateCsvError, match="score must be a number"):
        load_candidate_set(path)


def test_load_candidate_set_rejects_missing_required_columns(tmp_path: Path) -> None:
    path = tmp_path / "missing_smiles.csv"
    path.write_text("name,score\nAspirin,1.0\n", encoding="utf-8")

    with pytest.raises(CandidateCsvError, match="Missing required CSV columns: smiles"):
        load_candidate_set(path)


def test_load_candidate_set_rejects_non_finite_score(tmp_path: Path) -> None:
    path = tmp_path / "non_finite_score.csv"
    path.write_text("name,smiles,score\nAspirin,CCO,nan\n", encoding="utf-8")

    with pytest.raises(CandidateCsvError, match="score must be finite"):
        load_candidate_set(path)


def test_load_candidate_set_rejects_empty_csv(tmp_path: Path) -> None:
    path = tmp_path / "empty.csv"
    path.write_text("", encoding="utf-8")

    with pytest.raises(CandidateCsvError, match="Could not read candidate CSV"):
        load_candidate_set(path)
