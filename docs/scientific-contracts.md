# Scientific and Interoperability Contracts

## Purpose

Molecule Atlas integrates tools that were not designed around one common schema. This document defines the minimum contracts required to import, validate, compare, review, and eventually execute those tools without losing scientific meaning.

Application orchestration must preserve these scientific contracts. The UI, workers, predefined
workflows, and a future AI module invoke the same typed application capabilities rather than creating
transport- or agent-specific scientific schemas. See `docs/ai-first-readiness.md`.

## Application capability contract

An important application operation declares:

```text
capability_id
capability_version
kind: query | command | job | proposal
typed input schema
typed output schema
required permissions
risk and approval policy
side effects
cost and runtime class
idempotency, cancellation, and dry-run support
```

Capability IDs remain stable across URL or implementation changes. FastAPI operations use explicit
stable `operation_id` values. Internal CRUD and repository methods do not automatically become
capabilities or agent tools.

Capability payloads identify domain records and semantic artifacts explicitly. Do not use generic
`options`, `files`, or filename lists when fields and meanings can be modeled. A future agent receives
only authorized capabilities and never direct database, storage, executor, cluster, or provider
access.

## Run manifest

Every imported or managed run should normalize into a versioned manifest such as `molecule-atlas-run.json`.

Minimum sections:

```json
{
  "schema_version": "0.1.0",
  "run": {},
  "method": {},
  "inputs": [],
  "parameters": {},
  "environment": {},
  "artifacts": [],
  "predictions": [],
  "validation_results": [],
  "licenses": [],
  "warnings": []
}
```

The manifest complements raw output files; it does not replace or rewrite them.

### Implemented schema version 0.1.0

The checked-in validation schema is `schemas/run-manifest/0.1.0.schema.json`. The canonical Pydantic
models live in the FastAPI-independent `molecule_atlas.evidence` package. Unknown fields and
non-finite numbers are rejected. Artifact, input, prediction, and validation IDs are checked for
uniqueness and all method/artifact references must resolve within the manifest.

Canonical JSON is UTF-8 with lexicographically sorted object keys, compact separators, JSON-native
Pydantic values, no non-finite numbers, and one trailing newline. This project representation is
deterministic for the same validated manifest; it is not claimed to implement RFC 8785.

## Run state

Imported and executed runs must support:

- `succeeded`;
- `failed`;
- `partial`;
- `cancelled`;
- `unknown` when evidence is insufficient.

A partial run is valid data. Adapters should report which expected outputs are missing rather than rejecting the entire directory.

## Application run and attempt contract

The implemented manifest `run` section is a portable evidence snapshot. The target application model
uses one logical `Run` with one or more `RunAttempt` records for imports, reports, capabilities,
plugins, model inference, retries, and future agent actions.

The logical run carries project, capability ID/version, run type, actor, parent/root run, plan/step,
input/output manifest, idempotency, correlation, causation, status, timestamps, and structured error
fields. An attempt carries attempt number, retry relationship, executor/provider job identity, exact
plugin/container/checkpoint details, runtime, logs, artifacts, and attempt-specific failure.

Do not add these as silently required fields to schema 0.1.0. Introduce a versioned schema and
migration strategy when the persistence or execution milestone implements the shared model.

## Method identity

Capture as much as is available:

- Molecule Atlas adapter ID and version;
- upstream tool name and version;
- source commit;
- checkpoint/model identifier and hash;
- container image and digest;
- command and arguments;
- parameters;
- random seeds;
- environment and accelerator;
- runtime;
- license state.

Missing fields generate explicit warnings. They must not be silently invented.

The Milestone 1 auditor derives stable warnings for missing upstream identity/version, command,
random seed, environment, license metadata, checkpoint hash, and container digest when applicable.
Auditing never fills an absent provenance field with a guessed value. Local artifacts are reported as
verified, missing, mismatched, unsafe, or unreadable; external URIs are retained and explicitly marked
as not verified by the offline auditor.

## Artifact contract

Artifacts carry:

```text
id
role
path_or_uri
media_type
sha256
size_bytes
created_by_stage
original_name
metadata
```

Suggested roles include:

- receptor input;
- ligand input;
- predicted complex;
- pose set;
- raw score output;
- validation output;
- interaction output;
- log;
- report.

The same bytes must produce the same content hash. Tests should use deterministic fixtures.

The implemented portable `ArtifactManifest 0.1.0` complements the immutable `RunManifest 0.1.0`
artifact inventory with:

```text
artifact_id
artifact_type
schema_version
logical_name
semantic_role
media_type
path_or_uri
content_digest
size_bytes
derived_from_artifact_ids
domain_metadata
preview_metadata
```

Artifact IDs and logical names are unique. Derivation references must resolve within the complete
manifest and cannot contain self-references, repeated sources, or cycles. When bound to a
`RunManifest 0.1.0`, the artifact IDs, paths, media types, SHA-256 digests, and sizes must agree
exactly. The portable contract does not invent project, producing-run, attempt, storage, or creation
metadata before persistence owns those fields.

