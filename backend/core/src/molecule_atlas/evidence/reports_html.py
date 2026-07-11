import json
from datetime import datetime
from html import escape

from molecule_atlas.evidence.artifacts import ArtifactCheck
from molecule_atlas.evidence.models import Prediction, RunManifest

_PREDICTION_LABELS = {
    "docking_energy": "Docking energy",
    "pose_confidence": "Pose confidence",
    "structure_confidence": "Structure confidence",
    "binder_probability": "Binder probability",
    "predicted_affinity": "Predicted affinity",
}

_STYLES = """
:root { color-scheme: light dark; font-family: system-ui, sans-serif; line-height: 1.5; }
body { margin: 0 auto; max-width: 76rem; padding: 2rem; }
h1, h2, h3 { line-height: 1.2; }
section { border-top: 1px solid #8886; margin-top: 2rem; padding-top: 1rem; }
.notice { border-left: .3rem solid #b7791f; padding: .75rem 1rem; background: #b7791f18; }
.state { font-weight: 700; text-transform: uppercase; }
.prediction { border: 1px solid #8886; border-radius: .4rem; margin: 1rem 0; padding: 1rem; }
.caveat, .warning, .failure { color: #a33; }
dl { display: grid; grid-template-columns: minmax(10rem, 16rem) 1fr; gap: .35rem 1rem; }
dt { font-weight: 650; }
dd { margin: 0; overflow-wrap: anywhere; }
table { border-collapse: collapse; display: block; overflow-x: auto; width: 100%; }
th, td { border: 1px solid #8886; padding: .45rem .6rem; text-align: left; vertical-align: top; }
th { background: #8882; }
code { overflow-wrap: anywhere; }
""".strip()


def _text(value: object) -> str:
    return escape(str(value), quote=True)


def _recorded(value: str | None) -> str:
    return _text(value) if value is not None else "<em>not recorded</em>"


def _timestamp(value: datetime | None) -> str:
    return _text(value.isoformat()) if value is not None else "<em>not recorded</em>"


def _number(value: float) -> str:
    return format(value, ".15g")


def _prediction_value(prediction: Prediction) -> str:
    unit = f" {prediction.unit}" if prediction.unit is not None else ""
    return _text(f"{_number(prediction.value)}{unit}")


def _json_value(value: object) -> str:
    return _text(
        json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    )


def _definition(term: str, description: str) -> str:
    return f"<dt>{_text(term)}</dt><dd>{description}</dd>"


