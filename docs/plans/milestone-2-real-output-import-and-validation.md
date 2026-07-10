# Milestone 2 Implementation Plan: Real-Output Import and Validation

- Status: In progress
- Current slice: Slice 1 implemented; Slice 2 next
- Roadmap milestone: 2 — Real-output import and validation
- Planning date: 2026-07-10

## Outcome

Molecule Atlas will import captured outputs from Boltz and DiffDock, normalize their scientifically
different predictions without flattening them, validate pose artifacts through PoseBusters, and
produce deterministic Markdown and HTML evidence reports. Normal CI will replay tiny checked-in
fixtures without executing a model, using a database, requiring a GPU, or accessing the network.

This milestone extends the portable evidence core. It does not add web import, FastAPI capabilities,
persistence, managed scientific execution, plugin containers, Kubernetes, or external inference.

## Fixed constraints

- Preserve `RunManifest` schema `0.1.0` and its checked-in JSON Schema unchanged.
- Introduce every new portable contract with an explicit contract and schema version.
- Keep the default `molecule-atlas-core` runtime dependent only on Pydantic and the standard library.
- Treat PoseBusters as an optional validation integration; importing the core must not import RDKit,
  Pandas, or PoseBusters.
- Preserve raw upstream files and point normalized values and checks back to raw artifacts and fields.
- Represent missing, partial, failed, and unsupported layouts explicitly.
- Never persist an unqualified `score`. DiffDock confidence is pose confidence; Boltz confidence,
  structure confidence, binder probability, and predicted affinity remain distinct.
- Do not infer tool versions, commands, checkpoints, seeds, or licenses from filenames. Missing
  provenance produces warnings.
- Keep fixture replay deterministic and offline. Live upstream execution is outside this milestone.

## Current baseline

The implemented core lives under `backend/core/src/molecule_atlas/evidence`. It currently provides:

- immutable strict Pydantic `RunManifest 0.1.0` contracts;
- local artifact hashing and verification;
- manifest-only audit through `molecule-atlas audit --adapter manifest`;
- canonical JSON and Markdown reports;
- synthetic succeeded, partial, and failed fixtures.

The first implementation slice converts the hard-coded manifest adapter branch into a concrete,
typed adapter boundary without changing manifest audit results.

## Upstream compatibility snapshot

Compatibility claims are exact and fixture-backed. A newer upstream release is unsupported until a
captured fixture proves its layout.

| Integration | Initial verified target | Relevant upstream contract | Scientific interpretation |
| --- | --- | --- | --- |
| Boltz | `2.2.1` | `predictions/<input>/`, model CIF/mmCIF, per-model confidence JSON, optional affinity JSON | `confidence_score` is structure/complex confidence; `affinity_probability_binary` is binder probability; `affinity_pred_value` is predicted `log10(IC50 in µM)` and not measured affinity |
| DiffDock | `1.1.3` | one directory per complex with ranked SDF files; confidence is encoded in names such as `rank1_confidence-0.42.sdf` | confidence represents confidence in the predicted binding structure, not binding affinity |
| PoseBusters | `0.6.5` | `PoseBusters.bust(..., full_report=True)` tabular output using a named configuration | each named check becomes validation evidence; a mixed result is not collapsed to one verdict |

Primary references:

