# Capturing a genuine Boltz 2.2.1 fixture

The checked-in `documented-layout/` directory is deliberately not represented as model output. Use
this procedure to supplement that parser-development fixture with a small, redistributable run
before the `boltz` adapter is added to the public adapter registry.

Boltz 2.2.1 declares Python `>=3.10,<3.13` and has heavyweight scientific/runtime dependencies.
Capture it in a separate Python 3.12 environment; do not add Boltz to the Python 3.13 Molecule Atlas
core or normal CI environment. GPU compute is strongly recommended for generating a fixture but is
not an adapter requirement, normal CI requirement, or current Molecule Atlas execution feature.

## Before running

1. Choose the smallest scientifically meaningful protein-ligand input whose sequence, ligand, MSA,
   templates, and resulting files may all be redistributed publicly.
2. Record the source, version, license, retrieval date, and required citation for every input.
3. Review the Boltz 2.2.1 code, model-weight, and input-data licenses independently. Do not assume
   that the repository's MIT license grants redistribution rights for every input or downloaded
   asset.
4. Avoid confidential structures, sequences, project names, paths, and credentials.

## Reproducible capture

Run outside this repository, on a machine appropriate for Boltz inference. This is a future or
one-time fixture-capture procedure, not a Milestone 2 application runtime requirement:

```bash
python3.12 -m venv .venv-boltz-2.2.1
. .venv-boltz-2.2.1/bin/activate
python -m pip install --upgrade pip
python -m pip install "boltz==2.2.1"
python -m pip freeze > boltz-2.2.1-requirements.txt
boltz predict input.yaml --out_dir capture
```

Use `boltz predict --help` from the pinned installation to record any additional flags needed by the
chosen input. Save the exact command as an argument array, relevant random seeds, accelerator/runtime
information, checkpoint identity, and downloaded model digest where available. Do not infer these
values later from filenames.

Confirm that the unmodified output contains one target under `capture/predictions/`, including its
`<target>_model_<rank>.cif` or PDB structure and
`confidence_<target>_model_<rank>.json`. If affinity was requested, retain
`affinity_<target>.json`. Preserve all other raw upstream output and logs even when the first adapter
version does not normalize them.

## Adding the fixture

1. Copy the smallest unmodified output into a `real-output/succeeded/` directory.
2. Add a source record containing the exact command, input provenance, Boltz/package version,
   checkpoint and container details when known, licenses, citations, capture date, and SHA-256 for
   every retained file.
3. Derive partial and failure cases only when their construction is explicit. A partial fixture may
   omit one copied output while documenting that transformation; a failure fixture must retain the
   authentic raw log and structured failure context.
4. Run the offline adapter, report, artifact-audit, Ruff, formatting, Pyright, and full test gates.
5. Only then register `BoltzAdapter`, expose `audit --adapter boltz`, and update the compatibility
   catalog from “documented layout” to “captured real output.”

Model predictions in this fixture remain computational evidence. They do not establish biological
activity, affinity, selectivity, safety, synthesizability, or clinical value.
