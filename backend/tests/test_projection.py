from pathlib import Path

from app.services.candidate_repository import load_candidate_set
from app.services.projection import project_candidate_set


def test_project_candidate_set_returns_coordinates_for_valid_candidates() -> None:
    candidate_set = load_candidate_set(Path("tests/fixtures/tiny_candidates.csv"))

    points = project_candidate_set(candidate_set)

    assert len(points) == 5
    assert {point["candidate_id"] for point in points} == {
        "demo-1",
        "demo-2",
        "demo-3",
        "demo-4",
        "demo-5",
    }
    assert all("x" in point and "y" in point for point in points)
