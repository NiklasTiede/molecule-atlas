from datetime import datetime
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator

SchemaVersion = Literal["0.1.0"]
RunState = Literal["succeeded", "failed", "partial", "cancelled", "unknown"]
InputKind = Literal["receptor", "ligand", "complex", "other"]
StructureRepresentation = Literal[
    "2d_depiction",
    "conformer",
    "predicted_pose",
    "docked_pose",
    "experimental_complex",
    "sequence",
    "other",
]
ArtifactRole = Literal[
    "receptor_input",
    "ligand_input",
    "predicted_complex",
    "pose_set",
    "raw_score_output",
    "validation_output",
    "interaction_output",
    "log",
    "report",
    "other",
]
PredictionScope = Literal["complex", "pose", "ligand", "residue", "atom"]
OptimizationDirection = Literal["lower_is_better", "higher_is_better", "none"]
ValidationStatus = Literal["pass", "fail", "warning", "unavailable", "error"]
LicenseComponent = Literal[
    "adapter_code",
    "upstream_code",
    "model_weights",
    "dataset",
    "other",
]

_SEMVER_PATTERN = (
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$"
)
_SHA256_PATTERN = r"^[0-9a-f]{64}$"
_CONTAINER_DIGEST_PATTERN = r"^sha256:[0-9a-f]{64}$"


class EvidenceModel(BaseModel):
    """Strict base for portable evidence contracts."""

    model_config = ConfigDict(
        allow_inf_nan=False,
        extra="forbid",
        frozen=True,
        strict=True,
    )


class RunFailure(EvidenceModel):
    category: str = Field(min_length=1)
    message: str = Field(min_length=1)
    stage: str | None = Field(default=None, min_length=1)
    exit_code: int | None = None
    details: dict[str, JsonValue]


class RunMetadata(EvidenceModel):
    id: str = Field(min_length=1)
    state: RunState
    started_at: datetime | None
    finished_at: datetime | None
    expected_outputs: tuple[str, ...]
    missing_outputs: tuple[str, ...]
    failure: RunFailure | None

    @model_validator(mode="after")
    def validate_state_details(self) -> Self:
        if self.state == "failed" and self.failure is None:
            raise ValueError("failed run requires failure details")
        if self.state == "partial" and not self.missing_outputs and self.failure is None:
            raise ValueError("partial run requires missing outputs or failure details")
        if self.state == "succeeded" and (self.failure is not None or self.missing_outputs):
            raise ValueError("succeeded run cannot contain failure details or missing outputs")
        if (
            self.started_at is not None
            and self.finished_at is not None
            and self.finished_at < self.started_at
        ):
            raise ValueError("finished_at cannot be earlier than started_at")
        return self


class MethodMetadata(EvidenceModel):
    id: str = Field(min_length=1)
    adapter_id: str = Field(min_length=1)
    adapter_version: str = Field(pattern=_SEMVER_PATTERN)
    upstream_tool: str | None = Field(default=None, min_length=1)
    upstream_version: str | None = Field(default=None, min_length=1)
    source_commit: str | None = Field(default=None, min_length=1)
    checkpoint_id: str | None = Field(default=None, min_length=1)
    checkpoint_sha256: str | None = Field(default=None, pattern=_SHA256_PATTERN)
    container_image: str | None = Field(default=None, min_length=1)
    container_digest: str | None = Field(default=None, pattern=_CONTAINER_DIGEST_PATTERN)
    command: tuple[str, ...]
    random_seeds: tuple[int, ...]
    metadata: dict[str, JsonValue]


class EnvironmentMetadata(EvidenceModel):
    operating_system: str | None = Field(default=None, min_length=1)
    architecture: str | None = Field(default=None, min_length=1)
    python_version: str | None = Field(default=None, min_length=1)
    accelerator: str | None = Field(default=None, min_length=1)
    hardware: str | None = Field(default=None, min_length=1)
    dependencies: dict[str, str]

    def is_empty(self) -> bool:
        return not any(
            (
                self.operating_system,
                self.architecture,
                self.python_version,
                self.accelerator,
                self.hardware,
                self.dependencies,
            )
        )


class InputReference(EvidenceModel):
    id: str = Field(min_length=1)
    kind: InputKind
    artifact_id: str = Field(min_length=1)
    representation: StructureRepresentation | None
    upstream_id: str | None = Field(default=None, min_length=1)


class Artifact(EvidenceModel):
    id: str = Field(min_length=1)
    role: ArtifactRole
    path_or_uri: str = Field(min_length=1)
    media_type: str = Field(min_length=1)
    sha256: str = Field(pattern=_SHA256_PATTERN)
    size_bytes: int = Field(ge=0)
    created_by_stage: str = Field(min_length=1)
    original_name: str = Field(min_length=1)
    metadata: dict[str, JsonValue]


class PredictionRawSource(EvidenceModel):
    artifact_id: str = Field(min_length=1)
    field: str = Field(min_length=1)
    upstream_record_id: str | None = Field(default=None, min_length=1)


