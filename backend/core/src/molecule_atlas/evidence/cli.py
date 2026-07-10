import argparse
import sys
from collections import Counter
from collections.abc import Sequence
from pathlib import Path
from typing import cast

from molecule_atlas.evidence.adapters import EvidenceInputError, audit_path
from molecule_atlas.evidence.reports import render_markdown_report
from molecule_atlas.evidence.serialization import write_manifest, write_manifest_schema


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="molecule-atlas",
        description="Inspect and report portable Molecule Atlas evidence manifests.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    inspect_parser = commands.add_parser("inspect", help="Validate and summarize a run manifest")
    inspect_parser.add_argument("path", type=Path)

    audit_parser = commands.add_parser(
        "audit",
        help="Audit artifact hashes and write a canonical manifest",
    )
    audit_parser.add_argument("path", type=Path)
    audit_parser.add_argument("--adapter", required=True)
    audit_parser.add_argument("--output", required=True, type=Path)

    report_parser = commands.add_parser("report", help="Render a run report")
    report_parser.add_argument("manifest", type=Path)
    report_parser.add_argument("--format", choices=("markdown",), required=True)
    report_parser.add_argument("--output", type=Path)

    schema_parser = commands.add_parser("schema", help="Export the RunManifest JSON Schema")
    schema_parser.add_argument("--output", required=True, type=Path)
    return parser


def _inspect(path: Path) -> None:
    audit = audit_path(path)
    manifest = audit.manifest
    verified = sum(check.status == "verified" for check in audit.artifact_checks)
    prediction_counts = Counter(prediction.type for prediction in manifest.predictions)
    validation_counts = Counter(result.status for result in manifest.validation_results)
    predictions = ", ".join(
        f"{prediction_type}={count}" for prediction_type, count in sorted(prediction_counts.items())
    )
    validations = ", ".join(
        f"{status}={count}" for status, count in sorted(validation_counts.items())
    )
    print(f"Run: {manifest.run.id}")
    print(f"State: {manifest.run.state}")
    print(f"Schema: {manifest.schema_version}")
    print(
        f"Method: {manifest.method.upstream_tool or 'not recorded'} "
        f"(adapter {manifest.method.adapter_id} {manifest.method.adapter_version})"
    )
    print(f"Artifacts: {len(manifest.artifacts)} ({verified} verified)")
    print(f"Predictions: {predictions or 'none'}")
    print(f"Validation: {validations or 'none'}")
    print(f"Warnings: {len(manifest.warnings)}")
    for warning in manifest.warnings:
        print(f"- {warning.code}: {warning.message}")


def _audit(path: Path, adapter: str, output: Path) -> None:
    audit = audit_path(path, adapter=adapter)
    write_manifest(output, audit.manifest)
    print(f"Wrote canonical audited manifest: {output}")


def _report(manifest_path: Path, output: Path | None) -> None:
    audit = audit_path(manifest_path)
    report = render_markdown_report(
        audit.manifest,
        artifact_checks=audit.artifact_checks,
    )
    if output is None:
        print(report, end="")
        return
    output.write_text(report, encoding="utf-8")
    print(f"Wrote markdown report: {output}")


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    command = cast(str, args.command)
    try:
        if command == "inspect":
            _inspect(cast(Path, args.path))
        elif command == "audit":
            _audit(
                cast(Path, args.path),
                cast(str, args.adapter),
                cast(Path, args.output),
            )
        elif command == "report":
            _report(cast(Path, args.manifest), cast(Path | None, args.output))
        elif command == "schema":
            output = cast(Path, args.output)
            write_manifest_schema(output)
            print(f"Wrote RunManifest JSON Schema: {output}")
        else:
            raise AssertionError(f"Unhandled command: {command}")
    except (EvidenceInputError, OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
