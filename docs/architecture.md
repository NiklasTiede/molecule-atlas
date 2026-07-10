# Molecule Atlas Architecture

## Architectural goals

Molecule Atlas must support a useful laptop experience, a public or laboratory web deployment, and optional heavy scientific execution without coupling the application to one model, scheduler, cloud, or storage product.

The architecture prioritizes:

- explicit scientific contracts;
- deterministic local development;
- independent scientific runtime environments;
- durable job and artifact provenance;
- S3-compatible storage rather than vendor-specific APIs;
- browser-native scientific review;
- incremental delivery through a modular monolith.

## Current baseline

The current implementation is a ligand-centric React/FastAPI workbench. It loads a bundled candidate set, uses RDKit to validate and enrich molecules, and exposes typed API responses to the frontend. This completed baseline should remain working while the project grows.

Current boundaries are enforced by tests:

```text
main -> api -> services -> chem/adapters -> models
```

Generated OpenAPI types, strict Python typing, frontend tests, Playwright tests, and container smoke tests remain required.

## Target system

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│                            Molecule Atlas Web UI                             │
│                            React + TypeScript                                │
│                                                                              │
│  Molecule explorer   Protein/pocket viewer   Campaign and job views          │
│  Similarity/scaffold Mol* poses/interactions Validation/provenance           │
│  Chemical space      Candidate comparison   Review/annotations/shortlists    │
│                                                                              │
│          TanStack Query · TanStack Table · Plotly · 3Dmol.js · Mol*          │
└──────────────────────────────────┬───────────────────────────────────────────┘
                                   │ HTTPS / REST / SSE
                                   │ Generated OpenAPI types
┌──────────────────────────────────▼───────────────────────────────────────────┐
│                        FastAPI Control Plane                                 │
│                                                                              │
│  Projects       Compounds and sets      Targets and pockets                  │
│  Runs           Poses and predictions   Validation evidence                  │
│  Reviews        Plugin registry         Job lifecycle                        │
│  Provenance     Artifact references     Reports                              │
└───────────────┬─────────────────────┬───────────────────────┬────────────────┘
                │                     │                       │
        ┌───────▼────────┐   ┌────────▼─────────┐   ┌────────▼────────────┐
        │ PostgreSQL     │   │ Artifact store   │   │ Dispatcher/worker   │
        │ metadata/jobs  │   │ filesystem/S3    │   │ durable job state   │
        └────────────────┘   │ RustFS supported │   └────────┬────────────┘
                             └──────────────────┘            │
                                                   Executor interface
                                                             │
                    ┌────────────────────────────────────────▼───────────────┐
                    │ Fixture · Local OCI · Kubernetes · Remote GPU · Slurm │
                    └────────────────────────┬───────────────────────────────┘
                                             │
                    Immutable plugin input/output contracts
                                             │
┌────────────────────────────────────────────▼─────────────────────────────────┐
│ Scientific plugin containers                                                 │
│ RDKit/Meeko · Vina · PoseBusters · ProLIF · Boltz · DiffDock · future tools  │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Modular-monolith structure

Do not introduce microservices by default. The initial persistent application should use one codebase and separate process entry points where operationally useful.

```text
backend/
  app/
    api/
    domains/
      projects/
      chemistry/
      targets/
      evidence/
      campaigns/
      execution/
      review/
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

### FastAPI control plane

FastAPI owns:

- HTTP validation and authorization;
- project and review workflows;
- persistence transactions;
- job submission and state queries;
- pre-signed artifact upload/download flows;
- SSE progress streams;
- OpenAPI generation.

It must not run heavy model inference inside request handlers or FastAPI background tasks.

### Frontend

The frontend is an information-dense scientific workbench. Major views should synchronize selection across tables, molecular depictions, protein/pose visualization, predictions, interactions, and validation evidence.

Keep 3Dmol.js for existing simple conformer viewing. Introduce Mol* for proteins, pockets, complexes, and binding poses. Do not replace the working viewer until Mol* covers the corresponding path.

## Persistence

### Before shared projects

The evidence core and report generation must work on local files with no database. This enables CLI validation, fixtures, and simple web uploads.

### Shared deployment

Use PostgreSQL when projects, annotations, authentication, run history, or durable jobs are introduced.

Store metadata and references in PostgreSQL. Store large scientific artifacts outside the relational database.

### Artifact storage

Define an application-level `ArtifactStore` interface with at least:

- local filesystem implementation;
- S3-compatible implementation.

RustFS is the preferred deployment in the maintainer's k3s environment, but core code must use standard S3 semantics and avoid RustFS-specific coupling.

Remote workers should use short-lived, job-scoped pre-signed URLs rather than permanent object-storage credentials.

## Execution architecture

### Jobs

The application owns a durable internal job record. Provider-specific job IDs and states are mapped into the Molecule Atlas lifecycle.

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

A job is not successful until required output artifacts have been uploaded, checksummed, and validated against the plugin output schema.

### Initial queue

Use PostgreSQL as the first durable queue when persistence exists. A dispatcher can claim queued work with `FOR UPDATE SKIP LOCKED`. Do not introduce Celery, Redis, RabbitMQ, and Kubernetes operators simultaneously without a demonstrated need.

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
- capabilities;
- score semantics;
- licenses;
- golden fixtures.

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

## Deployment modes

### Laptop mode

Docker Compose or native development:

- frontend;
- FastAPI;
- optional worker;
- local filesystem or S3-compatible storage;
- fixture import/replay;
- RDKit and lightweight Vina workflows;
- optional remote GPU executor.

A useful local mode must not require Kubernetes or a GPU.

### k3s demo/laboratory mode

- ingress and TLS;
- frontend and API;
- dispatcher/worker;
- PostgreSQL;
- RustFS through the S3 interface;
- fixture and CPU workers;
- optional remote GPU execution.

Anonymous users must not be allowed to execute arbitrary containers or consume unlimited paid GPU resources. Apply authentication, quotas, allowlists, request limits, and retention policies before live execution is enabled.

### Institutional mode

Support local Kubernetes Jobs, remote GPU providers, and later a Slurm agent. The same run manifest and plugin contracts apply across environments.

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

## Architecture decision process

Major decisions should be recorded under `docs/adr/`. New dependencies or infrastructure should solve a current milestone requirement. Long-term architecture is guidance, not permission to implement every future component immediately.