def render_html_report(
    manifest: RunManifest,
    *,
    artifact_checks: tuple[ArtifactCheck, ...] = (),
) -> str:
    """Render a deterministic, escaped, self-contained scientific evidence report."""

    run = manifest.run
    lines = [
        "<!doctype html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>Molecule Atlas Evidence Report — {_text(run.id)}</title>",
        f"<style>{_STYLES}</style>",
        "</head>",
        f'<body data-state="{_text(run.state)}">',
        "<main>",
        "<h1>Molecule Atlas Evidence Report</h1>",
        '<p class="notice">Computational predictions and validation checks are evidence for '
        "expert review, not experimental conclusions.</p>",
        '<section id="run">',
        "<h2>Run</h2>",
        "<dl>",
        _definition("Run ID", f"<code>{_text(run.id)}</code>"),
        _definition("Schema version", f"<code>{_text(manifest.schema_version)}</code>"),
        _definition("State", f'<span class="state">{_text(run.state)}</span>'),
        _definition("Started", _timestamp(run.started_at)),
        _definition("Finished", _timestamp(run.finished_at)),
    ]
    if run.expected_outputs:
        lines.append(_definition("Expected outputs", ", ".join(map(_text, run.expected_outputs))))
    if run.missing_outputs:
        lines.append(
            _definition(
                "Missing expected outputs",
                f'<strong class="failure">{", ".join(map(_text, run.missing_outputs))}</strong>',
            )
        )
    if run.failure is not None:
        failure = run.failure
        lines.extend(
            (
                _definition("Failure category", f"<code>{_text(failure.category)}</code>"),
                _definition("Failure stage", _recorded(failure.stage)),
                _definition(
                    "Failure message",
                    f'<strong class="failure">{_text(failure.message)}</strong>',
                ),
            )
        )
        if failure.exit_code is not None:
            lines.append(_definition("Exit code", f"<code>{failure.exit_code}</code>"))
        if failure.details:
            lines.append(
                _definition("Failure details", f"<code>{_json_value(failure.details)}</code>")
            )
    lines.extend(("</dl>", "</section>"))

    method = manifest.method
    command = " ".join(map(_text, method.command)) if method.command else "<em>not recorded</em>"
    random_seeds = (
        ", ".join(map(str, method.random_seeds)) if method.random_seeds else "<em>not recorded</em>"
    )
    lines.extend(
        (
            '<section id="method">',
            "<h2>Method identity</h2>",
            "<dl>",
            _definition("Method reference", f"<code>{_text(method.id)}</code>"),
            _definition(
                "Adapter",
                f"<code>{_text(method.adapter_id)}</code> "
                f"<code>{_text(method.adapter_version)}</code>",
            ),
            _definition("Upstream tool", _recorded(method.upstream_tool)),
            _definition("Upstream version", _recorded(method.upstream_version)),
            _definition("Source commit", _recorded(method.source_commit)),
            _definition("Checkpoint", _recorded(method.checkpoint_id)),
            _definition("Checkpoint SHA-256", _recorded(method.checkpoint_sha256)),
            _definition("Container image", _recorded(method.container_image)),
            _definition("Container digest", _recorded(method.container_digest)),
            _definition("Command", command),
            _definition("Random seeds", random_seeds),
            "</dl>",
            "</section>",
            '<section id="warnings">',
            "<h2>Provenance warnings</h2>",
        )
    )
    if manifest.warnings:
        lines.append("<ul>")
        lines.extend(
            f'<li class="warning"><code>{_text(warning.code)}</code> '
            f"({_text(warning.path)}): {_text(warning.message)}</li>"
            for warning in manifest.warnings
        )
        lines.append("</ul>")
    else:
        lines.append("<p>None recorded.</p>")
    lines.append("</section>")

    lines.extend(('<section id="predictions">', "<h2>Typed predictions</h2>"))
    if not manifest.predictions:
        lines.append("<p>No normalized predictions were recorded.</p>")
    for prediction in manifest.predictions:
        label = _PREDICTION_LABELS[prediction.type]
        direction = prediction.optimization_direction.replace("_", " ")
        lines.extend(
            (
                f'<article class="prediction" data-prediction-type="{_text(prediction.type)}">',
                f"<h3>{_text(label)}: <code>{_text(prediction.id)}</code></h3>",
                "<dl>",
                _definition("Value", f"<strong>{_prediction_value(prediction)}</strong>"),
                _definition("Optimization direction", _text(direction)),
                _definition(
                    "Scope",
                    f"<code>{_text(prediction.scope)}</code> / "
                    f"<code>{_text(prediction.scope_id)}</code>",
                ),
                _definition("Method reference", f"<code>{_text(prediction.method_id)}</code>"),
                _definition(
                    "Raw source",
                    f"{_text(prediction.raw_source.artifact_id)} / "
                    f"<code>{_text(prediction.raw_source.field)}</code>",
                ),
                _definition("Interpretation", _text(prediction.interpretation)),
            )
        )
        if prediction.uncertainty is not None:
            uncertainty = prediction.uncertainty
            unit = f" {uncertainty.unit}" if uncertainty.unit is not None else ""
            lines.append(
                _definition(
                    "Uncertainty",
                    _text(f"{_number(uncertainty.value)}{unit} ({uncertainty.kind})"),
                )
            )
        for caveat in prediction.caveats:
            lines.append(_definition("Caveat", f'<span class="caveat">{_text(caveat)}</span>'))
        lines.extend(("</dl>", "</article>"))
    lines.append("</section>")

    check_by_id = {check.artifact_id: check for check in artifact_checks}
    lines.extend(
        (
            '<section id="artifacts">',
            "<h2>Artifact inventory</h2>",
            "<table>",
            "<thead><tr><th>ID</th><th>Role</th><th>Path or URI</th><th>Media type</th>"
            "<th>Bytes</th><th>SHA-256</th><th>Audit</th></tr></thead>",
            "<tbody>",
        )
    )
    for artifact in manifest.artifacts:
        check = check_by_id.get(artifact.id)
        audit_status = check.status if check is not None else "not checked"
        lines.append(
            f"<tr><td>{_text(artifact.id)}</td><td>{_text(artifact.role)}</td>"
            f"<td>{_text(artifact.path_or_uri)}</td><td>{_text(artifact.media_type)}</td>"
            f"<td>{artifact.size_bytes}</td><td><code>{artifact.sha256}</code></td>"
            f"<td>{_text(audit_status)}</td></tr>"
        )
    if not manifest.artifacts:
        lines.append('<tr><td colspan="7"><em>none</em></td></tr>')
    lines.extend(("</tbody>", "</table>", "</section>"))

    lines.extend(
        (
            '<section id="validation">',
            "<h2>Validation evidence</h2>",
            "<table>",
            "<thead><tr><th>Check</th><th>Validator</th><th>Status</th>"
            "<th>Measured value</th><th>Unit</th><th>Raw output</th></tr></thead>",
            "<tbody>",
        )
    )
    for result in manifest.validation_results:
        measured = (
            "not recorded" if result.measured_value is None else _json_value(result.measured_value)
        )
        lines.append(
            f'<tr data-validation-status="{_text(result.status)}">'
            f"<td>{_text(result.check_id)}</td>"
            f"<td>{_text(result.validator)} {_text(result.validator_version)}</td>"
            f"<td><strong>{_text(result.status)}</strong></td><td>{measured}</td>"
            f"<td>{_recorded(result.unit)}</td><td>{_text(result.raw_output_artifact_id)}</td></tr>"
        )
        lines.append(
            f'<tr><td colspan="6"><strong>{_text(result.check_id)}</strong>: '
            f"{_text(result.explanation)} Configuration: "
            f"<code>{_json_value(result.threshold_or_configuration)}</code>; input artifact: "
            f"<code>{_text(result.input_artifact_id)}</code>.</td></tr>"
        )
    if not manifest.validation_results:
        lines.append('<tr><td colspan="6"><em>none</em></td></tr>')
    lines.extend(("</tbody>", "</table>", "</section>"))

    lines.extend(('<section id="licenses">', "<h2>Licenses</h2>"))
    if manifest.licenses:
        lines.append("<ul>")
        for license_metadata in manifest.licenses:
            identity = license_metadata.identifier or license_metadata.name or "not recorded"
            acknowledgement = str(license_metadata.acknowledgement_required).lower()
            lines.append(
                f"<li>{_text(license_metadata.component)}: {_text(identity)}; "
                f"acknowledgement required: {acknowledgement}.</li>"
            )
        lines.append("</ul>")
    else:
        lines.append("<p>No license metadata was recorded; review provenance warnings.</p>")
    lines.append("</section>")

    lines.extend(
        (
            '<section id="scientific-caveats">',
            "<h2>Scientific caveats</h2>",
            "<ul>",
            "<li>A predicted pose is not an experimental structure.</li>",
            "<li>Pose confidence is not binding affinity, and predicted affinity is not measured "
            "affinity.</li>",
            "<li>Model output alone does not establish biological activity, selectivity, safety, "
            "synthesizability, or clinical value.</li>",
            "<li>Validation results are evidence; failures remain visible and require expert "
            "interpretation.</li>",
            "<li>This report defines no universal ranking across prediction types.</li>",
            "</ul>",
            "</section>",
            "</main>",
            "</body>",
            "</html>",
            "",
        )
    )
    return "\n".join(lines)
