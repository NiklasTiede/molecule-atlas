# Molecule Atlas Roadmap

## How to use this roadmap

This roadmap defines product milestones, not fixed release dates. Coding agents should implement the earliest incomplete milestone and avoid pulling later infrastructure into earlier work without a concrete dependency.

Every milestone must preserve the completed behavior and verification gates from previous milestones.

AI-first readiness is a cross-cutting architecture constraint, not permission to implement an LLM
early. The React UI and a future AI module must use the same typed, authorized application
capabilities. See `docs/ai-first-readiness.md` and ADR 0001.

Application deployment and scientific execution are independent roadmap concerns. Personal and
Team Server Compose packaging must remain useful without Kubernetes; Cluster Helm packaging and
each executor arrive only in their owning milestones. See ADR 0002.

## Milestone 0 — Ligand-centric workbench baseline

Status: substantially implemented.

Capabilities:

- bundled deterministic candidate set;
- RDKit parsing and canonicalization;
- structured invalid-SMILES handling;
- descriptors and triage flags;
- fingerprints and Tanimoto similarity;
- Murcko scaffolds;
- backend-generated 2D SVGs;
- simple 3D conformer viewing;
- chemical-space projection;
- React workbench with generated OpenAPI types;
- backend, frontend, e2e, and container verification.

Exit criteria:

- all existing CI gates pass;
- scientific caveats remain visible;
- current public APIs remain documented.

## Milestone 1 — Portable evidence core

Status: implemented.

Goal: represent model outputs rigorously without a database, GPU, or managed execution.

Deliverables:

- core Python package independent of FastAPI;
- versioned `RunManifest` schema;
- `Artifact`, `Prediction`, `ValidationResult`, and method metadata;
- SHA-256 artifact inventory;
- JSON Schema export;
- canonical JSON serialization;
- Markdown report generation;
- deterministic successful, partial, and failed fixtures;
- CLI entry point for inspecting and reporting fixture/imported runs.

Initial CLI shape:

```bash
molecule-atlas inspect PATH
molecule-atlas audit PATH --adapter ADAPTER --output OUTPUT
molecule-atlas report MANIFEST --format markdown
```

Exit criteria:

- no generic persistent `score` in the new evidence contract;
- missing provenance produces warnings rather than invented values;
- partial and failed runs can be represented;
- core tests require no network or GPU;
- FastAPI can call the core package without duplicate schemas.

Implemented scope:

- a separately packaged `molecule_atlas.evidence` core with Pydantic as its only runtime dependency;
- strict schema version `0.1.0` with typed docking energy, pose confidence, structure confidence,
  binder probability, and predicted-affinity records;
- streaming SHA-256 inventory and offline verification of local artifacts;
- canonical JSON, checked-in JSON Schema, and deterministic Markdown reports;
- synthetic successful, partial, and failed fixtures with explicit data provenance;
- `inspect`, `audit --adapter manifest`, `report --format markdown`, and schema-export CLI commands.

Real scientific-tool output adapters, PoseBusters execution, HTML reports, persistence, managed
execution, and protein/pose web visualization remain in their later milestones.

The broader AI-readiness checklist is not retroactively part of Milestone 1. Hierarchical persisted
runs, plans, authorization, idempotency, events, and durable workflow controls depend on later
milestones. They are assigned below and must land before the first feature that depends on them.

## Milestone 2 — Real-output import and validation

Status: implemented.

Goal: demonstrate value on outputs Molecule Atlas did not execute.

Deliverables:

- Boltz output adapter;
- DiffDock output adapter;
- PoseBusters integration and normalized checks;
- HTML report;
- successful, partial, and failed real-output fixtures where licensing permits;
- adapter compatibility metadata;
- versioned typed adapter input/output contracts;
- semantic artifact types and explicit artifact derivation lineage;
- adapter outputs that identify logical artifacts rather than relying on filenames;
- explicit score interpretation in reports.

A Vina or ProDock adapter may be added in this milestone if it helps prove cross-family normalization.

Exit criteria:

- at least two fundamentally different model families normalize into the same core contract;
- PoseBusters raw output remains traceable;
- reports clearly distinguish pose confidence, structure confidence, docking energy, binder probability, and predicted affinity;
- adapter failures identify unsupported layouts or versions precisely;
- normalized artifacts can be discovered by semantic type and traced to raw upstream artifacts.

Implemented scope:

- adapter-result contract `0.2.0` binds run and semantic artifact manifests without changing
  manifest-only result `0.1.0`;
- source-verified Boltz 2.2.1 and DiffDock 1.1.3 normalizers prove distinct structure-confidence,
  binder-probability, predicted-affinity, and pose-confidence semantics through offline fixtures;
