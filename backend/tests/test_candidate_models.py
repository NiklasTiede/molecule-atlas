import pytest
from pydantic import ValidationError

from app.models.candidate import DescriptorSet, InvalidCandidate, ValidationNote, ValidCandidate


def test_validation_note_accepts_known_levels() -> None:
    note = ValidationNote(level="warning", message="Invalid SMILES")

    assert note.level == "warning"
    assert note.message == "Invalid SMILES"


def test_validation_note_rejects_unknown_level() -> None:
    with pytest.raises(ValidationError):
        ValidationNote.model_validate({"level": "critical", "message": "Unsupported level"})


def test_api_models_reject_extra_fields() -> None:
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        ValidationNote.model_validate(
            {
                "level": "warning",
                "message": "Invalid SMILES",
                "unexpected": True,
            }
        )


def test_descriptor_model_rejects_string_coercion() -> None:
    with pytest.raises(ValidationError, match="valid number"):
        DescriptorSet.model_validate(
            {
                "molecular_weight": "180.2",
                "logp": 1.2,
                "tpsa": 63.6,
                "hbond_donors": 1,
                "hbond_acceptors": 3,
                "rotatable_bonds": 2,
                "ring_count": 1,
                "heavy_atom_count": 13,
                "fraction_csp3": 0.1,
                "murcko_scaffold": "c1ccccc1",
            }
        )


def test_api_models_are_frozen() -> None:
    note = ValidationNote(level="warning", message="Invalid SMILES")

    with pytest.raises(ValidationError, match="Instance is frozen"):
        setattr(note, "message", "Changed")  # noqa: B010 - exercise runtime freezing


def test_valid_candidate_requires_valid_only_fields() -> None:
    with pytest.raises(ValidationError):
        ValidCandidate.model_validate(
            {
                "id": "demo-1",
                "name": "Aspirin",
                "smiles": "CC(=O)Oc1ccccc1C(=O)O",
                "is_valid": True,
                "canonical_smiles": None,
                "validation_notes": [],
                "descriptors": None,
                "triage_flags": None,
                "structure_svg": None,
                "neighbors": [],
            }
        )


def test_invalid_candidate_rejects_valid_only_fields() -> None:
    with pytest.raises(ValidationError):
        InvalidCandidate.model_validate(
            {
                "id": "demo-1",
                "name": "Broken",
                "smiles": "not_a_smiles",
                "is_valid": False,
                "canonical_smiles": "C",
                "validation_notes": [{"level": "error", "message": "Invalid SMILES"}],
                "descriptors": None,
                "triage_flags": None,
                "structure_svg": None,
                "neighbors": [],
            }
        )
