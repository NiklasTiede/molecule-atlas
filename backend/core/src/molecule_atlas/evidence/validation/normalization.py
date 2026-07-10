import csv
import math
from dataclasses import dataclass
from pathlib import Path

from pydantic import JsonValue

from molecule_atlas.evidence.artifacts import inventory_artifact
from molecule_atlas.evidence.models import ManifestWarning, ValidationResult, ValidationStatus
from molecule_atlas.evidence.semantic_artifacts import SemanticArtifact
from molecule_atlas.evidence.validation.contracts import (
    PoseBustersCompatibilityError,
    PoseBustersNormalizationRequest,
    PoseBustersNormalizationResult,
    ValidationInputError,
    ValidatorMetadata,
)

_VALIDATOR_VERSION = "0.6.5"
_INTEGRATION_VERSION = "0.1.0"
_IDENTIFIER_COLUMNS = frozenset({"file", "molecule", "position"})


@dataclass(frozen=True)
class _CheckMapping:
    column: str
    label: str
    measured_column: str | None = None
    unit: str | None = None
    configuration: tuple[tuple[str, JsonValue], ...] = ()


_MOL_CHECKS = (
    _CheckMapping("mol_pred_loaded", "predicted molecule loading"),
    _CheckMapping("sanitization", "RDKit sanitization"),
    _CheckMapping("inchi_convertible", "InChI conversion"),
    _CheckMapping("all_atoms_connected", "atom connectivity"),
    _CheckMapping("no_radicals", "absence of radicals"),
    _CheckMapping("bond_lengths", "bond-length geometry"),
    _CheckMapping("bond_angles", "bond-angle geometry"),
    _CheckMapping("internal_steric_clash", "absence of internal steric clashes"),
    _CheckMapping("aromatic_ring_flatness", "aromatic-ring flatness"),
    _CheckMapping(
        "non-aromatic_ring_non-flatness",
        "non-aromatic-ring non-flatness",
    ),
    _CheckMapping("double_bond_flatness", "double-bond flatness"),
    _CheckMapping(
        "internal_energy",
        "internal-energy ratio",
        measured_column="energy_ratio",
        unit="ratio",
        configuration=(("maximum_energy_ratio", 100.0),),
    ),
)

_DOCK_CHECKS = (
    _CheckMapping("mol_cond_loaded", "conditioning structure loading"),
    _CheckMapping(
        "protein-ligand_maximum_distance",
        "maximum protein-ligand distance",
        measured_column="smallest_distance_protein",
        unit="angstrom",
        configuration=(("maximum_distance_angstrom", 5.0),),
    ),
    _CheckMapping(
        "minimum_distance_to_protein",
        "minimum distance to protein",
        measured_column="smallest_distance_protein",
        unit="angstrom",
        configuration=(("relative_distance_clash_cutoff", 0.75),),
    ),
    _CheckMapping(
        "minimum_distance_to_organic_cofactors",
        "minimum distance to organic cofactors",
    ),
    _CheckMapping(
        "minimum_distance_to_inorganic_cofactors",
        "minimum distance to inorganic cofactors",
    ),
    _CheckMapping("minimum_distance_to_waters", "minimum distance to waters"),
    _CheckMapping(
        "volume_overlap_with_protein",
        "volume overlap with protein",
        measured_column="volume_overlap_protein",
        unit="fraction",
        configuration=(("maximum_volume_overlap_fraction", 0.075),),
    ),
    _CheckMapping(
        "volume_overlap_with_organic_cofactors",
        "volume overlap with organic cofactors",
    ),
    _CheckMapping(
        "volume_overlap_with_inorganic_cofactors",
        "volume overlap with inorganic cofactors",
    ),
    _CheckMapping("volume_overlap_with_waters", "volume overlap with waters"),
)

_REDOCK_CHECKS = (
    _CheckMapping("mol_true_loaded", "reference ligand loading"),
    _CheckMapping("molecular_formula", "molecular-formula identity"),
    _CheckMapping("molecular_bonds", "molecular-bond identity"),
    _CheckMapping("double_bond_stereochemistry", "double-bond stereochemistry identity"),
    _CheckMapping("tetrahedral_chirality", "tetrahedral-chirality identity"),
    _CheckMapping(
        "rmsd_≤_2å",
        "heavy-atom RMSD threshold",
        measured_column="rmsd",
        unit="angstrom",
        configuration=(("maximum_rmsd_angstrom", 2.0),),
    ),
)

