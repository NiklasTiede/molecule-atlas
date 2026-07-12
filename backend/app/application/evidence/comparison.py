from collections import OrderedDict

from molecule_atlas.evidence.models import Prediction

from app.application.capabilities.catalog import COMPARE_CANDIDATES
from app.application.capabilities.models import CapabilityContext, require_permissions
from app.application.evidence.candidate_evidence import GetCandidateEvidenceCapability
from app.application.evidence.contracts import (
    CompareCandidatesInput,
    CompareCandidatesOutput,
    ComparisonPredictionEntry,
    ComparisonSubjectResult,
    ComparisonWarning,
    GetCandidateEvidenceInput,
    OptimizationDirection,
    PredictionComparisonGroup,
    PredictionType,
    ValidationCounts,
)
from app.application.evidence.ports import EvidenceRunRepository

PredictionKey = tuple[PredictionType, str | None, OptimizationDirection]


def _counts(statuses: tuple[str, ...]) -> ValidationCounts:
    return ValidationCounts(
        pass_count=statuses.count("pass"),
        fail_count=statuses.count("fail"),
        warning_count=statuses.count("warning"),
        unavailable_count=statuses.count("unavailable"),
        error_count=statuses.count("error"),
    )


def _prediction_key(prediction: Prediction) -> PredictionKey:
    return (prediction.type, prediction.unit, prediction.optimization_direction)


class CompareCandidatesCapability:
    definition = COMPARE_CANDIDATES

    def __init__(self, repository: EvidenceRunRepository) -> None:
        self._candidate_evidence = GetCandidateEvidenceCapability(repository)

    def execute(
        self,
        request: CompareCandidatesInput,
        *,
        context: CapabilityContext,
    ) -> CompareCandidatesOutput:
        require_permissions(self.definition, context)
        subject_results: list[ComparisonSubjectResult] = []
        warnings: list[ComparisonWarning] = []
        entries_by_key: OrderedDict[PredictionKey, list[ComparisonPredictionEntry]] = OrderedDict()
        prediction_count = 0

        for subject in request.subjects:
            evidence = self._candidate_evidence.execute(
                GetCandidateEvidenceInput(
                    run_id=subject.run_id,
                    candidate_id=subject.candidate_id,
                    candidate_external_id=subject.candidate_external_id,
                ),
                context=context,
            )
            statuses = tuple(result.status for result in evidence.validation_results)
            subject_results.append(
                ComparisonSubjectResult(
                    subject_id=subject.subject_id,
                    label=subject.label,
                    run_id=subject.run_id,
                    candidate_id=subject.candidate_id,
                    candidate_external_id=subject.candidate_external_id,
                    binding=evidence.binding,
                    method=evidence.method,
                    validation_counts=_counts(statuses),
                    related_artifact_ids=evidence.related_artifact_ids,
                )
            )
            if evidence.binding.status == "unbound":
                warnings.append(
                    ComparisonWarning(
                        code="comparison_subject_unbound",
                        subject_id=subject.subject_id,
                        message="No recorded ligand input matched this comparison subject.",
                    )
                )
            elif evidence.binding.status == "ambiguous":
                warnings.append(
                    ComparisonWarning(
                        code="comparison_subject_ambiguous",
                        subject_id=subject.subject_id,
                        message="Multiple recorded ligand inputs matched this comparison subject.",
                    )
                )

            prediction_count += len(evidence.predictions)
            for prediction in evidence.predictions:
                entries_by_key.setdefault(_prediction_key(prediction), []).append(
                    ComparisonPredictionEntry(
                        subject_id=subject.subject_id,
                        run_id=subject.run_id,
                        candidate_id=subject.candidate_id,
                        prediction=prediction,
                    )
                )

        groups = tuple(
            PredictionComparisonGroup(
                prediction_type=key[0],
                unit=key[1],
                optimization_direction=key[2],
                entries=tuple(entries),
            )
            for key, entries in entries_by_key.items()
            if len({entry.subject_id for entry in entries}) >= 2
        )
        included_count = sum(len(group.entries) for group in groups)
        if not groups:
            warnings.append(
                ComparisonWarning(
                    code="no_shared_prediction_groups",
                    message=(
                        "The selected subjects share no prediction type, unit, and optimization "
                        "direction suitable for like-for-like comparison."
                    ),
                )
            )

        return CompareCandidatesOutput(
            correlation_id=context.correlation_id,
            subjects=tuple(subject_results),
            prediction_groups=groups,
            excluded_prediction_count=prediction_count - included_count,
            warnings=tuple(warnings),
        )
