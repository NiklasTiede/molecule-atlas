from importlib import import_module
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Protocol, cast

from molecule_atlas.evidence.validation.contracts import (
    PoseBustersCompatibilityError,
    PoseBustersExecutionError,
    PoseBustersExecutionRequest,
    PoseBustersNormalizationRequest,
    PoseBustersNormalizationResult,
    PoseBustersUnavailableError,
)
from molecule_atlas.evidence.validation.normalization import normalize_posebusters_report

_VALIDATOR_VERSION = "0.6.5"


class _TabularReport(Protocol):
    def to_csv(self, *, index: bool, lineterminator: str) -> str: ...


class _PoseBustersInstance(Protocol):
    def bust(
        self,
        mol_pred: Path,
        mol_true: Path | None = None,
        mol_cond: Path | None = None,
        *,
        full_report: bool,
    ) -> _TabularReport: ...


class _PoseBustersFactory(Protocol):
    def __call__(self, *, config: str, max_workers: int) -> _PoseBustersInstance: ...


def _installed_version() -> str:
    try:
        return version("posebusters")
    except PackageNotFoundError as error:
        raise PoseBustersUnavailableError(
            "PoseBusters execution requires the optional 'posebusters' extra"
        ) from error


def _load_factory() -> _PoseBustersFactory:
    try:
        module = import_module("posebusters")
        factory = module.PoseBusters
    except (ImportError, AttributeError) as error:
        raise PoseBustersUnavailableError(
            "PoseBusters execution requires the optional 'posebusters' extra"
        ) from error
    return cast(_PoseBustersFactory, factory)


def _validate_paths(request: PoseBustersExecutionRequest) -> None:
    for label, path in (
        ("mol_pred", request.mol_pred),
        ("mol_true", request.mol_true),
        ("mol_cond", request.mol_cond),
    ):
        if path is not None and not path.is_file():
            raise PoseBustersExecutionError(f"PoseBusters {label} does not exist: {path}")
    if not request.artifact_root.is_dir():
        raise PoseBustersExecutionError(
            f"PoseBusters artifact root is not a directory: {request.artifact_root}"
        )
    report_path = request.report_path.resolve()
    if not report_path.is_relative_to(request.artifact_root.resolve()):
        raise PoseBustersExecutionError("PoseBusters report path must be inside artifact_root")
    if not request.report_path.parent.is_dir():
        raise PoseBustersExecutionError(
            f"PoseBusters report parent does not exist: {request.report_path.parent}"
        )


def run_posebusters(
    request: PoseBustersExecutionRequest,
) -> PoseBustersNormalizationResult:
    """Run the optional validator locally and normalize its deterministic full report."""

    _validate_paths(request)
    installed_version = _installed_version()
    if installed_version != _VALIDATOR_VERSION:
        raise PoseBustersCompatibilityError(
            f"PoseBusters execution supports exactly {_VALIDATOR_VERSION}; "
            f"installed {installed_version}"
        )
    factory = _load_factory()
    try:
        validator = factory(config=request.config, max_workers=0)
        report = validator.bust(
            request.mol_pred,
            mol_true=request.mol_true,
            mol_cond=request.mol_cond,
            full_report=True,
        )
        csv_text = report.to_csv(index=True, lineterminator="\n")
        request.report_path.write_text(csv_text, encoding="utf-8", newline="")
    except (OSError, UnicodeError) as error:
        raise PoseBustersExecutionError(
            f"Could not write PoseBusters full report: {error}"
        ) from error
    except Exception as error:
        raise PoseBustersExecutionError(f"PoseBusters validation failed: {error}") from error

    return normalize_posebusters_report(
        PoseBustersNormalizationRequest(
            report_path=request.report_path,
            artifact_root=request.artifact_root,
            input_artifact_id=request.input_artifact_id,
            raw_output_artifact_id=request.raw_output_artifact_id,
            validator_version=installed_version,
            config=request.config,
        )
    )
