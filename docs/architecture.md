# Molecule Atlas Architecture

## Architectural goals

Molecule Atlas must support a useful laptop experience, a shared single-server research deployment,
an advanced cluster deployment, and optional heavy scientific execution without coupling the
application to one model, scheduler, cloud, storage product, or control-plane packaging.

The architecture prioritizes:

- explicit scientific contracts;
- deterministic local development;
- independent scientific runtime environments;
- durable job and artifact provenance;
- S3-compatible storage rather than vendor-specific APIs;
- browser-native scientific review;
- one typed application capability boundary for the UI, workers, and future AI clients;
- one plan/run/attempt and provenance model across imports, execution, reports, and automation;
- capability-level authorization, policy, idempotency, and audit rather than prompt-based controls;
- independently selectable application-deployment and scientific-execution topologies;
- incremental delivery through a modular monolith.

## Current baseline

The current implementation combines the ligand-centric React/FastAPI workbench with a portable
evidence core. The workbench loads a bundled candidate set, uses RDKit to validate and enrich
molecules, and exposes typed API responses to the frontend. The separately packaged evidence core
validates versioned local run manifests, hashes artifacts, audits provenance, and produces canonical
JSON, JSON Schema, and deterministic Markdown or self-contained HTML reports without importing
FastAPI.

Current boundaries are enforced by tests:

```text
main -> api -> services -> chem/adapters -> models
```

The current service layer is a useful precursor but is not yet a formal capability catalog. When
Milestone 3 introduces evidence import over HTTP, add the application capability boundary around new
operations and migrate existing services only when a feature requires it.

Generated OpenAPI types, strict Python typing, frontend tests, Playwright tests, and container smoke tests remain required.

The implemented package boundary is:

```text
FastAPI application (app) ───────┐
                                 ├──> molecule_atlas.evidence (Pydantic + standard library)
molecule-atlas CLI ──────────────┘
```

`molecule_atlas.evidence` has no dependency on `app`, FastAPI, RDKit, persistence, schedulers, GPU
runtimes, or model providers. The current FastAPI API does not yet expose evidence endpoints; web
import belongs to Milestone 3.

## Target system

```text
┌───────────────────────┐
│ React workbench       │──HTTP──> FastAPI adapters ─────┐
│ generated API client  │          authn + HTTP mapping  │
└───────────────────────┘                                │
                                                         │
┌───────────────────────┐                                ▼
│ Future AI module      │──scoped in-process/API call────┤
└───────────────────────┘                                │
                                                         │
┌───────────────────────┐                                │
│ Workers / workflows   │──typed invocation──────────────┘
└───────────────────────┘
                                    ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ Application capabilities                                                     │
│ typed input/output · authorization · risk/approval · idempotency · budgets   │
│ bounded queries · commands/jobs/proposals · actor and correlation context    │
└──────────────────────────────────┬───────────────────────────────────────────┘
                                   ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ Domain and workflow model                                                    │
│ Project · Plan/PlanStep · Run/RunAttempt · Artifact · Validation             │
│ Evidence · Claim · Decision · typed domain events                            │
└───────────────┬─────────────────────┬───────────────────────┬────────────────┘
                │                     │                       │
        ┌───────▼────────┐   ┌────────▼─────────┐   ┌────────▼────────────┐
        │ PostgreSQL     │   │ Artifact store   │   │ Dispatcher/worker   │
        │ state/events   │   │ filesystem/S3    │   │ durable progression │
        └────────────────┘   └──────────────────┘   └────────┬────────────┘
                                                             ▼
                    ┌──────────────────────────────────────────────────────┐
                    │ Executor adapters                                   │
                    │ Fixture · Local OCI · Kubernetes · Remote GPU · Slurm│
                    └────────────────────────┬─────────────────────────────┘
                                             ▼
                    ┌──────────────────────────────────────────────────────┐
                    │ Versioned scientific plugins                        │
                    │ semantic artifacts · raw outputs · no AI logic      │
                    └──────────────────────────────────────────────────────┘
```

## Modular-monolith structure

Do not introduce microservices by default. The initial persistent application should use one codebase and separate process entry points where operationally useful.

