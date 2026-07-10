# Scientific and Interoperability Contracts

## Purpose

Molecule Atlas integrates tools that were not designed around one common schema. This document defines the minimum contracts required to import, validate, compare, review, and eventually execute those tools without losing scientific meaning.

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

## Run state

Imported and executed runs must support:

- `succeeded`;
- `failed`;
- `partial`;
- `cancelled`;
- `unknown` when evidence is insufficient.

A partial run is valid data. Adapters should report which expected outputs are missing rather than rejecting the entire directory.

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

## Import adapters

Import adapters inspect existing output directories and produce the same normalized contracts as managed execution.

Initial targets:

1. Boltz output;
2. DiffDock output;
3. PoseBusters output;
4. AutoDock Vina output;
5. ProDock campaign/database export.

An adapter should be tested against successful, partial, failed, and unknown-version fixtures where practical.

## Reports

The evidence core should support:

- canonical JSON;
- Markdown summary;
- self-contained or portable HTML report.

Reports must show:

- method identity;
- missing provenance;
- score definitions;
- artifact inventory;
- validation failures and warnings;
- partial-run status;
- scientific caveats.

Reports should not invent a universal ranking.

## Versioning

Schemas use explicit semantic versions. Breaking changes require a new major schema version and migration strategy. Adapters declare the versions they can read and produce.

Golden fixtures should protect normalization behavior across releases.

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
