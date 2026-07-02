from fastapi.testclient import TestClient

from app.main import app


def test_get_candidate_conformer_returns_mol_block() -> None:
    client = TestClient(app)

    response = client.get("/api/candidate-sets/demo/candidates/demo-1/conformer")

    assert response.status_code == 200
    body = response.json()
    assert body["candidate_id"] == "demo-1"
    assert "M  END" in body["mol_block"]
