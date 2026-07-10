# Molecule Atlas Domain Model

## Purpose

This document defines the durable concepts Molecule Atlas should use as it evolves from a ligand-centric candidate viewer into a target-aware campaign workbench. It prevents implementation shortcuts from collapsing scientifically distinct concepts into one table or API object.

The model is conceptual. Milestones should introduce only the entities required for the current feature.

## Project and collaboration

### Project

A workspace containing targets, compound collections, imported or executed runs, reviews, and exports.

### ProjectMember

A user and role within a project. Authentication and membership are introduced only when shared projects become a milestone.

### Annotation

A human-authored note linked to a candidate, pose, run, target, or shortlist decision.

### ReviewDecision

A transparent human decision such as `unreviewed`, `review`, `shortlisted`, or `rejected`. It must not be presented as measured biological truth.

## Chemistry

### Compound

The parent chemical identity used to group related representations. It may hold canonical identity keys and source references, but must not silently choose one protonation state, tautomer, stereoisomer, or conformer as universally correct.

### CompoundEnumeration

A specific chemical representation used in a computation, including:

- tautomer;
- protonation/charge state;
- stereochemistry;
- isotopic form where relevant;
- preparation provenance.

### Conformer

A three-dimensional geometry of a compound enumeration generated without protein context. A conformer is not a binding pose.

### CandidateSet

A named collection imported or produced together. Candidate sets remain a central user-facing concept.

Examples:

- uploaded screening library;
- generated molecule batch;
- compounds selected from ChEMBL;
- output of a filtering stage;
- shortlisted candidates.

### Candidate

Membership of a compound or enumeration in a candidate set or campaign context. Candidate-specific fields include source rank, review status, and stage-specific evidence.

A `Candidate` is not named `Drug`, `Lead`, or `ActiveCompound`.

## Targets and structures

### Target

The biological entity or hypothesis under investigation. A target is not the same as a specific structure file.

### ProteinStructure

An experimental or predicted structure with source metadata, chains, residues, ligands, cofactors, and artifact provenance.

### ReceptorPreparation

A computation-ready receptor derived from a protein structure. It records preparation decisions, versions, parameters, and artifacts.

### PocketDefinition

A versioned binding-site definition. Supported sources may include:

- reference ligand;
- explicit residue selection;
- Cartesian box;
- imported prediction;
- pocket-detection tool.

### ReferenceLigand

A ligand used to define or compare a pocket. It may be experimentally observed or computationally supplied; the origin must be explicit.

## Runs and campaigns

### Campaign

A scientific workflow definition connecting inputs, target context, stages, and execution policy.

A campaign may consume a candidate set and produce one or more result candidate sets. The first implementation can remain simpler than a general DAG.

### Run

One concrete attempt to execute or import a method for a specific set of inputs. Runs may be successful, failed, cancelled, or partial.

A run records:

- method and adapter;
- upstream version/commit/checkpoint;
- inputs and hashes;
- parameters and random seeds;
- environment and hardware;
- command or provider request;
- timestamps and runtime;
- artifacts;
- predictions;
- validation evidence;
- warnings and failure details;
- license metadata.

### Job

Operational state for executing a run. Jobs are not the scientific result. A run may exist from imported output without an internally managed job.

### Stage

A named operation within a campaign, such as preparation, docking, co-folding, validation, or interaction profiling.

## Scientific evidence

### Artifact

A file or object produced or consumed by a run.

Required metadata should include:

- stable identifier;
- role;
- media type;
- URI or local path;
- SHA-256;
- size;
- producing stage;
- source name where applicable.

Original upstream artifacts must remain traceable after normalization.

### Pose

A ligand geometry in protein/receptor context. A pose records:

- receptor preparation;
- compound enumeration;
- coordinates/artifact;
- method;
- pose rank where meaningful;
- relationship to the containing run;
- validation and interaction evidence.

A pose is distinct from a conformer and from an experimentally observed complex.

### Prediction

A typed numerical or categorical model output.

Required semantics:

- prediction type;
- value;
- unit where applicable;
- optimization direction where meaningful;
- scope: complex, pose, ligand, residue, or atom;
- method and raw source field;
- uncertainty/confidence if provided;
- interpretation and caveats.

Initial prediction types may include:

- `docking_energy`;
- `pose_confidence`;
- `structure_confidence`;
- `predicted_affinity`;
- `binder_probability`;
- molecular descriptors.

Do not introduce an unqualified generic `score` in persistent or public APIs.

### ValidationResult

A result from a named check.

Required semantics:

- validator and version;
- check ID;
- status: pass, fail, warning, unavailable, or error;
- measured value and unit where applicable;
- threshold/configuration;
- explanation;
- input artifact;
- raw output reference.

### InteractionFingerprint

A residue-level or atom-level representation of protein-ligand interactions, produced by ProLIF or another adapter. It must retain tool version and configuration.

### EvidenceBundle

A user-facing grouping of poses, predictions, validation results, interactions, artifacts, and provenance for one candidate or run. This is a presentation concept and should not erase the underlying typed records.

## Identity and lineage

Every normalized record should answer:

- Where did this come from?
- Which raw artifact contains the original value?
- Which adapter transformed it?
- Which version of the schema was used?
- Which upstream object does it refer to?

Use stable internal IDs and retain upstream IDs separately. Do not use filenames as the sole identity.

## Suggested relationships

```text
Project
├── Target
│   └── ProteinStructure
│       └── ReceptorPreparation
│           └── PocketDefinition
├── Compound
│   └── CompoundEnumeration
│       └── Conformer
├── CandidateSet
│   └── Candidate ───────────────┐
├── Campaign                     │
│   └── Run                      │
│       ├── Artifact             │
│       ├── Pose ────────────────┘
│       ├── Prediction
│       ├── ValidationResult
│       └── InteractionFingerprint
└── Annotation / ReviewDecision / Shortlist
```

## Migration from the current MVP

The current candidate model contains molecule data and a generic optional score. Preserve its working API while introducing new concepts incrementally.

Recommended migration:

1. Add typed `Prediction` objects while temporarily reading legacy demo scores as explicitly marked mock predictions.
2. Introduce importable candidate sets and stable IDs.
3. Add `RunManifest`, artifacts, and evidence import.
4. Add targets, structures, pockets, and poses.
5. Add persistence and project relationships.
6. Add managed jobs and campaign execution.

Avoid a single large database migration that attempts to model the complete long-term system before the corresponding workflows exist.
