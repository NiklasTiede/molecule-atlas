from pathlib import Path

from app.services.candidate_repository import load_candidate_set
from app.services.similarity import nearest_neighbors


def test_nearest_neighbors_excludes_query_and_sorts_descending() -> None:
    candidate_set = load_candidate_set(Path("tests/fixtures/tiny_candidates.csv"))

    neighbors = nearest_neighbors(candidate_set, "demo-1", limit=3)

    assert len(neighbors) == 3
    assert neighbors[0].candidate_id != "demo-1"
    assert neighbors[0].similarity >= neighbors[1].similarity >= neighbors[2].similarity
