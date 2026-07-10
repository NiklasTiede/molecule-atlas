from pathlib import Path

import pytest
from molecule_atlas.evidence.adapters import (
    AdapterImportRequest,
    AdapterImportResult,
    AdapterMetadata,
    EvidenceInputError,
    get_adapter,
    list_adapters,
)
from molecule_atlas.evidence.cli import main
from pydantic import ValidationError

FIXTURE_ROOT = Path("../data/evidence-fixtures")


def test_manifest_adapter_publishes_typed_compatibility_metadata() -> None:
    adapters = list_adapters()

    assert len(adapters) == 1
    metadata = adapters[0]
    assert metadata.adapter_id == "manifest"
    assert metadata.adapter_version == "0.1.0"
    assert metadata.upstream_tool is None
    assert metadata.source_format == "molecule-atlas-run-manifest"
    assert metadata.source_format_version == "0.1.0"
    assert metadata.verified_upstream_versions == ()
    assert metadata.supported_manifest_versions == ("0.1.0",)
    assert AdapterMetadata.model_validate_json(metadata.model_dump_json()) == metadata


def test_adapter_metadata_rejects_unknown_fields() -> None:
    payload: dict[str, object] = {
        "adapter_id": "fixture",
        "adapter_version": "0.1.0",
        "title": "Fixture",
        "description": "Fixture adapter metadata.",
        "upstream_tool": None,
        "source_format": "fixture-output",
        "source_format_version": "1",
        "verified_upstream_versions": (),
        "supported_manifest_versions": ("0.1.0",),
        "options": {},
    }

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        AdapterMetadata.model_validate(payload)


def test_adapter_metadata_requires_a_supported_manifest_version() -> None:
    with pytest.raises(ValidationError, match="at least 1 item"):
        AdapterMetadata(
            adapter_id="fixture",
            adapter_version="0.1.0",
            title="Fixture",
            description="Fixture adapter metadata.",
            upstream_tool=None,
            source_format="fixture-output",
            source_format_version="1",
            verified_upstream_versions=(),
            supported_manifest_versions=(),
        )


def test_adapter_request_rejects_unknown_contract_version() -> None:
    with pytest.raises(ValidationError, match=r"0\.1\.0"):
        AdapterImportRequest.model_validate(
            {
                "contract_version": "1.0.0",
                "source_path": FIXTURE_ROOT / "succeeded",
            }
        )


def test_manifest_adapter_returns_versioned_import_result() -> None:
    request = AdapterImportRequest(source_path=FIXTURE_ROOT / "succeeded")

    result = get_adapter("manifest").import_evidence(request)

    assert isinstance(result, AdapterImportResult)
    assert result.contract_version == "0.1.0"
    assert result.adapter_id == "manifest"
    assert result.adapter_version == "0.1.0"
    assert result.artifact_root == FIXTURE_ROOT / "succeeded"
    assert result.manifest.run.id == "fixture-succeeded"
    assert AdapterImportResult.model_validate_json(result.model_dump_json()) == result


def test_adapter_registry_rejects_unknown_adapter() -> None:
    with pytest.raises(EvidenceInputError, match="Unsupported adapter 'boltz'"):
        get_adapter("boltz")


def test_adapters_command_lists_verified_compatibility(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(["adapters"])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "manifest 0.1.0" in captured.out
    assert "molecule-atlas-run-manifest 0.1.0" in captured.out
    assert "Run manifests: 0.1.0" in captured.out
