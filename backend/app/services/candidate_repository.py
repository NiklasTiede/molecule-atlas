from pathlib import Path

import pandas as pd

from app.chem.descriptors import calculate_descriptors
from app.chem.rendering import mol_to_svg
from app.chem.standardization import parse_smiles
from app.chem.triage import calculate_triage_flags
from app.models.candidate import Candidate, CandidateSet


def _optional_str(value: object) -> str | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


def _optional_float(value: object) -> float | None:
    if value is None or pd.isna(value) or value == "":
        return None
    return float(value)


def load_candidate_set(
    path: Path,
    candidate_set_id: str = "demo",
    name: str = "Demo Candidate Set",
) -> CandidateSet:
    frame = pd.read_csv(path)
    candidates: list[Candidate] = []

    for index, row in frame.iterrows():
        parsed = parse_smiles(str(row["smiles"]))
        descriptors = calculate_descriptors(parsed.mol) if parsed.mol is not None else None
        triage = calculate_triage_flags(descriptors) if descriptors is not None else None
        svg = mol_to_svg(parsed.mol) if parsed.mol is not None else None

        candidates.append(
            Candidate(
                id=f"{candidate_set_id}-{index + 1}",
                name=str(row["name"]),
                smiles=str(row["smiles"]),
                canonical_smiles=parsed.canonical_smiles,
                source=_optional_str(row.get("source")),
                external_id=_optional_str(row.get("external_id")),
                score=_optional_float(row.get("score")),
                target=_optional_str(row.get("target")),
                notes=_optional_str(row.get("notes")),
                is_valid=parsed.is_valid,
                validation_notes=parsed.validation_notes,
                descriptors=descriptors,
                triage_flags=triage,
                structure_svg=svg,
            )
        )

    return CandidateSet(id=candidate_set_id, name=name, candidates=candidates)