```text
backend/
  core/
    pyproject.toml
    src/molecule_atlas/evidence/
  app/
    api/
    application/
      capabilities/
      plans/
      runs/
      policies/
      events/
    domains/
      projects/
      chemistry/
      targets/
      evidence/
      campaigns/
      execution/
      review/
      scientific_memory/
    infrastructure/
      database/
      artifacts/
      executors/
      authentication/
    workers/
    settings.py
    main.py
  migrations/
  tests/

frontend/
  src/
    api/
    components/
    features/
      candidates/
      targets/
      runs/
      poses/
      validation/
      review/
    routes/
    types/

plugins/
  fixtures/
  vina/
  posebusters/
  prolif/
  boltz/
  diffdock/

schemas/
  run-manifest/
  plugin/
  artifact/
  prediction/

deploy/
  compose/
  helm/
```

The exact migration should happen incrementally. Do not reorganize working code merely to match this tree before a feature needs the boundary.

## Core layers

### Core Python package

The portable scientific evidence core should be usable without FastAPI. It owns:

- run-manifest schemas;
- artifact hashing and inventory;
- typed prediction semantics;
- validation-result schemas;
- model registry metadata;
- output adapters;
- report generation.

The CLI, HTTP API, and workers should call this same package rather than duplicate parsing rules.

Milestone 1 implements this layer as the `molecule-atlas-core` distribution in `backend/core`.
Milestone 2 introduces a typed, versioned adapter request/result boundary and explicit compatibility
catalog around the local manifest adapter before registering provider- or scientific-tool-specific
adapters. It also adds a separately versioned semantic artifact manifest with logical names,
content-addressed identity, and derivation validation without mutating `RunManifest 0.1.0`. An
adapter is advertised only after pinned upstream layouts have offline fixture coverage.

The first upstream normalization implementation is an unregistered Boltz 2.2.1 adapter. It returns
adapter-result contract `0.2.0`, which contains both manifests and validates their artifact
inventories as one immutable boundary. Its current offline fixture proves the upstream-documented
layout and field semantics but is explicitly not model output. Registry and CLI exposure wait for a
genuine redistributable capture, so compatibility discovery never overstates what CI has verified.

The same rule applies to the unregistered DiffDock 1.1.3 adapter. It converts existing ranked SDF
files into typed pose-confidence evidence and semantic ligand-structure artifacts without loading
DiffDock, PyTorch, a model checkpoint, or GPU support. Boltz and DiffDock now demonstrate two
scientifically different normalization paths in core tests, but neither is a public capability or
registered CLI adapter until genuine redistributable fixtures establish operational compatibility.

PoseBusters follows a separate optional-validator boundary. Portable normalization reads a captured
CSV report with only the standard library and core contracts. The optional runner lazily imports the
exactly pinned upstream package, uses single-process execution, requests a full report, and
serializes that report deterministically before returning through the same normalization path. The
raw report is the traceable source of every check; the runner does not execute in FastAPI and does
not introduce a GPU or default core dependency.

### Application capability layer

The application layer owns meaningful operations used by transports, workers, predefined workflows,
and a future AI module. It depends on domain/core contracts and infrastructure ports, not on FastAPI.

A capability definition includes a stable ID/version, semantic kind, typed input/output, required
permissions, side effects, risk, cost/runtime class, and support for idempotency, cancellation, and
dry run. Capability handlers receive an explicit actor and correlation context. They perform domain
validation and authorization before state changes or execution requests.

Queries are bounded reads. Commands are explicit state changes. Jobs are asynchronous commands
represented through the shared run model. Proposals require validation or approval. Internal CRUD
and repository methods are not automatically capabilities and are not automatically exposed to a
future agent.

The capability layer is introduced with the first evidence-import HTTP workflow in Milestone 3.
Avoid creating a speculative global framework in Milestone 2; real adapters should first return
typed, semantic outputs that capability handlers can compose.

### FastAPI control plane

FastAPI owns:

- HTTP parsing and response mapping;
- authentication and actor-context extraction;
- mapping capability errors to documented HTTP failures;
- HTTP delivery for capability-issued pre-signed artifact upload/download flows;
- SSE progress streams;
- OpenAPI generation.

FastAPI handlers call application capabilities. They do not contain domain workflows, authorize only
in route decorators, mutate repositories directly, invoke plugins, or run heavy inference in request
handlers or FastAPI background tasks. Important endpoints set explicit stable OpenAPI `operation_id`
values based on capability IDs.

### Frontend

The frontend is an information-dense scientific workbench. Major views should synchronize selection across tables, molecular depictions, protein/pose visualization, predictions, interactions, and validation evidence.

Keep 3Dmol.js for existing simple conformer viewing. Introduce Mol* for proteins, pockets, complexes, and binding poses. Do not replace the working viewer until Mol* covers the corresponding path.