# PoseBusters full_report=True deliberately includes diagnostic values beyond the chosen binary
# tests. They remain in the raw artifact even where the normalized contract has no stable semantic
# mapping yet. Listing the verified 0.6.5 columns prevents expected diagnostics from being
# mislabeled as upstream schema drift.
_KNOWN_MOL_DIAGNOSTICS = frozenset(
    {
        "mol_true_loaded",
        "mol_cond_loaded",
        "passes_valence_checks",
        "passes_kekulization",
        "no_radicals_before_sanitization",
        "number_bonds",
        "shortest_bond_relative_length",
        "longest_bond_relative_length",
        "number_short_outlier_bonds",
        "number_long_outlier_bonds",
        "number_angles",
        "most_extreme_relative_angle",
        "number_outlier_angles",
        "number_noncov_pairs",
        "shortest_noncovalent_relative_distance",
        "number_clashes",
        "number_valid_bonds",
        "number_valid_angles",
        "number_valid_noncov_pairs",
        "number_aromatic_rings_checked",
        "number_aromatic_rings_pass",
        "aromatic_ring_maximum_distance_from_plane",
        "number_non-aromatic_rings_checked",
        "number_non-aromatic_rings_pass",
        "non-aromatic_ring_maximum_distance_from_plane",
        "number_double_bonds_checked",
        "number_double_bonds_pass",
        "double_bond_maximum_distance_from_plane",
        "num_h_added",
        "mol_pred_energy",
        "ensemble_avg_energy",
        "energy_ratio",
        "smallest_distance_protein",
        "num_pairwise_clashes_protein",
        "volume_overlap_protein",
        "smallest_distance_organic_cofactors",
        "num_pairwise_clashes_organic_cofactors",
        "volume_overlap_organic_cofactors",
        "smallest_distance_inorganic_cofactors",
        "num_pairwise_clashes_inorganic_cofactors",
        "volume_overlap_inorganic_cofactors",
        "smallest_distance_waters",
        "num_pairwise_clashes_waters",
        "volume_overlap_waters",
        "rmsd",
        "kabsch_rmsd",
        "centroid_distance",
    }
)


def _checks_for_config(config: str) -> tuple[_CheckMapping, ...]:
    if config == "mol":
        return _MOL_CHECKS
    if config == "dock":
        return (*_MOL_CHECKS, *_DOCK_CHECKS)
    return (*_MOL_CHECKS, *_DOCK_CHECKS, *_REDOCK_CHECKS)


def posebusters_metadata() -> ValidatorMetadata:
    """Return pinned compatibility without importing the optional upstream package."""

    return ValidatorMetadata(
        validator_id="posebusters",
        integration_version=_INTEGRATION_VERSION,
        upstream_tool="PoseBusters",
        verified_upstream_versions=(_VALIDATOR_VERSION,),
        configurations=("mol", "dock", "redock"),
        optional_dependency=f"posebusters=={_VALIDATOR_VERSION}",
    )


def _read_report(path: Path) -> tuple[tuple[str, ...], tuple[dict[str, str], ...]]:
    try:
        with path.open(newline="", encoding="utf-8") as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames is None:
                raise ValidationInputError(f"PoseBusters report has no header: {path}")
            fieldnames = tuple(reader.fieldnames)
            if len(fieldnames) != len(set(fieldnames)):
                raise ValidationInputError(f"PoseBusters report repeats columns: {path}")
            rows = tuple(dict(row) for row in reader)
    except (OSError, UnicodeError, csv.Error) as error:
        raise ValidationInputError(f"Could not read PoseBusters report {path}: {error}") from error
    if not rows:
        raise ValidationInputError(f"PoseBusters report has no result rows: {path}")
    missing_identifiers = _IDENTIFIER_COLUMNS - set(fieldnames)
    if missing_identifiers:
        raise ValidationInputError(
            "PoseBusters report is missing identifier columns: "
            f"{', '.join(sorted(missing_identifiers))}"
        )
    if any(None in row for row in rows):
        raise ValidationInputError(
            f"PoseBusters report contains rows wider than its header: {path}"
        )
    return fieldnames, rows


def _boolean_status(value: str) -> tuple[ValidationStatus, bool | str | None]:
    normalized = value.strip().lower()
    if normalized == "true":
        return "pass", True
    if normalized == "false":
        return "fail", False
    if not normalized:
        return "unavailable", None
    return "error", value


def _measured_value(
    row: dict[str, str],
    mapping: _CheckMapping,
) -> tuple[float | None, bool]:
    if mapping.measured_column is None:
        return None, True
    raw_value = row.get(mapping.measured_column, "").strip()
    if not raw_value:
        return None, True
    try:
        value = float(raw_value)
    except ValueError:
        return None, False
    return (value, True) if math.isfinite(value) else (None, True)