Artifact types are stable semantic identifiers such as `compound-set`, `protein-structure`,
`prepared-pocket`, `docking-pose-set`, `docking-score-table`, `interaction-fingerprint`,
`validation-report`, `candidate-shortlist`, or `campaign-report`. Filenames and media types alone do
not define scientific meaning.

## Prediction contract

Predictions must never be stored only as `score`.

Required fields:

```text
type
value
unit
scope
method reference
raw field/source
optimization direction
uncertainty/confidence
interpretation
```

Examples:

```text
Vina affinity:
  type: docking_energy
  unit: kcal/mol
  direction: lower_is_better

DiffDock confidence:
  type: pose_confidence
  unit: null
  direction: higher_is_better
  interpretation: pose-quality confidence, not binding affinity

Boltz affinity probability:
  type: binder_probability
  unit: probability
  direction: higher_is_better
```

Adapters are responsible for preserving upstream field names and documented meanings.

The implemented `Prediction` union contains:

- `docking_energy`, with a required unit and `lower_is_better` direction;
- `pose_confidence`, unitless and `higher_is_better`;
- `structure_confidence`, unitless and `higher_is_better`;
- `binder_probability`, constrained to `[0, 1]` with unit `probability`;
- `predicted_affinity`, with a required unit and explicit lower- or higher-is-better direction.

Every prediction includes a method reference, scope and scope ID, raw artifact and upstream field,
interpretation, caveats, and optional typed uncertainty. There is no persistent unqualified `score`
field in this contract.

## Validation contract

Validation is evidence, not a global verdict.

Each check records:

```text
validator
validator_version
check_id
status
measured_value
unit
threshold_or_configuration
explanation
input_artifact
raw_output_artifact
```

A candidate may have mixed validation results. UI defaults may filter on selected gates, but raw checks remain visible.

PoseBusters is the initial validator. Molecule Atlas should not duplicate its scientific algorithms.

The implemented PoseBusters integration pins upstream `0.6.5` behind the optional
`molecule-atlas-core[posebusters]` extra. The default portable core does not import pandas, RDKit, or
PoseBusters. Existing `full_report=True` CSV files normalize through the standard library into a
content-addressed `validation-report` artifact and explicit `ValidationResult` records.

Boolean values map to `pass` or `fail`; missing values map to `unavailable`; malformed mapped values
remain visible as `error`. Stable numeric details such as energy ratio, protein-ligand distance,
volume overlap, and redocking RMSD retain units and the pinned configuration threshold. Unmapped
columns remain byte-for-byte in the raw report and produce a compatibility warning. Every normalized
check references both its input artifact and raw report artifact.

Optional execution uses `max_workers=0`, always requests `full_report=True`, writes deterministic CSV,
and rejects any installed PoseBusters version other than `0.6.5`. It is local CPU validation, not
model inference or evidence of binding affinity or biological activity.

## Interaction contract

Interaction records should retain:

- tool and version;
- pose ID;
- receptor residue identity;
- ligand atom identity where available;
- interaction type;
- geometry values;
- configuration;
- raw output reference.

ProLIF is the preferred initial adapter. Other tools can map to the same normalized representation.

## Plugin definition

Each executable scientific adapter declares metadata separately from application code.

Example:

```yaml
id: boltz
name: Boltz
adapter_version: 0.1.0

execution:
  image: ghcr.io/example/plugin-boltz@sha256:...
  command: ["python", "-m", "molecule_atlas_boltz"]
  timeout_seconds: 7200

resources:
  cpu: 8
  memory_gib: 64
  gpu:
    required: true
    minimum_count: 1

capabilities:
  - complex_structure_prediction
  - pose_confidence
  - affinity_prediction

inputs:
  schema: schemas/boltz-input.schema.json
outputs:
  schema: schemas/boltz-output.schema.json

licenses:
  adapter: Apache-2.0
  upstream_code: MIT
  model_weights: MIT
```

Plugin images own their Python, CUDA, model, and native-library dependency versions. The FastAPI environment must not absorb all plugin dependencies.

## Plugin filesystem contract

```text
/input/
  request.json
  artifacts...

/output/
  result.json
  artifact-manifest.json
  stdout.log
  stderr.log
  artifacts/
```

Required behavior:

- validate `request.json` before expensive work;
- write structured failure information when possible;
- write outputs only beneath `/output`;
- preserve upstream raw outputs;
- generate a normalized result;
- use documented exit codes;
- never report success when required artifacts are absent.

Normalized plugin results declare a versioned result type and semantic artifacts. For example, a
docking plugin identifies logical `poses` and `scores` outputs as `docking-pose-set` and
`docking-score-table` artifacts with explicit media types and paths. Returning only `files: [...]` is
not a sufficient plugin result contract.

Plugins contain no AI planning, project authorization, approval, or scientific-decision logic.

## Import adapters

Import adapters inspect existing output directories and produce the same normalized contracts as managed execution.

Initial targets:

1. Boltz output;
2. DiffDock output;
3. PoseBusters output;
4. AutoDock Vina output;
5. ProDock campaign/database export.