Viewer state is not scientific state. Plans, parameters, selections that affect execution, claims,
decisions, validation issues, and AI proposals must be represented by typed backend records and
normal views. The product remains fully usable when any future AI module is disabled.

## Persistence

### Before shared projects

The evidence core and report generation must work on local files with no database. This enables CLI validation, fixtures, and simple web uploads.

### Shared deployment

Use PostgreSQL when projects, annotations, authentication, run history, or durable jobs are introduced.

Store metadata and references in PostgreSQL. Store large scientific artifacts outside the relational database.

Persistence introduces actors, capability authorization, idempotency, plans/steps, hierarchical
runs/attempts, typed events, semantic artifact relationships, scientific claims, and decisions before
an AI module is allowed to orchestrate work. Chat history is not a substitute for these records.

### Artifact storage

Define an application-level `ArtifactStore` interface with at least:

- local filesystem implementation;
- S3-compatible implementation.

RustFS is the preferred deployment in the maintainer's k3s environment, but core code must use standard S3 semantics and avoid RustFS-specific coupling.

Remote workers should use short-lived, job-scoped pre-signed URLs rather than permanent object-storage credentials.

## Execution architecture

### Runs, attempts, and provider jobs

The application owns one logical `Run` for a capability invocation. A `RunAttempt` represents one
concrete import or execution attempt, including retries. A provider job ID and provider-specific
state are operational fields attached to an attempt; they are not a separate scientific result model.

The same run hierarchy covers imports, local capabilities, reports, scientific plugins, model
inference, and future agent actions. Runs carry capability and plan references, actor, parent/root,
idempotency, correlation, and causation IDs. Attempts carry executor/plugin identity, runtime,
attempt-specific artifacts, logs, and failure details.

Recommended states:

```text
created
queued
preparing
submitted
running
collecting_outputs
validating_outputs
succeeded
failed
cancelling
cancelled
```

A run attempt is not successful until required output artifacts have been uploaded, checksummed, and
validated against the plugin output schema. The logical run derives its state from attempts and
workflow policy rather than hiding retry history.

### Initial queue

Use PostgreSQL as the first durable queue when persistence exists. A dispatcher can claim queued
attempts with `FOR UPDATE SKIP LOCKED`. Plan and step state must survive process failure, approval
waits, and retries. SSE is a projection of durable typed events, not the source of truth. Do not
introduce Celery, Redis, RabbitMQ, a workflow engine, and Kubernetes operators simultaneously without
a demonstrated need.

### Executor contract

Executors translate a provider-neutral request into an execution environment.

```text
FixtureExecutor
LocalOciExecutor
KubernetesJobExecutor
RemoteGpuExecutor
SlurmAgentExecutor
```

Campaign and evidence domains must not depend on provider APIs.

Executors receive validated attempt requests from the dispatcher. A future AI module never calls an
executor or provider adapter directly.

### Slurm

A hosted Molecule Atlas instance must not connect directly to an internet-exposed Slurm controller. Use a small agent deployed inside the institution that initiates outbound authenticated communication, submits jobs, and uploads results.

## Plugin contract

Each scientific plugin is independently versioned and containerized. It declares:

- adapter ID and version;
- upstream tool/version/commit;
- image digest;
- input and output schemas;
- command;
- resource requirements;
- plugin feature declarations, distinct from application capability IDs;
- score semantics;
- licenses;
- golden fixtures;
- typed semantic result and artifact contracts.

Filesystem convention:

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

The plugin adapter normalizes upstream results but never discards or rewrites the original evidence without retaining traceability.

Plugin results identify logical artifact names, semantic artifact types, media types, schema
versions, and paths. They do not return an untyped list of filenames. Plugins remain computational
tools and never contain AI planning, approval, authorization, or project-decision logic.

## Future AI module

Do not create an AI microservice now. After the capability, plan, run, authorization, approval,
budget, event, and bounded-query foundations exist, an initial AI module may live inside the modular
monolith and call the same application capabilities as other clients.

The module can be extracted later for demonstrated independent scaling, stronger isolation, multiple
agent workers, or provider-specific runtime needs. Whether in-process or remote, it receives a
delegating actor and narrowly scoped capabilities. It does not receive database, object-store,
executor, cluster, or provider credentials.

An LLM proposes typed plans and explanations. The backend validates plan dependencies, permissions,
risk, approvals, idempotency, budgets, and execution. Agent identity, version, model/provider,
delegating user, tool calls, cost, and approval records remain auditable. The UI must expose the same
plan, run, artifact, validation, claim, and decision records without requiring chat history.

