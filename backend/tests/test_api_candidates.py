from fastapi.testclient import TestClient

from app.main import app
from app.models.api import ErrorResponse
from app.models.candidate import CandidateSet


def test_get_demo_candidate_set() -> None:
    client = TestClient(app)

    response = client.get("/api/candidate-sets/demo")

    assert response.status_code == 200
    candidate_set = CandidateSet.model_validate_json(response.content)
    assert candidate_set.id == "demo"
    assert len(candidate_set.candidates) >= 5
    first_candidate = candidate_set.candidates[0]
    assert first_candidate.is_valid is True
    assert first_candidate.descriptors.molecular_weight > 0


def test_get_candidate_neighbors() -> None:
    client = TestClient(app)

    response = client.get("/api/candidate-sets/demo/candidates/demo-1/neighbors")

    assert response.status_code == 200
    body = response.json()
    assert len(body) > 0
    assert body[0]["candidate_id"] != "demo-1"


def test_get_candidate_neighbors_returns_not_found() -> None:
    response = TestClient(app).get("/api/candidate-sets/demo/candidates/does-not-exist/neighbors")

    assert response.status_code == 404
    assert ErrorResponse.model_validate_json(response.content).detail == "Candidate not found"


def test_get_candidate_neighbors_returns_empty_for_invalid_candidate() -> None:
    response = TestClient(app).get("/api/candidate-sets/demo/candidates/demo-6/neighbors")

    assert response.status_code == 200
    assert response.json() == []
