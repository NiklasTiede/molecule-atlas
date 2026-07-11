from pathlib import Path

from molecule_atlas.evidence import (
    AdapterImportRequest,
    ManifestWarning,
    audit_manifest,
    load_manifest,
    render_html_report,
)
from molecule_atlas.evidence.adapters.boltz import BoltzAdapter
from molecule_atlas.evidence.adapters.diffdock import DiffDockAdapter

FIXTURE_ROOT = Path("../data/evidence-fixtures")


def test_html_report_is_deterministic_self_contained_and_complete() -> None:
    manifest = load_manifest(FIXTURE_ROOT / "succeeded/molecule-atlas-run.json")
    artifact_checks = audit_manifest(
        manifest,
        root=FIXTURE_ROOT / "succeeded",
    ).artifact_checks

    report = render_html_report(manifest, artifact_checks=artifact_checks)

    assert report == render_html_report(manifest, artifact_checks=artifact_checks)
    assert report.startswith("<!doctype html>\n")
    assert '<meta charset="utf-8">' in report
    assert "<style>" in report
    assert "<script" not in report.lower()
    assert 'src="http' not in report.lower()
    assert 'href="http' not in report.lower()
    assert "fixture-succeeded" in report
    assert "Docking energy" in report
    assert "Binder probability" in report
    assert "Validation evidence" in report
    assert "minimum_distance" in report
    assert "verified" in report
    assert "universal ranking" in report


def test_html_report_exposes_partial_and_failed_runs() -> None:
    partial = render_html_report(load_manifest(FIXTURE_ROOT / "partial/molecule-atlas-run.json"))
    failed = render_html_report(load_manifest(FIXTURE_ROOT / "failed/molecule-atlas-run.json"))

    assert 'data-state="partial"' in partial
    assert "Missing expected outputs" in partial
    assert "predicted complex" in partial
    assert 'data-state="failed"' in failed
    assert "Synthetic upstream failure" in failed
    assert "upstream_error" in failed


def test_html_report_escapes_all_manifest_text() -> None:
    manifest = load_manifest(FIXTURE_ROOT / "succeeded/molecule-atlas-run.json")
    unsafe = manifest.model_copy(
        update={
            "warnings": (
                *manifest.warnings,
                ManifestWarning(
                    code="unsafe_markup",
                    message='<script>alert("unsafe")</script>',
                    path="warnings.<unsafe>",
                ),
            )
        }
    )

    report = render_html_report(unsafe)

    assert '<script>alert("unsafe")</script>' not in report
    assert "&lt;script&gt;alert(&quot;unsafe&quot;)&lt;/script&gt;" in report
    assert "warnings.&lt;unsafe&gt;" in report


def test_html_report_keeps_model_family_prediction_semantics_distinct() -> None:
    boltz = BoltzAdapter().import_evidence(
        AdapterImportRequest(source_path=FIXTURE_ROOT / "boltz-2.2.1/documented-layout")
    )
    diffdock = DiffDockAdapter().import_evidence(
        AdapterImportRequest(source_path=FIXTURE_ROOT / "diffdock-1.1.3/documented-layout")
    )

    boltz_report = render_html_report(boltz.manifest)
    diffdock_report = render_html_report(diffdock.manifest)

    assert "Structure confidence" in boltz_report
    assert "Binder probability" in boltz_report
    assert "Predicted affinity" in boltz_report
    assert "log10(IC50/µM)" in boltz_report
    assert "Pose confidence" in diffdock_report
    assert "Predicted affinity" not in diffdock_report
    assert "not binding affinity" in diffdock_report