- [Boltz 2.2.1 prediction and output documentation](https://github.com/jwohlwend/boltz/blob/v2.2.1/docs/prediction.md)
- [Boltz repository and license](https://github.com/jwohlwend/boltz)
- [DiffDock inference and interpretation documentation](https://github.com/gcorso/DiffDock)
- [DiffDock 1.1.3 release](https://github.com/gcorso/DiffDock/releases/tag/v1.1.3)
- [PoseBusters API documentation](https://posebusters.readthedocs.io/en/latest/api_notebook.html)
- [PoseBusters repository and license](https://github.com/maabuu/posebusters)

Before committing real-output bytes, verify the exact source input, generator version/commit,
license, fixture redistribution permission, and any required citation in `data/README.md`. Upstream
code or model licenses do not automatically establish the license of an unrelated input dataset.

## Target packages and contracts

### Adapter package

Replace the single `evidence/adapters.py` module with a package while preserving its public imports:

```text
molecule_atlas/evidence/adapters/
├── __init__.py       # stable public exports
├── contracts.py      # versioned request/result and metadata models; adapter Protocol
├── manifest.py       # existing normalized-manifest importer
├── registry.py       # explicit built-in adapter catalog and lookup
├── boltz.py          # Boltz directory detection and normalization
└── diffdock.py       # DiffDock directory detection and normalization
```

Initial contracts:

```text
AdapterMetadata
  adapter_id
  adapter_version
  title
  description
  upstream_tool
  source_format
  source_format_version
  verified_upstream_versions
  supported_manifest_versions

AdapterImportRequest 0.1.0
  contract_version
  source_path

AdapterImportResult 0.1.0
  contract_version
  adapter_id
  adapter_version
  artifact_root
  manifest: RunManifest 0.1.0
```

The adapter protocol accepts a typed request and returns a typed result. Registry membership is
explicit; no dynamic imports, entry-point discovery, or generic plugin framework are needed.

When semantic artifact manifests land, add a new adapter result contract version rather than
silently changing `AdapterImportResult 0.1.0`.

### Semantic artifact manifest

Add `molecule_atlas/evidence/semantic_artifacts.py` with a separately versioned
`ArtifactManifest 0.1.0`. This leaves `RunManifest 0.1.0` immutable while adding the semantic output
contract already anticipated by `docs/scientific-contracts.md`.

```text
ArtifactManifest
  schema_version
  artifacts

SemanticArtifact
  artifact_id
  logical_name
  artifact_type
  schema_version
  semantic_role
  media_type
  path_or_uri
  content_digest
  size_bytes
  derived_from_artifact_ids
  domain_metadata
  preview_metadata
```

Before persistence exists, project, producing-run, producing-attempt, and storage-URI fields are not
invented. Portable records use local paths and link to the run through the adapter result/bundle.
Future persistence adds those relationships through an explicit newer schema.

Initial artifact types needed in this milestone:

```text
protein-structure
predicted-complex
docking-pose-set
raw-prediction-output
validation-report
run-log
evidence-report
```

Validate unique IDs and logical names, content-digest format, and acyclic/resolvable
`derived_from_artifact_ids`. Cross-check artifact IDs, locations, digests, sizes, and media types
against the accompanying `RunManifest` inventory.

### Adapter normalization behavior

`BoltzAdapter` initially accepts exactly one Boltz prediction target per import. If an output root
contains multiple target directories, the adapter reports an ambiguity error listing the targets;
a later batching capability belongs to the web-import milestone.

It inventories:

- the input YAML when available;
- every predicted CIF/mmCIF model;
- each confidence JSON;
- optional affinity JSON;
- optional PAE/PDE/pLDDT arrays;
- available logs and provenance files.

Each raw JSON field becomes only its documented prediction type. Optional affinity is expected only
when the recorded input requested it. Missing model or confidence outputs create a partial run;
invalid JSON or an upstream failure creates structured failure evidence while preserving readable
artifacts.

`DiffDockAdapter` initially accepts exactly one complex directory. It inventories every ranked SDF,
the input protein/ligand references when present, and available logs/configuration. Rank and
confidence are parsed from the documented filename convention, but the original filename remains
the raw source. The normalized `PoseConfidencePrediction.raw_source.field` is
`filename.confidence`; confidence is never labeled affinity.

Both adapters reject unrecognized or ambiguous layouts with a stable error code, the detected paths,
and their verified compatibility metadata. They do not guess the closest version.

### PoseBusters integration

Add:

```text
molecule_atlas/evidence/validation/
├── contracts.py      # validation request/result versions
├── normalization.py  # explicit column-to-check mappings
└── posebusters.py    # optional upstream import and invocation
```

The optional dependency is pinned to the verified `0.6.x` compatibility range in the integration or
development dependency group, not the default core runtime. The runner uses a named configuration
(`dock`, `redock`, or `mol`) supplied by typed input and requests `full_report=True`.

Raw tabular output is serialized deterministically as a validation artifact before normalization.
Each mapped boolean test and measured value becomes a `ValidationResult` with validator version,
check ID, status, threshold/configuration, explanation, input artifact, and raw-output artifact.
Unknown columns remain in the raw artifact and produce a compatibility warning; they are not
silently discarded or guessed.

## CLI changes

Preserve existing commands and exit behavior. Add incrementally:

```text
molecule-atlas adapters
    List installed adapter IDs, adapter versions, source formats, and verified upstream versions.

molecule-atlas audit PATH --adapter manifest|boltz|diffdock --output MANIFEST
    Normalize and audit one supported source directory.

molecule-atlas validate MANIFEST --validator posebusters \
    --config dock --output OUTPUT
    Run or normalize validation and preserve the raw validation artifact.

molecule-atlas report MANIFEST --format markdown|html [--output OUTPUT]
    Render deterministic reports with identical scientific content.
```

No auto-detection in this milestone. Requiring `--adapter` avoids silently choosing the wrong
upstream interpretation. `inspect` continues to inspect normalized manifests.

## Fixture plan

Use small immutable bundles under:

```text
data/evidence-fixtures/
├── synthetic/                 # move or retain existing Milestone 1 bundles compatibly
├── boltz-2.2.1/
│   ├── succeeded/
│   ├── partial/
│   ├── failed/
│   └── unsupported-layout/
├── diffdock-1.1.3/
│   ├── succeeded/
│   ├── partial/
│   ├── failed/
│   └── unsupported-layout/
└── posebusters-0.6.5/
    ├── pass-and-fail/
    └── upstream-error/
```

Do not move the existing fixture paths in a way that breaks current CLI or test behavior. Real
fixtures include a `SOURCE.md` or equivalent data-README entry recording:

- upstream repository, release, and commit;
- exact command and parameters when known;
- input structure source and license;
- output and redistribution license determination;
- capture date;
- any truncation or deterministic normalization;
- SHA-256 inventory;
- statement that the fixture is computational evidence, not biological truth.

The successful cross-family fixtures must contain scientifically different predictions: Boltz
structure confidence and optional affinity/binder outputs versus DiffDock pose confidence. Partial
fixtures omit an expected artifact but retain remaining evidence. Failed fixtures retain logs and
structured failure. Unsupported fixtures prove precise compatibility errors.

## Acceptance-criterion map

| Roadmap criterion | Packages/models and commands | Fixtures and tests | Documentation |
| --- | --- | --- | --- |
| Boltz output adapter | `adapters/boltz.py`; typed adapter request/result; `audit --adapter boltz` | pinned succeeded/partial/failed/unsupported Boltz fixtures; field-semantic and raw-lineage tests | compatibility table, data provenance, score interpretation |
| DiffDock output adapter | `adapters/diffdock.py`; `PoseConfidencePrediction`; `audit --adapter diffdock` | ranked SDF fixtures; filename parsing, ambiguity, partial/failure tests | explicit statement that confidence is not affinity |
| PoseBusters integration | `validation/posebusters.py`; typed validation request/result; explicit check mapping; `validate` | mixed pass/fail, unavailable/error, unknown-column, and raw-output tests | version/configuration and check interpretation |
| HTML report | deterministic `reports_html.py` using escaped standard-library rendering; `report --format html` | golden semantic assertions for succeeded, partial, failed, warnings, and caveats | README and CLI examples after delivery |
| Real-output fixtures | versioned fixture directories and source records | canonical hashes and offline replay across all states | `data/README.md` plus per-source record |
| Adapter compatibility metadata | `AdapterMetadata`; explicit registry; `adapters` command | strict/frozen/version validation and unknown-version errors | compatibility snapshot and update procedure |
| Versioned typed adapter I/O | `AdapterImportRequest` and `AdapterImportResult`; later semantic result version | JSON/Pydantic round trips, extra-field rejection, schema assertions | `scientific-contracts.md` |
| Semantic artifact types and derivation | `ArtifactManifest`, `SemanticArtifact`, artifact-type literals | uniqueness, digest, resolution, cycle, and RunManifest cross-check tests | `scientific-contracts.md` and schema docs |
| Logical outputs, not filenames | `logical_name`, `artifact_type`, and adapter field mappings | rename-resilience where upstream layout permits; no filename-only normalized lookup | adapter authoring guidance |
| Explicit score interpretation | existing typed prediction union plus adapter-specific mappings | assert no generic `score`; exact units/directions/caveats per raw field | reports, compatibility docs, scientific contracts |
| Two model families normalize to one core | both adapters return the shared versioned evidence bundle | common conformance suite over Boltz and DiffDock fixtures | roadmap completion note |
| PoseBusters raw traceability | raw table artifact plus `ValidationResult.raw_output_artifact_id` | every normalized check resolves to raw bytes and input pose | validation contract documentation |
| Distinct report semantics | Markdown and HTML render by prediction discriminator | cross-family report assertions prohibit affinity/confidence conflation | report interpretation section |
| Precise unsupported-layout failures | stable adapter error codes and compatibility metadata | unknown version, missing directory, ambiguous target, malformed JSON | troubleshooting table |
| Semantic discovery and raw derivation | artifact-manifest queries by type/logical name and derivation graph | raw-to-normalized lineage assertions | artifact contract documentation |

## Incremental implementation slices

### Slice 1 — Adapter contracts and catalog

Status: implemented on 2026-07-10.

- Convert `adapters.py` into the focused adapter package.
- Add strict frozen `AdapterMetadata`, `AdapterImportRequest 0.1.0`, and
  `AdapterImportResult 0.1.0`.
- Add the `EvidenceAdapter` protocol, explicit registry, and `ManifestAdapter`.
- Route existing `audit_path` through the registry with unchanged manifest results.
- Add `molecule-atlas adapters`.
- Add focused contract, registry, CLI, architecture, Ruff, and Pyright tests.

This is the first implementation slice. It registers only `manifest`; Boltz and DiffDock are not
advertised until their fixture-backed implementations exist.

### Slice 2 — Semantic artifact manifest

- Add `ArtifactManifest 0.1.0`, semantic artifact types, logical names, and derivation validation.
- Add canonical serialization and JSON Schema export under `schemas/artifact-manifest/0.1.0`.
- Add a new adapter-result contract version carrying both run and artifact manifests.
- Keep `RunManifest 0.1.0` byte-for-byte and schema-for-schema compatible.

### Slice 3 — Boltz import

- Capture and document licensed Boltz 2.2.1 fixtures.
- Implement layout validation, artifact inventory, typed field mappings, partial/failure behavior,
  and compatibility errors.
- Add report assertions for structure confidence, binder probability, and predicted affinity.

### Slice 4 — DiffDock import

- Capture and document licensed DiffDock 1.1.3 fixtures.
- Implement complex-directory validation, ranked pose inventory, pose-confidence mapping,
  partial/failure behavior, and compatibility errors.
- Run the shared adapter conformance suite against both model families.

### Slice 5 — PoseBusters validation

- Add the optional upstream dependency boundary and pinned compatibility metadata.
- Preserve deterministic raw full-report output.
- Normalize explicit checks into validation evidence and cover mixed, unavailable, and error states.

### Slice 6 — HTML reports and completion

- Add deterministic self-contained HTML output with escaped content and no remote assets.
- Update README, data provenance, scientific contracts, roadmap implemented scope, and CLI help.
- Run all core/backend tests, Ruff, formatting, strict Pyright, schema checks, frontend regression
  gates where shared contracts are unaffected, and container smoke tests if packaging changed.

## Verification gates

Every slice runs its focused tests first. Before Milestone 2 is marked implemented, run:

```bash
cd backend
UV_CACHE_DIR=../.uv-cache uv run pytest
UV_CACHE_DIR=../.uv-cache uv run ruff check .
UV_CACHE_DIR=../.uv-cache uv run ruff format --check .
UV_CACHE_DIR=../.uv-cache uv run pyright
```

Also run `make evidence-contract-check` for every checked-in schema and update that target when the
artifact-manifest schema is added. Normal gates must remain offline and deterministic.

## Deferred work

- FastAPI upload/import endpoints and application capabilities: Milestone 3.
- Protein/pocket browser visualization: Milestone 4.
- PostgreSQL, shared projects, authentication, and persistent artifact storage: Milestone 5.
- Plugin containers and live Vina/PoseBusters campaign execution: Milestone 6.
- Kubernetes, remote GPU, Slurm, or external Boltz/DiffDock inference: Milestones 7–9.
- AI integration or agent tooling: Milestone 10.

No Vina or ProDock adapter is required to complete this milestone. Add one only if Boltz and DiffDock
cannot demonstrate the required cross-family normalization, and record that scope change before
implementation.