- PoseBusters 0.6.5 has a genuine CPU full-report fixture, portable normalization, and an optional
  exactly pinned local runner;
- deterministic Markdown and self-contained escaped HTML reports expose run state, typed
  predictions, artifact audits, validation evidence, provenance warnings, licenses, and caveats;
- normal CI remains offline and requires no database, GPU, model download, or FastAPI import.

The pinned Boltz and DiffDock releases contain no redistributable generated-output fixtures, and
creating those model outputs would pull live inference forward. Their current fixtures are explicitly
documentation-derived and the adapters remain outside the public registry. Genuine successful,
partial, and failed model captures, final conformance, and registration move to Milestone 8 alongside
the owning remote-GPU execution work. This limitation does not block manifest-based web evidence
import in Milestone 3 and is not represented as verified operational compatibility.

## Milestone 3 — Evidence import in the web workbench

Status: in progress. Slice 1 implements the capability catalog, permission-aware invocation context,
bounded local `get_run_summary` query, explicit correlation ID, and thin HTTP operation. Safe local
bundle import and the remaining review/query UI follow in the next slices.

Goal: make the visual application useful for reviewing imported model evidence.

Deliverables:

- an explicit application capability layer between FastAPI and domain/core operations;
- initial stable capability IDs and versions for evidence import, inspection, comparison, validation,
  and report generation;
- capability metadata for permissions, side effects, risk, cost/runtime class, idempotency,
  cancellation, and dry-run support, even when later milestones own enforcement;
- typed capability input and output contracts;
- thin FastAPI handlers with explicit, stable OpenAPI `operation_id` values;
- explicit query, command, job, and proposal semantics;
- upload/import of a run manifest and referenced artifacts;
- run summary and provenance view;
- typed prediction panel;
- validation evidence panel;
- candidate/run relationship in the frontend;
- comparison of at least two poses or methods;
- bounded `get_run_summary`, `get_candidate_evidence`, `list_available_artifacts`, and
  `compare_candidates` queries where supported by the current local data model;
- request/capability correlation identifiers without pretending they are durable persistence;
- clear partial/failed run states;
- frontend and Playwright coverage.

This milestone may use temporary/local upload storage. PostgreSQL and shared projects are not required yet.

Exit criteria:

- a user can inspect an imported run without reading raw JSON;
- every displayed normalized value links to method and provenance information;
- failed validation is visually prominent but does not destroy the raw record;
- handlers contain transport concerns only and do not directly execute plugins or perform ad hoc
  storage/database mutations;
- the UI calls the same capability contracts intended for workers and future authorized AI clients;
- low-level CRUD operations are not automatically exposed as capabilities.

## Milestone 4 — Protein, pocket, and pose workspace

Goal: connect molecule review to protein context.

Deliverables:

- PDB/mmCIF import;
- target and protein-structure models;
- Mol* integration;
- chain/residue/ligand selection;
- reference-ligand and box/residue pocket definitions;
- pose visualization in receptor context;
- synchronized candidate, pose, and residue selection;
- distinction between conformer, predicted pose, and experimental complex;
- optional ProLIF interaction import/computation;
- capability-backed target, pocket, pose, and comparison operations with typed inputs/outputs;
- semantic protein-structure, prepared-pocket, pose-set, and interaction artifacts;
- no scientific state that exists only inside viewer components.

Exit criteria:

- a candidate pose can be inspected in its protein pocket;
- receptor, pocket, ligand representation, and pose provenance are visible;
- the existing simple conformer viewer remains functional or has an explicitly tested replacement.

## Milestone 5 — Persistent projects and shared review

Goal: support persistent, multi-user research projects and a production-capable shared deployment on
one Linux server or VM.

Deliverables:

- PostgreSQL and migrations;
- project, target, candidate-set, annotation, and review persistence;
- actor records that distinguish humans, services, plugins, and future agents;
- capability-level authorization with narrowly scoped permissions;
- one generic hierarchical `Run` and `RunAttempt` model for imports, capabilities, reports, plugins,
  model inference, and future agent actions;
- parent/root run, plan/step, correlation, and causation relationships;
- a minimal persisted `Plan` and `PlanStep` model usable by predefined workflows and manual UI plans;
- idempotency records for side-effecting and run-creating commands;
- versioned typed domain events with actor and correlation/causation envelopes;
- typed persistent artifact manifests with semantic type, content digest, producing run, and
  derivation relationships;
- S3-compatible artifact store abstraction;
- local filesystem and S3 implementations;
- RustFS deployment example;
- authentication suitable for a private deployment;
- review status, annotations, and shortlists;
- scientific claims and decision records with supporting/contradicting evidence and human ownership;
- audit events and project decision history;
- a production-oriented Team Server Docker Compose profile using the normal release images;
- documented reverse-proxy/HTTPS integration, persistent volumes, health checks, restart policies,
  backup/restore, schema migration, and release upgrades for the Team Server profile.