def _explanation(label: str, status: ValidationStatus) -> str:
    if status == "pass":
        return f"PoseBusters reported that {label} passed."
    if status == "fail":
        return f"PoseBusters reported that {label} failed."
    if status == "unavailable":
        return f"PoseBusters did not return an available result for {label}."
    return f"PoseBusters returned an invalid value for {label}; inspect the raw report."


def normalize_posebusters_report(
    request: PoseBustersNormalizationRequest,
) -> PoseBustersNormalizationResult:
    """Normalize a captured full report while retaining all upstream CSV bytes."""

    if request.validator_version != _VALIDATOR_VERSION:
        raise PoseBustersCompatibilityError(
            f"PoseBusters integration supports exactly {_VALIDATOR_VERSION}; "
            f"received {request.validator_version}"
        )
    fieldnames, rows = _read_report(request.report_path)
    raw_artifact = inventory_artifact(
        request.report_path,
        root=request.artifact_root,
        artifact_id=request.raw_output_artifact_id,
        role="validation_output",
        media_type="text/csv",
        created_by_stage="posebusters_validation",
        metadata={
            "config": request.config,
            "full_report": True,
            "validator_version": request.validator_version,
        },
    )
    semantic_artifact = SemanticArtifact(
        artifact_id=raw_artifact.id,
        logical_name="posebusters_full_report",
        artifact_type="validation-report",
        schema_version=None,
        semantic_role="validation_output",
        media_type=raw_artifact.media_type,
        path_or_uri=raw_artifact.path_or_uri,
        content_digest=f"sha256:{raw_artifact.sha256}",
        size_bytes=raw_artifact.size_bytes,
        derived_from_artifact_ids=(),
        domain_metadata={
            "config": request.config,
            "input_artifact_id": request.input_artifact_id,
            "validator_version": request.validator_version,
        },
        preview_metadata={},
    )

    mappings = _checks_for_config(request.config)
    mapped_columns = {mapping.column for mapping in mappings}
    known_columns = _IDENTIFIER_COLUMNS | mapped_columns | _KNOWN_MOL_DIAGNOSTICS
    unknown_columns = tuple(sorted(set(fieldnames) - known_columns))
    missing_columns = tuple(sorted(mapped_columns - set(fieldnames)))
    warnings: list[ManifestWarning] = []
    if unknown_columns:
        warnings.append(
            ManifestWarning(
                code="posebusters_unknown_columns",
                message=(
                    "Unmapped PoseBusters columns remain in the raw report: "
                    f"{', '.join(unknown_columns)}"
                ),
                path=raw_artifact.path_or_uri,
            )
        )
    if missing_columns:
        warnings.append(
            ManifestWarning(
                code="posebusters_missing_columns",
                message=(
                    "Expected PoseBusters columns are absent and normalize as unavailable: "
                    f"{', '.join(missing_columns)}"
                ),
                path=raw_artifact.path_or_uri,
            )
        )

    results: list[ValidationResult] = []
    for row_index, row in enumerate(rows):
        position = row.get("position", "").strip() or str(row_index)
        for mapping in mappings:
            status, boolean_value = _boolean_status(row.get(mapping.column, ""))
            measured_value, measurement_valid = _measured_value(row, mapping)
            if not measurement_valid:
                status = "error"
            if mapping.measured_column is None:
                normalized_value: bool | int | float | str | None = boolean_value
            else:
                normalized_value = measured_value
            configuration: dict[str, JsonValue] = {
                "config": request.config,
                **dict(mapping.configuration),
            }
            results.append(
                ValidationResult(
                    id=f"posebusters-{position}-{mapping.column}",
                    validator="PoseBusters",
                    validator_version=request.validator_version,
                    check_id=mapping.column,
                    status=status,
                    measured_value=normalized_value,
                    unit=mapping.unit,
                    threshold_or_configuration=configuration,
                    explanation=_explanation(mapping.label, status),
                    input_artifact_id=request.input_artifact_id,
                    raw_output_artifact_id=raw_artifact.id,
                )
            )

    return PoseBustersNormalizationResult(
        validator_version=request.validator_version,
        config=request.config,
        artifact_root=request.artifact_root,
        raw_report_artifact=raw_artifact,
        semantic_artifact=semantic_artifact,
        validation_results=tuple(results),
        warnings=tuple(warnings),
    )
