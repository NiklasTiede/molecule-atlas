# Molecule Atlas Product Vision

## Product statement

Molecule Atlas is an open-source, self-hosted visual workbench for exploring small molecules, inspecting protein-ligand results, validating computational evidence, and running reproducible structure-based discovery workflows.

It is not a drug-discovery oracle. It helps researchers organize, inspect, compare, validate, and communicate computational hypotheses before deciding what deserves further computational or experimental work.

## Why this project should exist

Open-source tools already exist for most individual steps in structure-based molecular discovery: molecular preparation, docking, co-folding, affinity prediction, pose validation, interaction profiling, molecular generation, and visualization. The persistent problem is that these tools expose incompatible inputs, outputs, environments, score meanings, licenses, and operational requirements.

Researchers commonly bridge those gaps with notebooks, shell scripts, directories of PDB/SDF files, manually copied parameters, and spreadsheets. This makes it difficult to answer basic questions later:

- Which exact receptor and ligand representation produced this result?
- Which model, checkpoint, container, parameters, and random seed were used?
- Does a value represent docking energy, pose confidence, structure confidence, binder probability, or predicted affinity?
- Did the pose pass physical and chemical validity checks?
- Can another researcher reproduce the run?
- Why was a candidate shortlisted or rejected?

Molecule Atlas addresses this engineering and usability gap.

## Product principles

### The visual workbench is the product

The primary experience is a browser-based scientific workbench, not a marketing site and not only a command-line tool. Researchers should be able to move between candidate tables, molecular structures, protein pockets, poses, interactions, validation evidence, provenance, and review decisions without assembling several unrelated applications.

### Trust is the foundation

Every result must retain its scientific meaning and provenance. Molecule Atlas must not flatten unrelated outputs into a generic score. It should make uncertainty, missing metadata, failed validation, and partial execution visible.

### Import and execution are both supported

Molecule Atlas must provide value when it did not run the computation. It should import outputs from tools such as AutoDock Vina, ProDock, DiffDock, Boltz, GNINA, and future adapters.

Later, the same model and artifact contracts should support launching workflows through local containers, Kubernetes Jobs, remote GPU providers, or institutional clusters.

### Local-first and self-hostable

A researcher should be able to run a useful version on a laptop. A laboratory should be able to deploy a shared version on its own infrastructure. The project should not require sending proprietary targets or compounds to a third-party service.

### Human review remains central

Predictions are evidence, not decisions. Molecule Atlas supports annotation, comparison, shortlisting, and export, but does not claim that a candidate is safe, active, synthesizable, selective, or clinically viable.

### Reuse scientific tools instead of reimplementing them

Molecule Atlas should integrate RDKit, Meeko, AutoDock Vina, PoseBusters, ProLIF, Mol*, Boltz, DiffDock, and other mature tools through explicit adapters. The project should focus its own engineering effort on interoperability, reproducibility, deployment, and review workflows.

## Target users

Primary users are:

- computational chemists running docking or structure-model workflows;
- structural biologists reviewing predicted protein-ligand complexes;
- medicinal chemists reviewing candidate sets and computational evidence;
- research software engineers supporting laboratory infrastructure;
- small biotechnology teams that need a self-hosted alternative to commercial cloud workbenches.

The first external users should already understand that docking and model predictions require expert interpretation.

## Core user journey

A mature Molecule Atlas workflow should support:

1. Create a project.
2. Import or select a protein structure.
3. define or import a binding pocket.
4. Import a candidate molecule set.
5. Explore descriptors, scaffolds, similarities, and chemical space.
6. Import existing model outputs or configure a workflow.
7. Run lightweight local steps or submit heavy jobs to external compute.
8. Inspect poses in the protein context.
9. Review interactions and physical-validity checks.
10. Compare outputs from multiple methods with explicit score semantics.
11. Annotate, reject, or shortlist candidates.
12. Export a reproducible manifest and human-readable report.

## Product scope

### Molecule and candidate exploration

- SMILES/SDF import and validation;
- canonical structures and explicit invalid-record handling;
- descriptors, fingerprints, similarity, scaffolds, and chemical-space views;
- clear distinction between compound identity, enumerated forms, conformers, and poses;
- comparison against reference ligands or known compounds.

