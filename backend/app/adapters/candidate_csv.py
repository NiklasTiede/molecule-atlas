import math
from pathlib import Path

import pandas as pd

from app.models.candidate import CandidateInput

_REQUIRED_COLUMNS = frozenset({"name", "smiles"})


class CandidateCsvError(ValueError):
    """Raised when an input CSV cannot be converted to typed candidate rows."""


def _optional_text(value: str) -> str | None:
    text = value.strip()
    return text or None


def _required_text(value: str, column: str, row_number: int) -> str:
    text = value.strip()
    if not text:
        raise CandidateCsvError(f"Row {row_number}: {column} is required")
    return text


def _optional_float(value: str, column: str, row_number: int) -> float | None:
    text = value.strip()
    if not text:
        return None
    try:
        parsed = float(text)
    except ValueError as error:
        raise CandidateCsvError(
            f"Row {row_number}: {column} must be a number, got {value!r}"
        ) from error
    if not math.isfinite(parsed):
        raise CandidateCsvError(f"Row {row_number}: {column} must be finite, got {value!r}")
    return parsed


def read_candidate_inputs(path: Path) -> tuple[CandidateInput, ...]:
    try:
        frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    except (pd.errors.EmptyDataError, pd.errors.ParserError) as error:
        raise CandidateCsvError(f"Could not read candidate CSV: {error}") from error
    columns = tuple(str(column) for column in frame.columns)
    missing_columns = _REQUIRED_COLUMNS.difference(columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise CandidateCsvError(f"Missing required CSV columns: {missing}")

    candidates: list[CandidateInput] = []
    for row_number, values in enumerate(frame.itertuples(index=False, name=None), start=2):
        record = dict(zip(columns, values, strict=True))
        if not all(isinstance(value, str) for value in record.values()):
            raise CandidateCsvError(f"Row {row_number}: all CSV cells must be text")

        candidates.append(
            CandidateInput(
                name=_required_text(record["name"], "name", row_number),
                smiles=_required_text(record["smiles"], "smiles", row_number),
                source=_optional_text(record.get("source", "")),
                external_id=_optional_text(record.get("external_id", "")),
                score=_optional_float(record.get("score", ""), "score", row_number),
                target=_optional_text(record.get("target", "")),
                notes=_optional_text(record.get("notes", "")),
            )
        )

    return tuple(candidates)
