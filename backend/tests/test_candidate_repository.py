from pathlib import Path

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