Implementation order within the milestone:

1. persistence and artifact-storage kernel;
2. actors, authentication, capability authorization, and idempotency;
3. hierarchical runs/attempts, typed events, and correlation/causation lineage;
4. minimal plans/steps using existing capability definitions;
5. shared review, claims, decisions, and audit history.

Each slice should remain deployable and tested; do not attempt one undifferentiated schema migration.

Exit criteria:

- users can return to projects and imported runs after restart;
- large artifacts are not stored in relational columns;
- storage implementation is not coupled to RustFS-specific APIs;
- migrations and backup guidance are documented;
- retries create attempts beneath the same logical run rather than duplicate scientific records;
- idempotent command retries do not duplicate imports, artifacts, reports, or runs;
- authorization is enforced inside capabilities, not only in the UI or route layer;
- predefined/manual plans can be validated and inspected before any LLM integration;
- claims and decisions remain inspectable independently of comments or future chat history.
- a laboratory can deploy the shared application on one Linux server through the documented Compose
  profile without installing Kubernetes;
- metadata and artifacts can be backed up and restored through a documented, tested procedure;
- Compose configuration and release images do not create contracts that prevent later Helm
  packaging.

## Milestone 6 — First managed scientific campaign

Goal: run one useful, reproducible, lightweight end-to-end workflow.

Recommended workflow:

```text
candidate set
→ RDKit/Meeko preparation
→ AutoDock Vina
→ PoseBusters
→ ProLIF
→ result ingestion
→ visual review
```

Deliverables:

- plugin definition schema;
- plugin input/output filesystem contract;
- fixture/replay executor;
- local OCI executor;
- durable `RunAttempt` lifecycle with provider-job metadata;
- durable plan and plan-step progression using the shared run/attempt model;
- dispatcher/worker process;
- retries, cancellation, timeouts, structured failure handling, and resume after process failure;
- steps that can wait for human approval and resume later;
- persisted approval requests and decisions linked to actor, plan step, and run;
- capability risk classifications and approval policies;
- execution budgets and limits for runtime, retries, CPU/GPU, artifact size, cost, and parallelism;
- idempotency for job-creating commands;
- typed run/artifact/validation events as the source for SSE updates;
- persisted event/outbox delivery suitable for workflow progression and browser projections;
- correlation and causation propagation across capability, run, attempt, executor, plugin, artifact,
  and validation boundaries;
- SSE progress;
- exact container digest and parameters in run provenance;
- reference redocking campaign.

Exit criteria:

- one command/deployment can run the reference campaign reproducibly;
- run-attempt success requires validated output artifacts;
- imported and managed runs produce the same evidence model;
- no model executes inside an HTTP request handler;
- SSE is a projection of durable state and is not the workflow source of truth;
- a workflow can stop for approval or process failure and resume without losing lineage;
- every managed operation is inspectable through the normal UI without AI.
- the reference campaign can run through the Team Server Compose profile and local OCI executor
  without Kubernetes.

## Milestone 7 — Cluster deployment and Kubernetes execution

Goal: provide an advanced, production-capable k3s/Kubernetes deployment and optional Kubernetes Job
execution while preserving the Team Server path and safe execution boundaries.

Deliverables:

- a versioned Helm chart using the same release images, migrations, and application configuration
  concepts as the Team Server Compose profile;
- documented k3s and conformant Kubernetes deployment paths;
- an optional Kubernetes Job executor behind the existing executor contract;
- PostgreSQL and S3-compatible storage configuration, including a RustFS example;
- resource requests/limits;
- liveness, readiness, migration, backup/restore, and release-upgrade guidance;
- ingress/TLS guidance;
- authentication and quotas;
- curated public projects and replayable jobs;
- retention and cleanup policies;
- security review for uploaded files and plugin allowlists;

Exit criteria:

- visitors can explore curated campaigns immediately;
- anonymous users cannot run arbitrary images or consume unbounded compute;
- runs, attempts, workflow state, and artifacts survive API pod restarts;
- the Cluster profile can operate with fixture/replay or a non-Kubernetes remote executor when
  Kubernetes Job execution is disabled;
- Team Server Compose and Cluster Helm installations remain supported from the same release and
  preserve the same application and scientific contracts;
- Helm rendering/schema checks and a k3s smoke path protect the supported cluster configuration;
- capability permissions, risk policies, idempotency, and budgets remain enforced when replicas or
  Kubernetes workers retry work.

## Milestone 8 — Remote GPU models

Goal: add real GPU-backed structure-model execution without coupling the product to one provider.

Deliverables:

