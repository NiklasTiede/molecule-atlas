# Molecule Atlas Domain Model

## Purpose

This document defines the durable concepts Molecule Atlas should use as it evolves from a ligand-centric candidate viewer into a target-aware campaign workbench. It prevents implementation shortcuts from collapsing scientifically distinct concepts into one table or API object.

The model is conceptual. Milestones should introduce only the entities required for the current feature.

## Project and collaboration

### Project

A workspace containing targets, compound collections, imported or executed runs, reviews, and exports.

### ProjectMember

A user and role within a project. Authentication and membership are introduced only when shared projects become a milestone.

### Actor

The identity responsible for an application action. Actor types are `human`, `service`, `plugin`, and
`agent`. An agent actor records its delegating human and granted scope; it is never stored as if it
were the human. Actors become persistent with shared projects, but capability invocations should
carry explicit actor context as soon as authorization exists.

### Annotation

A human-authored note linked to a candidate, pose, run, target, or shortlist decision.

### ReviewDecision

A transparent human decision such as `unreviewed`, `review`, `shortlisted`, or `rejected`. It must not be presented as measured biological truth.

`ReviewDecision` is a workflow status for a reviewed object. It is distinct from a
`ScientificDecision`, which records a project-level choice, rationale, alternatives, evidence, owner,
and approval history.

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

### Capability

A stable, versioned, meaningful application operation with typed input/output contracts, permissions,
side effects, risk, cost/runtime class, and execution features. Capabilities are used by HTTP
handlers, workers, predefined workflows, and a future AI module. Repository CRUD methods are not
automatically capabilities.

Capabilities are classified as query, command, job, or proposal. Important capability IDs remain
stable even when transports or implementations change.

### Campaign

A scientific workflow definition connecting inputs, target context, stages, and execution policy.

A campaign may consume a candidate set and produce one or more result candidate sets. The first implementation can remain simpler than a general DAG.

### Plan

A versioned objective and constrained set of steps. Plans can be created manually or from predefined
workflow templates before any LLM exists. A future AI module proposes the same plan structure.

A plan records project, objective, status, version, creator, constraints, budget, and timestamps.

### PlanStep

A configured invocation of a capability. It records capability ID/version, typed input bindings,
dependencies, status, and approval policy. Plans and steps are validated before execution and can
wait for human approval.

### Run

A logical invocation of a capability for a specific set of inputs. The same model covers imports,
reports, application operations, scientific plugins, model inference, and future agent actions. A run
may have multiple attempts because of retry or provider failure.

A run records:

- capability ID/version and run type;
- project, plan, and plan-step relationships;
- initiating actor;
- parent and root run relationships;
- idempotency, correlation, and causation IDs;
- input and output manifest references;
- aggregate status and structured error details;
- timestamps;
- child attempts and runs.

### RunAttempt

One concrete import or execution attempt beneath a logical run. An attempt records:

- attempt number and retry relationship;
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

The implemented portable `RunManifest` 0.1.0 currently describes one evidence-producing/import
attempt. Later schemas must relate that evidence snapshot to the shared logical run without silently
changing the existing contract.

### Job

An external or internal provider execution handle attached to a run attempt. Provider job IDs and
states are operational data, not the scientific result and not a second execution model. Imported
runs may have attempts without provider jobs.

### Stage

A named operation within a campaign, such as preparation, docking, co-folding, validation, or interaction profiling.

## Scientific evidence

### Artifact

A file or object produced or consumed by a run or run attempt.

Required metadata should include:

- stable identifier;
- semantic artifact type and schema version;
- semantic role;
- media type;
- storage URI or portable local path;
- content digest, initially SHA-256;
- size;
- project and producing run/attempt where applicable;
- derived-from artifact relationships;
- creation timestamp;
- domain and preview metadata;
- producing stage and logical plugin output name;
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

### Evidence

A structured reference to information that supports or contradicts a claim or informs a decision.
Evidence points to typed predictions, validation results, artifacts, observations, runs, or other
reviewable records. It does not copy or flatten their semantics.

### ScientificClaim