### Target and pocket workspace

- PDB/mmCIF import;
- chain, residue, ligand, cofactor, metal, and water visibility;
- receptor-preparation records;
- reference-ligand and manual pocket definitions;
- multiple receptor conformations;
- Mol* protein and protein-ligand visualization.

### Evidence import and audit

- versioned run manifests;
- artifact inventory and SHA-256 hashes;
- model/checkpoint/container/environment metadata;
- successful, failed, and partial run representation;
- model-specific output adapters;
- typed prediction semantics and units;
- readable JSON, Markdown, and HTML reports.

### Validation and interpretation

- PoseBusters-backed pose validation;
- interaction fingerprints through ProLIF or compatible tools;
- explicit validation status, measured values, thresholds, versions, and raw output;
- visible warnings for missing provenance or unsupported interpretations;
- no generic cross-model score unless a user explicitly defines a transparent ranking profile.

### Campaign execution

Execution is a long-term product capability, not the first implementation dependency.

- local fixture/replay executor;
- local OCI-container executor;
- AutoDock Vina and preparation workflows;
- Kubernetes Job execution for k3s and larger clusters;
- remote GPU provider adapters;
- Slurm integration through an agent inside institutional networks;
- cancellation, retry, failure handling, quotas, and immutable execution provenance.

### Collaboration

- shared projects;
- annotations and review status;
- shortlists;
- audit history;
- reproducible exports;
- optional authentication and permissions for shared deployments.

## Scientific language and claims

Use terms such as:

- candidate;
- computational hit;
- predicted pose;
- predicted affinity;
- pose confidence;
- validation result;
- hypothesis for experimental follow-up.

Avoid unsupported terms such as:

- drug;
- safe compound;
- active compound;
- lead;
- clinically promising;
- validated binder.

A candidate with a favorable docking score is not established to be active, selective, soluble, permeable, metabolically stable, safe, or synthesizable.

## Differentiation

Molecule Atlas is not intended to replace every scientific pipeline.

Compared with docking toolkits such as ProDock, Molecule Atlas should be broader across model families and stronger in browser-based review, typed evidence semantics, validation, collaboration, and imported-run auditing. ProDock and similar projects can be upstream execution systems with first-class import adapters.

Compared with hosted platforms, Molecule Atlas should be open, self-hostable, provider-independent, privacy-friendly, and useful without paid GPU execution.

Compared with benchmarking systems such as PoseBench or PLINDER, Molecule Atlas should focus on operational scientific runs and project review rather than leaderboard construction.

Compared with PoseBusters, Molecule Atlas should reuse validation algorithms and provide the surrounding provenance, explanation, visualization, and review experience.

## Long-term architecture direction

The product should remain a modular monolith until scale or independent contribution boundaries justify separation.

- React and TypeScript provide the browser workbench.
- FastAPI provides the control plane and OpenAPI contract.
- Python domain packages provide chemistry, schemas, adapters, validation, and reports.
- PostgreSQL stores shared metadata and durable job state when persistence is introduced.
- An S3-compatible artifact abstraction supports local files and systems such as RustFS.
- Scientific tools run in independently versioned OCI plugin containers.
- Generic executor adapters support fixture, local, Kubernetes, remote GPU, and Slurm environments.

See `docs/architecture.md`, `docs/domain-model.md`, `docs/scientific-contracts.md`, and `docs/roadmap.md`.

## What is intentionally not promised

Molecule Atlas does not promise:

- discovery of clinically viable drugs;
- universal affinity accuracy;
- automatic medicinal-chemistry decisions;
- replacement of laboratory assays;
- replacement of expert protein or ligand preparation;
- one model or ranking method that works across all targets;
- an unrestricted public GPU service;
- immediate support for every docking or structure model.

## Success criteria

The project is succeeding when external users can:

- import their own real model outputs;
- understand scores without consulting model-specific scripts;
- detect invalid or suspicious poses;
- reproduce or audit a run months later;
- compare methods in one interface;
- communicate a shortlist and its evidence to collaborators;
- contribute an adapter without modifying the core application;
- run the application locally or on their own infrastructure.

GitHub stars are secondary. Repeat usage, contributed adapters, research citations, and real project reviews are stronger indicators.
