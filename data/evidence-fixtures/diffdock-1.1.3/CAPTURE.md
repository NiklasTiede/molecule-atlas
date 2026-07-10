# Capturing a genuine DiffDock 1.1.3 fixture

The checked-in `documented-layout/` directory is a parser-development fixture, not model output.
This procedure is for a future or one-time genuine capture before the adapter is publicly
registered. It is not a Milestone 2 application runtime requirement.

DiffDock 1.1.3 can run on CPU when a protein PDB is supplied, but its own documentation describes
CPU inference as significantly slower and recommends a GPU when available. Neither GPU compute nor
DiffDock itself is required to import existing output, run the adapter tests, or use normal
Molecule Atlas CI.

## Before running

1. Choose a minimal protein and ligand whose source files and generated outputs may be redistributed.
2. Record source, version, license, retrieval date, and citation for both inputs.
3. Review code, model-weight, input-data, and generated-output redistribution terms independently.
4. Avoid confidential structures, project names, local paths, and credentials.

## Reproducible capture

Use the official `v1.1.3` environment outside the Molecule Atlas core. Record the fully resolved
environment and exact command. The upstream reference invocation is:

```bash
python -m inference \
  --config default_inference_args.yaml \
  --protein_ligand_csv input.csv \
  --out_dir capture
```

Preserve the complete unmodified complex directory, including every
`rank<rank>_confidence<confidence>.sdf`, the `rank1.sdf` alias, logs, configuration, input records,
checkpoint identity, runtime/device information, and failures. Do not infer missing provenance from
the filenames.

## Adding the fixture

1. Copy the smallest licensed output into `real-output/succeeded/`.
2. Add a source record with command, environment, input provenance, DiffDock version/commit,
   checkpoint digests, licenses, citations, capture date, and file SHA-256 values.
3. Derive partial cases only with an explicit transformation record. A failed case must retain its
   authentic raw log and failure context.
4. Run offline adapter, report, artifact-audit, Ruff, formatting, Pyright, and full test gates.
5. Only then register `DiffDockAdapter` and expose it through the CLI compatibility catalog.

DiffDock confidence describes predicted pose quality. It is not binding affinity or evidence of
biological activity, selectivity, safety, synthesizability, or clinical value.