class PredictionUncertainty(EvidenceModel):
    kind: str = Field(min_length=1)
    value: float = Field(ge=0)
    unit: str | None = Field(default=None, min_length=1)


class _PredictionBase(EvidenceModel):
    id: str = Field(min_length=1)
    value: float
    scope: PredictionScope
    scope_id: str = Field(min_length=1)
    method_id: str = Field(min_length=1)
    raw_source: PredictionRawSource
    uncertainty: PredictionUncertainty | None
    interpretation: str = Field(min_length=1)
    caveats: tuple[str, ...]


class DockingEnergyPrediction(_PredictionBase):
    type: Literal["docking_energy"] = "docking_energy"
    unit: str = Field(min_length=1)
    optimization_direction: Literal["lower_is_better"] = "lower_is_better"


class PoseConfidencePrediction(_PredictionBase):
    type: Literal["pose_confidence"] = "pose_confidence"
    unit: None = None
    optimization_direction: Literal["higher_is_better"] = "higher_is_better"


class StructureConfidencePrediction(_PredictionBase):
    type: Literal["structure_confidence"] = "structure_confidence"
    unit: None = None
    optimization_direction: Literal["higher_is_better"] = "higher_is_better"


class BinderProbabilityPrediction(_PredictionBase):
    type: Literal["binder_probability"] = "binder_probability"
    value: float = Field(ge=0, le=1)
    unit: Literal["probability"] = "probability"
    optimization_direction: Literal["higher_is_better"] = "higher_is_better"


class PredictedAffinityPrediction(_PredictionBase):
    type: Literal["predicted_affinity"] = "predicted_affinity"
    unit: str = Field(min_length=1)
    optimization_direction: Literal["lower_is_better", "higher_is_better"]


Prediction = Annotated[
    DockingEnergyPrediction
    | PoseConfidencePrediction
    | StructureConfidencePrediction
    | BinderProbabilityPrediction
    | PredictedAffinityPrediction,
    Field(discriminator="type"),
]


class ValidationResult(EvidenceModel):
    id: str = Field(min_length=1)
    validator: str = Field(min_length=1)
    validator_version: str = Field(min_length=1)
    check_id: str = Field(min_length=1)
    status: ValidationStatus
    measured_value: bool | int | float | str | None
    unit: str | None = Field(default=None, min_length=1)
    threshold_or_configuration: dict[str, JsonValue]
    explanation: str = Field(min_length=1)
    input_artifact_id: str = Field(min_length=1)
    raw_output_artifact_id: str = Field(min_length=1)


class LicenseMetadata(EvidenceModel):
    component: LicenseComponent
    identifier: str | None = Field(default=None, min_length=1)
    name: str | None = Field(default=None, min_length=1)
    source_uri: str | None = Field(default=None, min_length=1)
    redistribution_restrictions: str | None = Field(default=None, min_length=1)
    acknowledgement_required: bool
    notes: str | None = Field(default=None, min_length=1)


class ManifestWarning(EvidenceModel):
    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    path: str = Field(min_length=1)


def _duplicates(values: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return tuple(sorted(duplicates))


class RunManifest(EvidenceModel):
    schema_version: SchemaVersion
    run: RunMetadata
    method: MethodMetadata
    inputs: tuple[InputReference, ...]
    parameters: dict[str, JsonValue]
    environment: EnvironmentMetadata
    artifacts: tuple[Artifact, ...]
    predictions: tuple[Prediction, ...]
    validation_results: tuple[ValidationResult, ...]
    licenses: tuple[LicenseMetadata, ...]
    warnings: tuple[ManifestWarning, ...]

    @model_validator(mode="after")
    def validate_ids_and_lineage(self) -> Self:
        identity_groups = {
            "artifact": tuple(artifact.id for artifact in self.artifacts),
            "input": tuple(input_reference.id for input_reference in self.inputs),
            "prediction": tuple(prediction.id for prediction in self.predictions),
            "validation result": tuple(result.id for result in self.validation_results),
        }
        for label, values in identity_groups.items():
            duplicates = _duplicates(values)
            if duplicates:
                raise ValueError(f"duplicate {label} IDs: {', '.join(duplicates)}")

        artifact_ids = set(identity_groups["artifact"])
        for input_reference in self.inputs:
            if input_reference.artifact_id not in artifact_ids:
                raise ValueError(
                    f"input {input_reference.id} references unknown artifact "
                    f"{input_reference.artifact_id}"
                )
        for prediction in self.predictions:
            if prediction.method_id != self.method.id:
                raise ValueError(
                    f"prediction {prediction.id} references unknown method {prediction.method_id}"
                )
            if prediction.raw_source.artifact_id not in artifact_ids:
                raise ValueError(
                    f"prediction {prediction.id} references unknown raw artifact "
                    f"{prediction.raw_source.artifact_id}"
                )
        for result in self.validation_results:
            for label, artifact_id in (
                ("input", result.input_artifact_id),
                ("raw output", result.raw_output_artifact_id),
            ):
                if artifact_id not in artifact_ids:
                    raise ValueError(
                        f"validation result {result.id} references unknown {label} artifact "
                        f"{artifact_id}"
                    )
        return self
