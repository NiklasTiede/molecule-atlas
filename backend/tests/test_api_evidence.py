from fastapi.testclient import TestClient

from app.main import app


def test_get_run_summary_endpoint_uses_capability_contract() -> None:
    response = TestClient(app).get(
        "/api/evidence/runs/fixture-succeeded",
        headers={"X-Correlation-ID": "corr-http-test"},
    )

    assert response.status_code == 200
    assert response.headers["X-Correlation-ID"] == "corr-http-test"
    body = response.json()
    assert body["capability_id"] == "get_run_summary"
    assert body["correlation_id"] == "corr-http-test"
    assert body["run"]["run_id"] == "fixture-succeeded"
    assert body["run"]["validation_counts"]["fail_count"] == 1


def test_get_run_summary_endpoint_maps_not_found() -> None:
    response = TestClient(app).get("/api/evidence/runs/unknown-run")

    assert response.status_code == 404
    assert response.json() == {"detail": "Evidence run not found: unknown-run"}


def test_get_run_summary_has_stable_openapi_operation_id() -> None:
    operation = app.openapi()["paths"]["/api/evidence/runs/{run_id}"]["get"]

    assert operation["operationId"] == "get_run_summary"