An adapter should be tested against successful, partial, failed, and unknown-version fixtures where practical.

The implemented adapter boundary uses strict, frozen Pydantic contracts:

```text
AdapterMetadata
  adapter ID/version
  upstream tool when applicable
  source format/version
  verified upstream versions
  supported normalized manifest versions

AdapterImportRequest 0.1.0
  contract version
  source path

AdapterImportResult 0.1.0
  contract version
  adapter ID/version
  artifact root
  RunManifest 0.1.0

AdapterImportResult 0.2.0
  contract version
  adapter ID/version
  artifact root
  RunManifest 0.1.0
  ArtifactManifest 0.1.0, validated against the run artifact inventory
```

The explicit built-in registry currently contains only `manifest`. It reads an existing
`molecule-atlas-run.json` file or directory, validates the normalized contract, derives provenance
warnings, and verifies local artifact bytes. `molecule-atlas adapters` exposes its compatibility
metadata. A source-verified but unregistered `BoltzAdapter` parses the documented Boltz 2.2.1 output
layout into `AdapterImportResult 0.2.0`. It maps `confidence_score` to structure confidence,
`affinity_probability_binary` to binder probability, and `affinity_pred_value` to predicted
`log10(IC50/µM)` with lower-is-better semantics. The last value is not measured affinity. Boltz and
DiffDock are not registered until pinned real-output layouts have deterministic captured-fixture
coverage. Documented pLDDT, PAE, and PDE NPZ files remain opaque, content-addressed
`raw-prediction-output` artifacts; the portable core does not load NumPy or reinterpret their
matrices during import.

The source-verified, unregistered `DiffDockAdapter` parses the documented DiffDock 1.1.3 ranked-SDF
convention into the same adapter-result `0.2.0` boundary. A filename confidence becomes only a
`PoseConfidencePrediction` with `filename.confidence` raw lineage and higher-is-better semantics.
It is never labeled affinity. The unqualified `rank1.sdf` copy is retained as a top-pose alias
artifact and does not create a duplicate prediction. Rank gaps produce a partial run.

The adapter result `0.1.0` remains tied to `RunManifest 0.1.0`. `ArtifactManifest 0.1.0` is available
as a separate portable contract. Adapter result `0.2.0` binds both manifests and rejects any path,
media type, digest, size, or inventory disagreement without silently changing
`AdapterImportResult 0.1.0`.

## Reports

The evidence core supports:

- canonical JSON;
- Markdown summary;
- self-contained HTML report.

Reports must show:

- method identity;
- missing provenance;
- score definitions;
- artifact inventory;
- validation failures and warnings;
- partial-run status;
- scientific caveats.

Reports should not invent a universal ranking.

The current CLI supports:

```text
molecule-atlas adapters
molecule-atlas inspect PATH
molecule-atlas audit PATH --adapter manifest --output OUTPUT
molecule-atlas report MANIFEST --format markdown|html [--output OUTPUT]
molecule-atlas schema --contract run-manifest|artifact-manifest --output OUTPUT
```

Markdown and HTML reports include run state and failures, method identity, provenance warnings,
typed prediction meanings, the artifact inventory and audit state, all validation results, licenses,
and scientific caveats.

## Versioning

Schemas use explicit semantic versions. Breaking changes require a new major schema version and migration strategy. Adapters declare the versions they can read and produce.

Golden fixtures should protect normalization behavior across releases.

## Plans, actors, events, claims, and decisions

Plans and plan steps are typed, versioned application records before any LLM integration. A step
references a capability ID/version, typed input bindings, dependencies, status, and approval policy.
The backend validates and executes plans regardless of whether they came from the UI, a predefined
workflow, or a future AI proposal.

Actors are typed as human, service, plugin, or agent. An agent record includes its delegating human,
permission scope, agent/model identity, tool calls, and approvals. It is never indistinguishable from
the user.

Domain events use versioned names such as `run.created.v1`, `artifact.created.v1`,
`validation.issue_detected.v1`, `plan.approval_required.v1`, and `decision.recorded.v1`. The envelope
includes event ID/type, occurrence time, project, actor, correlation ID, causation ID, and a typed
payload. Persisted state and events drive workflow progression; SSE is only a delivery projection.

Scientific claims retain supporting and contradicting evidence, status, proposer, reviewer, and
supersession. Scientific decisions retain owner, rationale, rejected alternatives, evidence, AI
contribution, and human approval. Neither chat history nor a model response is the authoritative
record.

## License metadata

Track separately:

- adapter code license;
- upstream code license;
- model-weight license;
- dataset license;
- redistribution restrictions;
- user acknowledgement requirements where applicable.

Do not assume that open source code implies unrestricted model weights or training data.

## Scientific invariants

The following are non-negotiable:

- conformers are not poses;
- predicted poses are not experimental structures;
- pose confidence is not binding affinity;
- predicted affinity is not measured affinity;
- absent activity data does not mean inactivity;
- validation failure must remain visible;
- raw evidence and normalization lineage must remain traceable;
- no model result alone establishes a drug candidate.
