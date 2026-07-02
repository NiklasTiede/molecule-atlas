from fastapi.testclient import TestClient

from app.main import app


def test_get_demo_candidate_set() -> None:
    client = TestClient(app)

    response = client.get("/api/candidate-sets/demo")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == "demo"
    assert len(body["candidates"]) >= 5
    assert body["candidates"][0]["descriptors"]["molecular_weight"] > 0


def test_get_candidate_neighbors() -> None:
    client = TestClient(app)

    response = client.get("/api/candidate-sets/demo/candidates/demo-1/neighbors")

    assert response.status_code == 200
    body = response.json()
    assert len(body) > 0
    assert body[0]["candidate_id"] != "demo-1"
