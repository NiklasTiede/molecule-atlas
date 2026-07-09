from pathlib import Path

from app.adapters.candidate_csv import read_candidate_inputs
from app.chem.descriptors import calculate_descriptors
from app.chem.rendering import mol_to_svg
from app.chem.standardization import ValidParsedMolecule, parse_smiles
from app.chem.triage import calculate_triage_flags
from app.models.candidate import (
    Candidate,
    CandidateInput,
    CandidateSet,
    InvalidCandidate,
    ValidationNote,
    ValidCandidate,
)


def _valid_candidate(
    candidate_input: CandidateInput,
    candidate_id: str,
    parsed: ValidParsedMolecule,
) -> ValidCandidate:
    descriptors = calculate_descriptors(parsed.mol)
    return ValidCandidate(
        id=candidate_id,
        name=candidate_input.name,
        smiles=candidate_input.smiles,
        canonical_smiles=parsed.canonical_smiles,
        source=candidate_input.source,
        external_id=candidate_input.external_id,
        score=candidate_input.score,
        target=candidate_input.target,
        notes=candidate_input.notes,
        validation_notes=(),
        descriptors=descriptors,
        triage_flags=calculate_triage_flags(descriptors),
        structure_svg=mol_to_svg(parsed.mol),
    )


def _invalid_candidate(
    candidate_input: CandidateInput,
    candidate_id: str,
    validation_notes: tuple[ValidationNote, ...],
) -> InvalidCandidate:
    return InvalidCandidate(
        id=candidate_id,
        name=candidate_input.name,
        smiles=candidate_input.smiles,
        source=candidate_input.source,
        external_id=candidate_input.external_id,
        score=candidate_input.score,
        target=candidate_input.target,
        notes=candidate_input.notes,
        validation_notes=validation_notes,
    )


def load_candidate_set(
    path: Path,
    candidate_set_id: str = "demo",
    name: str = "Demo Candidate Set",
) -> CandidateSet:
    candidates: list[Candidate] = []

    for index, candidate_input in enumerate(read_candidate_inputs(path), start=1):
        candidate_id = f"{candidate_set_id}-{index}"
        parsed = parse_smiles(candidate_input.smiles)
        if isinstance(parsed, ValidParsedMolecule):
            candidate = _valid_candidate(
                candidate_input,
                candidate_id,
                parsed,
            )
        else:
            candidate = _invalid_candidate(
                candidate_input,
                candidate_id,
                parsed.validation_notes,
            )
        candidates.append(candidate)

    return CandidateSet(id=candidate_set_id, name=name, candidates=tuple(candidates))