- generic remote executor interface;
- one implemented provider adapter;
- Boltz plugin image and golden fixture;
- optional DiffDock plugin;
- genuine successful, partial, and failed Boltz output captures plus import-adapter conformance and
  registration;
- genuine DiffDock captures, conformance, and registration when the optional plugin is included;
- short-lived artifact URLs;
- GPU resource and timeout metadata;
- provider state mapping, retries, and cancellation;
- cost/concurrency controls;
- approval policy for paid or high-cost execution;
- captured successful and failure scenarios.

Exit criteria:

- the same Boltz run contract works through imported output, replay fixture, and live remote execution;
- provider credentials never reach the browser or manifests;
- provider credentials never reach a future AI module;
- failures such as OOM, timeout, missing output, and invalid input are testable.

## Milestone 9 — Institutional execution

Goal: support laboratory and university compute.

Deliverables:

- Slurm agent design and implementation with a real design partner;
- outbound authenticated agent communication;
- Apptainer/container support;
- partition/resource mapping;
- shared-filesystem or object-storage transfer modes;
- operational documentation and compatibility tests.

Exit criteria:

- a real external cluster runs a reference campaign;
- Slurm is not exposed directly to the public internet;
- cluster-specific configuration remains outside scientific contracts;
- institutional execution uses the same capability, plan, run, attempt, event, and artifact contracts
  as local and Kubernetes execution.
- the Slurm agent can serve an appropriately configured Team Server or Cluster control plane; it does
  not require moving the web application onto Kubernetes.

## Milestone 10 — Governed AI assistance

Goal: add optional AI planning and explanation only after capabilities, plans, runs, permissions,
approvals, budgets, events, and bounded project queries are trusted.

Deliverables:

- an AI module inside the modular monolith unless isolation or scale demonstrates a service need;
- a global project assistant and contextual “ask about this” entry points;
- bounded project-context tools backed by application queries, never raw database access;
- typed plan proposals using existing capability IDs and versions;
- plan review/edit/approval UI with risk, runtime, GPU, and cost estimates;
- structured action/result cards linked to normal run, artifact, validation, claim, and decision views;
- agent actor identity, version, model/provider identity, delegating user, permission scope, tool calls,
  token/cost metadata, and approval records;
- explicit human ownership for accepted scientific claims and decisions;
- deterministic replay fixtures for agent tool orchestration without calling an LLM in normal CI.

Exit criteria:

- the agent can invoke only capabilities authorized for its delegating user and granted scope;
- no agent path bypasses validation, authorization, idempotency, risk, approval, budget, run, event, or
  provenance controls;
- an agent can propose a plan but the normal backend validates and executes it;
- the complete workflow and scientific record remain understandable without chat history;
- the product remains fully usable with the AI module disabled.

This milestone does not automatically approve MCP, a vector database, a graph database, autonomous
web research, generated-code execution, or a multi-agent architecture.

## Milestone 11 — Generative and advanced workflows

Goal: extend only after screening and review workflows are trusted.

Possible capabilities:

- one molecular-generation adapter;
- synthesis assessment;
- multi-objective ranking profiles;
- ensemble receptor campaigns;
- active-learning loops;
- experimental observation import.

These are not approved merely by appearing on the roadmap. Each requires renewed user validation and scientific design.

## Cross-cutting requirements

Every milestone should maintain:

- explicit scientific caveats;
- deterministic offline tests;
- generated API contract checks;
- strict typing and linting;
- architecture-boundary tests;
- documented data/license provenance;
- no silent conversion of model output semantics;
- no unrelated infrastructure expansion;
- stable capability IDs and versioned typed inputs/outputs for important operations;
- thin transport handlers and capability-level policy enforcement;
- semantic artifact types and structured provenance relationships;
- one plan/run/attempt model across human, service, plugin, and future agent activity;
- bounded context queries rather than unrestricted data access;
- typed actor, correlation, causation, event, and decision records when their owning milestone exists;
- normal UI inspection for every future agent-invocable operation.
- personal, Team Server, and Cluster packaging preserve the same application and scientific
  contracts;
- control-plane deployment and scientific executor selection remain independent, with provider
  details confined to deployment configuration and executor adapters;
- official Compose and Helm packaging reuse release images and application configuration concepts
  rather than becoming separate product implementations.

## Product validation gates

Before significant expansion beyond imports and review, obtain at least three external users willing to test real outputs.

Continue when users report that Molecule Atlas:

- removes meaningful manual parsing;
- catches invalid or misleading results;
- improves reproducibility;
- makes cross-model comparison easier;
- supports communication with collaborators.

Reconsider the direction when users only seek free hosted GPU execution, do not value provenance/validation, or existing projects solve the same workflow more effectively.
