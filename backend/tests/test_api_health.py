from fastapi.testclient import TestClient

from app.main import app
from app.models.api import HealthResponse


def test_health_returns_ok() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert HealthResponse.model_validate_json(response.content).status == "ok"