## Deployment modes

Application deployment answers where the web control plane, durable state, and workers run.
Scientific execution answers where a particular plugin attempt runs. These are independent
decisions connected through the provider-neutral executor contract. See ADR 0002 for the durable
deployment and execution decision.

Installing the application on Kubernetes does not require every scientific operation to use a
Kubernetes Job. Installing the application with Compose does not restrict it to local computation.
Executor availability is selected explicitly through configuration, authorization, policy, and
infrastructure credentials; it is not inferred from the control-plane deployment profile.

### Personal profile

Docker Compose or native development:

- frontend;
- FastAPI;
- optional worker;
- local filesystem or S3-compatible storage;
- fixture import/replay;
- RDKit and lightweight Vina workflows;
- optional remote GPU executor.

A useful local mode must not require Kubernetes or a GPU.

### Team Server profile

The recommended shared deployment for most laboratories and small biotechnology teams is a
production-oriented Docker Compose stack on one Linux server or VM:

- reverse proxy with documented HTTPS integration;
- frontend and API;
- dispatcher/worker when managed execution exists;
- PostgreSQL when shared persistence exists;
- local filesystem or S3-compatible artifact storage;
- authentication and capability-level authorization;
- persistent volumes, health checks, restart policies, and resource guidance;
- documented backup, restore, schema migration, and release-upgrade procedures.

Scientists use the normal browser workbench; they do not need Docker or server access. The operator
may be a technically capable researcher, research software engineer, or local IT administrator.

This profile is production-capable for a single host, but it does not claim host-level high
availability. Backups must be restorable outside the failed host. Heavy work can use local OCI
execution within configured limits or be delegated to remote GPU, Kubernetes, or Slurm executors.

### Cluster profile

The advanced deployment for research IT groups and organizations that already operate k3s or
another conformant Kubernetes platform uses Helm and the same application images and contracts as
the Team Server profile:

- ingress and TLS;
- frontend and API;
- dispatcher/worker;
- PostgreSQL, deployed or externally managed according to operator policy;
- S3-compatible artifact storage, including a documented RustFS option;
- fixture and CPU workers;
- optional Kubernetes Job execution;
- optional remote GPU execution.

Anonymous users must not be allowed to execute arbitrary containers or consume unlimited paid GPU resources. Apply authentication, quotas, allowlists, request limits, and retention policies before live execution is enabled.

Single-node k3s improves packaging and reconciliation but does not by itself provide host-level high
availability. Highly available deployments require an appropriate multi-node control plane,
database, storage, ingress, and backup design.

### Institutional execution

Institutional compute is an executor topology rather than a separate web-application deployment.
Support local or remote Kubernetes Jobs, remote GPU providers, and later a Slurm agent from an
appropriately configured Team Server or Cluster installation. The same capability, run, manifest,
plugin, artifact, and validation contracts apply across environments.

### Release and configuration parity

Official Compose and Helm packaging should consume the same immutable application images, schema
migrations, health endpoints, and application configuration model. Environment-specific resources
such as ingress, volumes, secrets, service accounts, and storage classes remain deployment adapters
rather than domain concerns.

Deployment verification should eventually cover a Team Server Compose smoke/upgrade path and Helm
rendering plus a k3s smoke/upgrade path. Executor conformance tests remain separate so adding or
changing an executor does not require a new scientific result model.

## Security boundaries

Treat uploaded structures and model outputs as untrusted data.

- validate file type and size;
- never execute uploaded code;
- never permit arbitrary image names in public deployments;
- isolate scientific containers;
- use restricted service accounts and network policies where available;
- avoid exposing storage credentials;
- redact secrets from logs and manifests;
- preserve audit events for privileged actions.
- enforce permissions, idempotency, risk, approvals, and budgets inside application capabilities;
- distinguish human, service, plugin, and agent actors;
- never expose direct database, storage, executor, cluster, or provider credentials to an AI module;
- do not rely on prompts to enforce security or scientific policy;
- avoid placing sensitive scientific inputs in LLM requests, traces, or logs without explicit scope
  and policy.

## Architecture decision process

Major decisions should be recorded under `docs/adr/`. New dependencies or infrastructure should solve a current milestone requirement. Long-term architecture is guidance, not permission to implement every future component immediately.

See `docs/ai-first-readiness.md` and ADR 0001 for the capability, orchestration, and deferred-AI
rules. See ADR 0002 for the supported deployment profiles and executor independence.
