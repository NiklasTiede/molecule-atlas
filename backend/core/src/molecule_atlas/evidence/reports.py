import json
from datetime import datetime

from molecule_atlas.evidence.artifacts import ArtifactCheck
from molecule_atlas.evidence.models import Prediction, RunManifest

_PREDICTION_LABELS = {
    "docking_energy": "Docking energy",
    "pose_confidence": "Pose confidence",
    "structure_confidence": "Structure confidence",
    "binder_probability": "Binder probability",
    "predicted_affinity": "Predicted affinity",
}


def _markdown(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _recorded(value: str | None) -> str:
    return _markdown(value) if value is not None else "not recorded"


def _timestamp(value: datetime | None) -> str:
    return value.isoformat() if value is not None else "not recorded"


def _number(value: float) -> str:
    return format(value, ".15g")


def _prediction_value(prediction: Prediction) -> str:
    unit = f" {prediction.unit}" if prediction.unit is not None else ""
    return f"{_number(prediction.value)}{unit}"


def _json_value(value: object) -> str:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def render_markdown_report(
    manifest: RunManifest,
    *,
    artifact_checks: tuple[ArtifactCheck, ...] = (),
) -> str:
    """Render a deterministic report without collapsing typed evidence into a ranking."""

    lines = [
        "# Molecule Atlas Evidence Report",
        "",
        "> Computational predictions and validation checks are evidence for expert review, "
        "not experimental conclusions.",
        "",
        "## Run",
        "",
        f"- Run ID: `{_markdown(manifest.run.id)}`",
        f"- Schema version: `{manifest.schema_version}`",
        f"- State: **{manifest.run.state}**",
        f"- Started: {_timestamp(manifest.run.started_at)}",
        f"- Finished: {_timestamp(manifest.run.finished_at)}",
    ]
    if manifest.run.expected_outputs:
        expected_outputs = ", ".join(map(_markdown, manifest.run.expected_outputs))
        lines.append(f"- Expected outputs: {expected_outputs}")
    if manifest.run.missing_outputs:
        missing_outputs = ", ".join(map(_markdown, manifest.run.missing_outputs))
        lines.append(f"- Missing expected outputs: **{missing_outputs}**")
    if manifest.run.failure is not None:
        failure = manifest.run.failure
        lines.extend(
            [
                f"- Failure category: `{_markdown(failure.category)}`",
                f"- Failure stage: {_recorded(failure.stage)}",
                f"- Failure message: **{_markdown(failure.message)}**",
            ]
        )
        if failure.exit_code is not None:
            lines.append(f"- Exit code: `{failure.exit_code}`")
        if failure.details:
            lines.append(f"- Failure details: `{_markdown(_json_value(failure.details))}`")

    method = manifest.method
    command = " ".join(map(_markdown, method.command)) if method.command else "not recorded"
    random_seeds = (
        ", ".join(map(str, method.random_seeds)) if method.random_seeds else "not recorded"
    )
    lines.extend(
        [
            "",
            "## Method identity",
            "",
            f"- Method reference: `{_markdown(method.id)}`",
            f"- Adapter: `{_markdown(method.adapter_id)}` `{method.adapter_version}`",
            f"- Upstream tool: {_recorded(method.upstream_tool)}",
            f"- Upstream version: {_recorded(method.upstream_version)}",
            f"- Source commit: {_recorded(method.source_commit)}",
            f"- Checkpoint: {_recorded(method.checkpoint_id)}",
            f"- Checkpoint SHA-256: {_recorded(method.checkpoint_sha256)}",
            f"- Container image: {_recorded(method.container_image)}",
            f"- Container digest: {_recorded(method.container_digest)}",
            f"- Command: {command}",
            f"- Random seeds: {random_seeds}",
            "",
            "## Provenance warnings",
            "",
        ]
    )
    if manifest.warnings:
        lines.extend(
            f"- `{_markdown(warning.code)}` ({_markdown(warning.path)}): "
            f"{_markdown(warning.message)}"
            for warning in manifest.warnings
        )
    else:
        lines.append("- None recorded.")

    lines.extend(["", "## Typed predictions", ""])
    if not manifest.predictions:
        lines.append("No normalized predictions were recorded.")
    for prediction in manifest.predictions:
        label = _PREDICTION_LABELS[prediction.type]
        direction = prediction.optimization_direction.replace("_", " ")
        raw_source = (
            f"{_markdown(prediction.raw_source.artifact_id)} / "
            f"`{_markdown(prediction.raw_source.field)}`"
        )
        lines.extend(
            [
                f"### {label}: `{_markdown(prediction.id)}`",
                "",
                f"- Value: **{_prediction_value(prediction)}**",
                f"- Optimization direction: {direction}",
                f"- Scope: `{prediction.scope}` / `{_markdown(prediction.scope_id)}`",
                f"- Method reference: `{_markdown(prediction.method_id)}`",
                f"- Raw source: {raw_source}",
                f"- Interpretation: {_markdown(prediction.interpretation)}",
            ]
        )
        if prediction.uncertainty is not None:
            uncertainty_unit = (
                f" {prediction.uncertainty.unit}" if prediction.uncertainty.unit is not None else ""
            )
            lines.append(
                f"- Uncertainty: {_number(prediction.uncertainty.value)}{uncertainty_unit} "
                f"({_markdown(prediction.uncertainty.kind)})"
            )
        lines.extend(f"- Caveat: {_markdown(caveat)}" for caveat in prediction.caveats)
        lines.append("")

    check_by_id = {check.artifact_id: check for check in artifact_checks}
    lines.extend(
        [
            "## Artifact inventory",
            "",
            "| ID | Role | Path or URI | Media type | Bytes | SHA-256 | Audit |",
            "| --- | --- | --- | --- | ---: | --- | --- |",
        ]
    )
    for artifact in manifest.artifacts:
        check = check_by_id.get(artifact.id)
        audit_status = check.status if check is not None else "not checked"
        lines.append(
            f"| {_markdown(artifact.id)} | {_markdown(artifact.role)} | "
            f"{_markdown(artifact.path_or_uri)} | {_markdown(artifact.media_type)} | "
            f"{artifact.size_bytes} | `{artifact.sha256}` | {audit_status} |"
        )
    if not manifest.artifacts:
        lines.append("| _none_ |  |  |  |  |  |  |")

    lines.extend(
        [
            "",
            "## Validation evidence",
            "",
            "| Check | Validator | Status | Measured value | Unit | Raw output |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for result in manifest.validation_results:
        measured = (
            "not recorded" if result.measured_value is None else _json_value(result.measured_value)
        )
        validator = f"{_markdown(result.validator)} {_markdown(result.validator_version)}"
        lines.append(
            f"| {_markdown(result.check_id)} | {validator} | **{result.status}** | "
            f"{_markdown(measured)} | "
            f"{_recorded(result.unit)} | {_markdown(result.raw_output_artifact_id)} |"
        )
        lines.append(f"- **{_markdown(result.check_id)}**: {_markdown(result.explanation)}")
        lines.append(
            f"  Configuration: `{_markdown(_json_value(result.threshold_or_configuration))}`; "
            f"input artifact: `{_markdown(result.input_artifact_id)}`."
        )
    if not manifest.validation_results:
        lines.append("| _none_ |  |  |  |  |  |")

    lines.extend(["", "## Licenses", ""])
    if manifest.licenses:
        for license_metadata in manifest.licenses:
            identity = license_metadata.identifier or license_metadata.name or "not recorded"
            acknowledgement = str(license_metadata.acknowledgement_required).lower()
            lines.append(
                f"- {_markdown(license_metadata.component)}: {_markdown(identity)}; "
                f"acknowledgement required: {acknowledgement}."
            )
    else:
        lines.append("- No license metadata was recorded; review provenance warnings.")

    lines.extend(
        [
            "",
            "## Scientific caveats",
            "",
            "- A predicted pose is not an experimental structure.",
            "- Pose confidence is not binding affinity, and predicted affinity is not "
            "measured affinity.",
            "- Model output alone does not establish biological activity, selectivity, "
            "safety, synthesizability, or clinical value.",
            "- Validation results are evidence; failures remain visible and require expert "
            "interpretation.",
            "- This report defines no universal ranking across prediction types.",
            "",
        ]
    )
    return "\n".join(lines)
