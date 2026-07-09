from pathlib import Path

from app.models.candidate import CandidateSet
from app.services.candidate_repository import load_candidate_set
from app.services.projection import project_candidate_set


def test_project_candidate_set_returns_coordinates_for_valid_candidates() -> None:
    candidate_set = load_candidate_set(Path("tests/fixtures/tiny_candidates.csv"))

    points = project_candidate_set(candidate_set)

    assert len(points) == 5
    assert {point.candidate_id for point in points} == {
        "demo-1",
        "demo-2",
        "demo-3",
        "demo-4",
        "demo-5",
    }
    assert all(isinstance(point.x, float) and isinstance(point.y, float) for point in points)


def test_project_candidate_set_returns_empty_for_fewer_than_two_valid_candidates() -> None:
    candidate_set = load_candidate_set(Path("tests/fixtures/tiny_candidates.csv"))
    single_candidate_set = CandidateSet(
        id="single",
        name="Single Candidate",
        candidates=(candidate_set.candidates[0],),
    )

    assert project_candidate_set(single_candidate_set) == ()
