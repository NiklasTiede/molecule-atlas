import stat
from collections.abc import Callable
from pathlib import Path
from zipfile import ZipInfo

import pytest
from pydantic import ValidationError

from app.application.capabilities.models import ActorContext, CapabilityContext
from app.application.evidence.contracts import (
    MAX_EVIDENCE_BUNDLE_BYTES,
    GetRunSummaryInput,
    ImportEvidenceBundleInput,
)
from app.application.evidence.import_bundle import ImportEvidenceBundleCapability
from app.application.evidence.ports import (
    EvidenceBundleConflictError,
    EvidenceBundleInputError,
    EvidenceBundleLimitError,
)
from app.application.evidence.run_summary import GetRunSummaryCapability
from app.infrastructure.evidence.local_repository import LocalEvidenceRunRepository
from tests.evidence_bundle_factory import evidence_bundle_bytes

FIXTURE_ROOT = Path(__file__).parents[2] / "data" / "evidence-fixtures"


def _symbolic_link_info() -> ZipInfo:
    info = ZipInfo("artifacts/unsafe-link")
    info.external_attr = (stat.S_IFLNK | 0o777) << 16
    return info


def _context() -> CapabilityContext:
    return CapabilityContext(
        actor=ActorContext(
            actor_id="test-suite",
            actor_type="service",
            permissions=("evidence:import", "evidence:read"),
        ),
        correlation_id="corr-import-test",
        causation_id=None,
    )


def _request(
    bundle: bytes,
    *,
    idempotency_key: str = "import-fixture-1",
) -> ImportEvidenceBundleInput:
    return ImportEvidenceBundleInput(
        archive_bytes=bundle,
        original_filename="evidence.zip",
        idempotency_key=idempotency_key,
    )


def test_import_bundle_publishes_audited_run_for_bounded_queries(tmp_path: Path) -> None:
    repository = LocalEvidenceRunRepository((), upload_root=tmp_path)
    capability = ImportEvidenceBundleCapability(repository)
    bundle = evidence_bundle_bytes(FIXTURE_ROOT / "succeeded")

    result = capability.execute(_request(bundle), context=_context())

    assert result.capability_id == "import_evidence_bundle"
    assert result.capability_version == "0.1.0"
    assert result.correlation_id == "corr-import-test"
    assert result.idempotency_replayed is False
    assert result.run.run_id == "fixture-succeeded"
    assert result.run.state == "succeeded"
    assert result.run.artifact_count == 4
    assert result.run.validation_counts.fail_count == 1
    assert len(tuple(tmp_path.iterdir())) == 1

    summary = GetRunSummaryCapability(repository).execute(
        request=GetRunSummaryInput(run_id=result.run.run_id),
        context=_context(),
    )
    assert summary.run == result.run


def test_import_bundle_preserves_partial_run_state(tmp_path: Path) -> None:
    capability = ImportEvidenceBundleCapability(
        LocalEvidenceRunRepository((), upload_root=tmp_path)
    )

    result = capability.execute(
        _request(evidence_bundle_bytes(FIXTURE_ROOT / "partial")),
        context=_context(),
    )

    assert result.run.state == "partial"
    assert result.run.missing_outputs == ("predicted complex",)


def test_import_bundle_replays_same_idempotency_key_without_duplicate_storage(
    tmp_path: Path,
) -> None:
    capability = ImportEvidenceBundleCapability(
        LocalEvidenceRunRepository((), upload_root=tmp_path)
    )
    request = _request(evidence_bundle_bytes(FIXTURE_ROOT / "succeeded"))

    first = capability.execute(request, context=_context())
    replay = capability.execute(request, context=_context())

    assert first.idempotency_replayed is False
    assert replay.idempotency_replayed is True
    assert replay.run == first.run
    assert len(tuple(tmp_path.iterdir())) == 1


def test_import_bundle_rejects_idempotency_key_reuse_for_different_bytes(
    tmp_path: Path,
) -> None:
    capability = ImportEvidenceBundleCapability(
        LocalEvidenceRunRepository((), upload_root=tmp_path)
    )
    capability.execute(
        _request(evidence_bundle_bytes(FIXTURE_ROOT / "succeeded")),
        context=_context(),
    )

    with pytest.raises(EvidenceBundleConflictError, match="different bundle"):
        capability.execute(
            _request(evidence_bundle_bytes(FIXTURE_ROOT / "partial")),
            context=_context(),
        )


@pytest.mark.parametrize(
    ("bundle", "message"),
    (
        (
            lambda: evidence_bundle_bytes(
                FIXTURE_ROOT / "succeeded",
                extra_members=(("../escape.txt", b"escape"),),
            ),
            "unsafe",
        ),
        (
            lambda: evidence_bundle_bytes(
                FIXTURE_ROOT / "succeeded",
                extra_members=((_symbolic_link_info(), b"target"),),
            ),
            "symbolic link",
        ),
        (
            lambda: evidence_bundle_bytes(
                FIXTURE_ROOT / "succeeded",
                extra_members=(("molecule-atlas-run.json", b"{}"),),
            ),
            "duplicate",
        ),
        (
            lambda: evidence_bundle_bytes(
                FIXTURE_ROOT / "succeeded",
                replacements={"molecule-atlas-run.json": b"{}"},
            ),
            "manifest validation failed",
        ),
        (
            lambda: evidence_bundle_bytes(
                FIXTURE_ROOT / "succeeded",
                omitted=frozenset({"artifacts/predicted-pose.sdf"}),
            ),
            "artifact validation failed",
        ),
        (
            lambda: evidence_bundle_bytes(
                FIXTURE_ROOT / "succeeded",
                replacements={"artifacts/predicted-pose.sdf": b"tampered"},
            ),
            "artifact validation failed",
        ),
    ),
)
def test_import_bundle_rejects_unsafe_or_inconsistent_archives(
    tmp_path: Path,
    bundle: Callable[[], bytes],
    message: str,
) -> None:
    capability = ImportEvidenceBundleCapability(
        LocalEvidenceRunRepository((), upload_root=tmp_path)
    )

    with pytest.raises(EvidenceBundleInputError, match=message):
        capability.execute(_request(bundle()), context=_context())

    assert tuple(tmp_path.iterdir()) == ()


def test_import_bundle_rejects_excessive_member_count(tmp_path: Path) -> None:
    extra_members = tuple((f"extra/{index}.txt", b"") for index in range(256))
    bundle = evidence_bundle_bytes(
        FIXTURE_ROOT / "succeeded",
        extra_members=extra_members,
    )
    capability = ImportEvidenceBundleCapability(
        LocalEvidenceRunRepository((), upload_root=tmp_path)
    )

    with pytest.raises(EvidenceBundleLimitError, match="too many members"):
        capability.execute(_request(bundle), context=_context())


def test_import_contract_rejects_archive_over_transport_limit() -> None:
    with pytest.raises(ValidationError):
        _request(b"x" * (MAX_EVIDENCE_BUNDLE_BYTES + 1))
