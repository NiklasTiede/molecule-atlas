from pathlib import Path

from fastapi.testclient import TestClient

from app.api.evidence import (
    MAX_EVIDENCE_BUNDLE_BYTES,
    get_import_evidence_capability,
    get_run_summary_capability,
)
from app.application.evidence.import_bundle import ImportEvidenceBundleCapability
from app.application.evidence.run_summary import GetRunSummaryCapability
from app.infrastructure.evidence.local_repository import LocalEvidenceRunRepository
from app.main import app
from tests.evidence_bundle_factory import evidence_bundle_bytes

FIXTURE_ROOT = Path(__file__).parents[2] / "data" / "evidence-fixtures"


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


def test_import_evidence_bundle_endpoint_publishes_run_for_summary_query(tmp_path: Path) -> None:
    repository = LocalEvidenceRunRepository((), upload_root=tmp_path)
    import_capability = ImportEvidenceBundleCapability(repository)
    summary_capability = GetRunSummaryCapability(repository)
    app.dependency_overrides[get_import_evidence_capability] = lambda: import_capability
    app.dependency_overrides[get_run_summary_capability] = lambda: summary_capability
    try:
        response = TestClient(app).post(
            "/api/evidence/imports",
            files={
                "bundle": (
                    "evidence.zip",
                    evidence_bundle_bytes(FIXTURE_ROOT / "succeeded"),
                    "application/zip",
                )
            },
            headers={
                "Idempotency-Key": "web-import-1",
                "X-Correlation-ID": "corr-web-import",
            },
        )
        summary_response = TestClient(app).get(
            "/api/evidence/runs/fixture-succeeded",
            headers={"X-Correlation-ID": "corr-web-summary"},
        )
    finally:
        app.dependency_overrides.pop(get_import_evidence_capability)
        app.dependency_overrides.pop(get_run_summary_capability)

    assert response.status_code == 201
    assert response.headers["X-Correlation-ID"] == "corr-web-import"
    assert response.json()["run"]["run_id"] == "fixture-succeeded"
    assert summary_response.status_code == 200
    assert summary_response.json()["run"]["run_id"] == "fixture-succeeded"


def test_import_evidence_bundle_endpoint_rejects_oversized_transport() -> None:
    response = TestClient(app).post(
        "/api/evidence/imports",
        files={"bundle": ("large.zip", b"x" * (MAX_EVIDENCE_BUNDLE_BYTES + 1), "application/zip")},
        headers={"Idempotency-Key": "web-import-large"},
    )

    assert response.status_code == 413
    assert response.json() == {"detail": "Evidence bundle exceeds the 10485760-byte limit"}


def test_import_evidence_bundle_endpoint_maps_invalid_zip_with_correlation() -> None:
    response = TestClient(app).post(
        "/api/evidence/imports",
        files={"bundle": ("invalid.zip", b"not-a-zip", "application/zip")},
        headers={
            "Idempotency-Key": "web-import-invalid",
            "X-Correlation-ID": "corr-web-invalid",
        },
    )

    assert response.status_code == 400
    assert response.headers["X-Correlation-ID"] == "corr-web-invalid"
    assert "not a readable ZIP" in response.json()["detail"]


def test_import_evidence_bundle_has_stable_openapi_operation_id() -> None:
    operation = app.openapi()["paths"]["/api/evidence/imports"]["post"]

    assert operation["operationId"] == "import_evidence_bundle"


def test_list_available_artifacts_endpoint_is_bounded_and_correlated() -> None:
    response = TestClient(app).get(
        "/api/evidence/runs/fixture-succeeded/artifacts?offset=1&limit=2",
        headers={"X-Correlation-ID": "corr-http-artifacts"},
    )

    assert response.status_code == 200
    assert response.headers["X-Correlation-ID"] == "corr-http-artifacts"
    body = response.json()
    assert body["total"] == 4
    assert body["offset"] == 1
    assert body["limit"] == 2
    assert [artifact["artifact_id"] for artifact in body["artifacts"]] == [
        "predicted-pose",
        "raw-predictions",
    ]


def test_validate_evidence_artifacts_endpoint_returns_structured_checks() -> None:
    response = TestClient(app).get(
        "/api/evidence/runs/fixture-succeeded/artifact-validation",
        headers={"X-Correlation-ID": "corr-http-validation"},
    )

    assert response.status_code == 200
    assert response.headers["X-Correlation-ID"] == "corr-http-validation"
    body = response.json()
    assert body["counts"]["verified_count"] == 4
    assert {check["status"] for check in body["artifact_checks"]} == {"verified"}


def test_artifact_endpoints_have_stable_openapi_operation_ids() -> None:
    paths = app.openapi()["paths"]

    assert (
        paths["/api/evidence/runs/{run_id}/artifacts"]["get"]["operationId"]
        == "list_available_artifacts"
    )
    assert (
        paths["/api/evidence/runs/{run_id}/artifact-validation"]["get"]["operationId"]
        == "validate_evidence_artifacts"
    )
