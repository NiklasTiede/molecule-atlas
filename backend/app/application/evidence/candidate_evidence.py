from molecule_atlas.evidence.models import InputReference, Prediction, ValidationResult

from app.application.capabilities.catalog import GET_CANDIDATE_EVIDENCE
from app.application.capabilities.models import CapabilityContext, require_permissions
from app.application.evidence.contracts import (
    CandidateEvidenceBinding,
    CandidateEvidenceWarning,
    CandidateEvidenceWarningCode,
    GetCandidateEvidenceInput,
    GetCandidateEvidenceOutput,
)
from app.application.evidence.ports import EvidenceRunRepository, StoredEvidenceRun
from app.application.evidence.run_summary import (
    EvidenceRunNotFoundError,
    build_method_summary,
)


def _warning(
    code: CandidateEvidenceWarningCode,
    message: str,
) -> CandidateEvidenceWarning:
    return CandidateEvidenceWarning(code=code, message=message)


def _references(request: GetCandidateEvidenceInput) -> tuple[str, ...]:
    references = [request.candidate_id]
    if (
        request.candidate_external_id is not None
        and request.candidate_external_id != request.candidate_id
    ):
        references.append(request.candidate_external_id)
    return tuple(references)


def _matching_inputs(
    stored_run: StoredEvidenceRun,
    references: tuple[str, ...],
) -> tuple[InputReference, ...]:
    reference_set = set(references)
    return tuple(
        input_reference
        for input_reference in stored_run.manifest.inputs
        if input_reference.kind == "ligand"
        and (input_reference.id in reference_set or input_reference.upstream_id in reference_set)
    )


def _binding(
    request: GetCandidateEvidenceInput,
    *,
    references: tuple[str, ...],
    matched_inputs: tuple[InputReference, ...],
) -> CandidateEvidenceBinding:
    if not matched_inputs:
        status = "unbound"
        explanation = "No recorded ligand input ID or upstream ID matches the candidate references."
    elif len(matched_inputs) > 1:
        status = "ambiguous"
        explanation = (
            "Multiple recorded ligand inputs match the candidate references; evidence was not "
            "assigned automatically."
        )
    else:
        status = "bound"
        explanation = "One recorded ligand input matches the candidate references exactly."
    return CandidateEvidenceBinding(
        status=status,
        candidate_id=request.candidate_id,
        candidate_external_id=request.candidate_external_id,
        reference_ids_checked=references,
        matched_input_ids=tuple(item.id for item in matched_inputs),
        matched_input_artifact_ids=tuple(item.artifact_id for item in matched_inputs),
        explanation=explanation,
    )


def _related_artifact_ids(
    stored_run: StoredEvidenceRun,
    input_artifact_id: str,
) -> tuple[str, ...]:
    related = {input_artifact_id}
    artifact_manifest = stored_run.artifact_manifest
    if artifact_manifest is not None:
        changed = True
        while changed:
            changed = False
            for artifact in artifact_manifest.artifacts:
                if artifact.artifact_id not in related and any(
                    source_id in related for source_id in artifact.derived_from_artifact_ids
                ):
                    related.add(artifact.artifact_id)
                    changed = True
    return tuple(
        artifact.id for artifact in stored_run.manifest.artifacts if artifact.id in related
    )


def _related_predictions(
    stored_run: StoredEvidenceRun,
    *,
    related_artifact_ids: tuple[str, ...],
    scope_reference_ids: frozenset[str],
) -> tuple[Prediction, ...]:
    related_set = set(related_artifact_ids)
    return tuple(
        prediction
        for prediction in stored_run.manifest.predictions
        if prediction.raw_source.artifact_id in related_set
        or (prediction.scope == "ligand" and prediction.scope_id in scope_reference_ids)
    )


def _related_validation_results(
    stored_run: StoredEvidenceRun,
    *,
    related_artifact_ids: tuple[str, ...],
) -> tuple[ValidationResult, ...]:
    related_set = set(related_artifact_ids)
    return tuple(
        result
        for result in stored_run.manifest.validation_results
        if result.input_artifact_id in related_set or result.raw_output_artifact_id in related_set
    )


class GetCandidateEvidenceCapability:
    definition = GET_CANDIDATE_EVIDENCE

    def __init__(self, repository: EvidenceRunRepository) -> None:
        self._repository = repository

    def execute(
        self,
        request: GetCandidateEvidenceInput,
        *,
        context: CapabilityContext,
    ) -> GetCandidateEvidenceOutput:
        require_permissions(self.definition, context)
        stored_run = self._repository.find(request.run_id)
        if stored_run is None:
            raise EvidenceRunNotFoundError(f"Evidence run not found: {request.run_id}")

        references = _references(request)
        matched_inputs = _matching_inputs(stored_run, references)
        binding = _binding(request, references=references, matched_inputs=matched_inputs)
        lineage_available = stored_run.artifact_manifest is not None
        warnings: list[CandidateEvidenceWarning] = []

        if binding.status == "unbound":
            warnings.append(
                _warning(
                    "candidate_not_bound",
                    "Candidate evidence remains unbound because no recorded ligand input matched.",
                )
            )
            related_artifact_ids: tuple[str, ...] = ()
            predictions: tuple[Prediction, ...] = ()
            validation_results: tuple[ValidationResult, ...] = ()
        elif binding.status == "ambiguous":
            warnings.append(
                _warning(
                    "ambiguous_candidate_binding",
                    "Candidate evidence remains unbound because multiple ligand inputs matched.",
                )
            )
            related_artifact_ids = ()
            predictions = ()
            validation_results = ()
        else:
            matched_input = matched_inputs[0]
            related_artifact_ids = _related_artifact_ids(
                stored_run,
                matched_input.artifact_id,
            )
            scope_reference_ids = frozenset(
                (
                    *references,
                    matched_input.id,
                    matched_input.artifact_id,
                    *(
                        (matched_input.upstream_id,)
                        if matched_input.upstream_id is not None
                        else ()
                    ),
                )
            )
            predictions = _related_predictions(
                stored_run,
                related_artifact_ids=related_artifact_ids,
                scope_reference_ids=scope_reference_ids,
            )
            validation_results = _related_validation_results(
                stored_run,
                related_artifact_ids=related_artifact_ids,
            )
            if not lineage_available:
                warnings.append(
                    _warning(
                        "semantic_lineage_unavailable",
                        "No semantic artifact manifest was recorded; evidence was limited to "
                        "direct artifact and ligand-scope references.",
                    )
                )

        prediction_total = len(predictions)
        validation_total = len(validation_results)
        if prediction_total > request.prediction_limit:
            warnings.append(
                _warning(
                    "prediction_limit_reached",
                    "Additional related predictions exist beyond the requested limit.",
                )
            )
        if validation_total > request.validation_limit:
            warnings.append(
                _warning(
                    "validation_limit_reached",
                    "Additional related validation results exist beyond the requested limit.",
                )
            )

        return GetCandidateEvidenceOutput(
            correlation_id=context.correlation_id,
            run_id=request.run_id,
            binding=binding,
            method=build_method_summary(stored_run.manifest.method),
            lineage_available=lineage_available,
            related_artifact_ids=related_artifact_ids,
            prediction_total=prediction_total,
            prediction_limit=request.prediction_limit,
            predictions=predictions[: request.prediction_limit],
            validation_total=validation_total,
            validation_limit=request.validation_limit,
            validation_results=validation_results[: request.validation_limit],
            warnings=tuple(warnings),
        )
