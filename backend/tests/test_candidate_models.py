import pytest
from pydantic import ValidationError

from app.models.candidate import ValidationNote


def test_validation_note_accepts_known_levels() -> None:
    note = ValidationNote(level="warning", message="Invalid SMILES")

    assert note.level == "warning"
    assert note.message == "Invalid SMILES"


def test_validation_note_rejects_unknown_level() -> None:
    with pytest.raises(ValidationError):
        ValidationNote(level="critical", message="Unsupported level")
