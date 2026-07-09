from app.chem.rendering import ConformerGenerationError, mol_to_sdf_block
from app.chem.standardization import InvalidParsedMolecule, parse_smiles
from app.models.api import ConformerResponse
from app.models.candidate import CandidateSet, is_valid_candidate
from app.services.similarity import CandidateNotFoundError, find_candidate


class InvalidCandidateForConformerError(ValueError):
    pass


class StoredCandidateDataError(RuntimeError):
    pass


class ConformerUnavailableError(RuntimeError):
    pass


def generate_candidate_conformer(
    candidate_set: CandidateSet,
    candidate_id: str,
) -> ConformerResponse:
    candidate = find_candidate(candidate_set, candidate_id)
    if candidate is None:
        raise CandidateNotFoundError(candidate_id)
    if not is_valid_candidate(candidate):
        raise InvalidCandidateForConformerError("Cannot generate conformer for invalid molecule")

    parsed = parse_smiles(candidate.canonical_smiles)
    if isinstance(parsed, InvalidParsedMolecule):
        raise StoredCandidateDataError("Stored canonical SMILES is invalid")

    try:
        mol_block = mol_to_sdf_block(parsed.mol)
    except ConformerGenerationError as error:
        raise ConformerUnavailableError(str(error)) from error
    return ConformerResponse(candidate_id=candidate.id, mol_block=mol_block)