A reviewable scientific interpretation with statement, claim type, status, confidence semantics,
supporting evidence, contradicting evidence, proposer, reviewer, and supersession relationship.
Statuses include `proposed`, `accepted`, `rejected`, `uncertain`, and `superseded`.

Model output alone cannot create an accepted claim. An agent may propose a claim but is not its human
reviewer.

### ScientificDecision

A human-owned project choice with selected candidates or actions, rationale, rejected alternatives,
supporting evidence, owner, AI contribution if any, approvals, and timestamp. Important decisions do
not live only in annotations or chat history.

### DomainEvent

A typed, versioned fact about a domain transition. Its envelope carries event ID/type, occurrence
time, project, actor, correlation ID, causation ID, and typed payload. Events support durable workflow
progression, audit, SSE projections, and later agent notifications; SSE itself is not durable state.

## Identity and lineage

Every normalized record should answer:

- Where did this come from?
- Which raw artifact contains the original value?
- Which adapter transformed it?
- Which version of the schema was used?
- Which upstream object does it refer to?
- Which actor and capability initiated the operation?
- Which plan, parent/root run, attempt, correlation, and causation relationships apply?
- Which artifacts were used, generated, or derived?
- Which evidence supports or contradicts a claim or informed a decision?

Use stable internal IDs and retain upstream IDs separately. Do not use filenames as the sole identity.

## Suggested relationships

```text
Project
├── Actor / ProjectMember
├── Target
│   └── ProteinStructure
│       └── ReceptorPreparation
│           └── PocketDefinition
├── Compound
│   └── CompoundEnumeration
│       └── Conformer
├── CandidateSet
│   └── Candidate ───────────────┐
├── Campaign / Plan              │
│   └── PlanStep → Capability    │
│       └── Run                  │
│           ├── child Run        │
│           └── RunAttempt       │
│               ├── Artifact     │
│               ├── Pose ────────┘
│               ├── Prediction
│               ├── ValidationResult
│               └── InteractionFingerprint
├── Evidence ──> ScientificClaim ──> ScientificDecision
└── Annotation / ReviewDecision / Shortlist / DomainEvent
```

## Migration from the current MVP

The current candidate model contains molecule data and a generic optional score. Preserve its working API while introducing new concepts incrementally.

Recommended migration:

1. Add typed `Prediction` objects while temporarily reading legacy demo scores as explicitly marked mock predictions.
2. Introduce importable candidate sets and stable IDs.
3. Add `RunManifest`, artifacts, and evidence import.
4. Add typed application capabilities and bounded evidence queries when HTTP import begins.
5. Add targets, structures, pockets, and poses through the same capability and artifact contracts.
6. Add persistence, actors, authorization, hierarchical runs/attempts, plans/steps, idempotency,
   events, claims, decisions, and project relationships.
7. Add managed campaign execution, durable progression, approvals, risk policies, and budgets.
8. Add optional AI plan proposal and explanation only after the normal execution path is trusted.

Avoid a single large database migration that attempts to model the complete long-term system before the corresponding workflows exist.

### Current portable evidence implementation

Milestone 1 implements `Run`, `Artifact`, typed `Prediction`, and `ValidationResult` as versioned,
immutable Pydantic contracts in the portable core. These records are file-backed and have no
database identity or persistence mapping. Stable manifest IDs and explicit artifact references
provide local lineage.

The evidence `Prediction` contract is a discriminated union. Docking energy, pose confidence,
structure confidence, binder probability, and predicted affinity remain distinct types with their
own unit and optimization-direction constraints. The legacy candidate workbench's optional mock
`score` remains unchanged for backward compatibility and is not part of the evidence manifest.

Inputs may declare representations such as conformer, predicted pose, docked pose, or experimental
complex. This records the distinction without introducing target, protein, pocket, or pose-workspace
entities before their roadmap milestone.

Milestone 2 adds a companion portable `ArtifactManifest 0.1.0`. It gives every artifact a stable
logical name, controlled semantic type and role, algorithm-qualified content digest, and explicit
derived-from relationships. Its complete inventory must match the corresponding `RunManifest 0.1.0`
artifact paths, media types, hashes, and sizes. Persistence-only project, producing-run, and storage
relationships remain deferred rather than being invented in the portable contract.
