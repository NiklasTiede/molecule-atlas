# Demo Data

`demo_candidates.csv` is a small manually curated demonstration dataset of common molecules plus one intentionally invalid SMILES row.

The `score` values are mock demo values. They are not measured affinities, docking scores, clinical claims, or medicinal recommendations.

This dataset is used to exercise Molecule Atlas ingestion, validation, descriptor calculation, similarity search, and UI states.

## Portable evidence fixtures

`evidence-fixtures/` contains three manually authored, deterministic run bundles:

- `succeeded`: all expected synthetic outputs exist, with typed docking-energy and
  binder-probability predictions plus mixed pass/fail validation evidence;
- `partial`: a raw pose-confidence value exists while the expected predicted-complex artifact is
  explicitly missing;
- `failed`: a structured upstream failure retains its synthetic raw stderr log and has no prediction.

All structures, values, logs, tool names, timestamps, and validation results in these bundles are
synthetic. They were created for Molecule Atlas contract tests, do not come from a scientific tool,
model, checkpoint, or external dataset, and must not be interpreted as biological evidence. The
fixture manifests inventory every included raw artifact by relative path, byte size, and SHA-256.

The successful bundle also contains `molecule-atlas-artifacts.json`, a canonical synthetic
`ArtifactManifest 0.1.0`. It assigns stable logical names and semantic artifact types to the same
complete artifact inventory, uses algorithm-qualified content digests, and records explicit
ligand-to-pose and pose-to-validation derivation relationships. Tests require its paths, media types,
digests, and sizes to match `molecule-atlas-run.json` exactly.

The evidence fixtures are provided under CC0-1.0 as recorded in each manifest. They require no model
download, network access, database, GPU, or third-party service.
