import pytest
from fastapi.testclient import TestClient
from rdkit import Chem
from rdkit.Chem import AllChem

from app.main import app
from app.models.api import ConformerResponse, ErrorResponse


def test_get_candidate_conformer_returns_mol_block() -> None:
    client = TestClient(app)

    response = client.get("/api/candidate-sets/demo/candidates/demo-1/conformer")

    assert response.status_code == 200
    conformer = ConformerResponse.model_validate_json(response.content)
    assert conformer.candidate_id == "demo-1"
    assert "M  END" in conformer.mol_block


def test_get_candidate_conformer_returns_not_found() -> None:
    response = TestClient(app).get("/api/candidate-sets/demo/candidates/does-not-exist/conformer")

    assert response.status_code == 404
    assert ErrorResponse.model_validate_json(response.content).detail == "Candidate not found"


def test_get_candidate_conformer_rejects_invalid_candidate() -> None:
    response = TestClient(app).get("/api/candidate-sets/demo/candidates/demo-6/conformer")

    assert response.status_code == 422
    assert (
        ErrorResponse.model_validate_json(response.content).detail
        == "Cannot generate conformer for invalid molecule"
    )


def test_get_candidate_conformer_handles_embedding_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_embedding(mol: Chem.Mol, randomSeed: int = -1) -> int:
        return -1

    monkeypatch.setattr(AllChem, "EmbedMolecule", fail_embedding)

    response = TestClient(app).get("/api/candidate-sets/demo/candidates/demo-1/conformer")

    assert response.status_code == 422
    assert (
        ErrorResponse.model_validate_json(response.content).detail
        == "Could not generate a 3D conformer for this molecule."
    )
