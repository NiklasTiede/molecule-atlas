# AGENTS.md

Instructions for coding agents working on Molecule Atlas.

## Mission

Molecule Atlas is an open-source, self-hosted visual workbench for exploring small molecules, inspecting protein-ligand results, validating computational evidence, and running reproducible structure-based discovery workflows.

It is not a drug-discovery decision engine. It helps researchers inspect and communicate computational hypotheses while preserving scientific caveats, provenance, and score semantics.

Before product or architecture work, read:

1. `docs/product-vision.md`
2. `docs/roadmap.md`
3. `docs/architecture.md`
4. `docs/domain-model.md`
5. `docs/scientific-contracts.md`
6. `docs/ai-first-readiness.md`

## Milestone discipline

Implement the earliest incomplete roadmap milestone unless the user explicitly selects another one.

Do not implement future infrastructure merely because it appears in the long-term architecture. Each change should solve a current acceptance criterion and preserve the completed ligand-centric workbench.

The immediate next milestone is real-output import and validation: typed Boltz and DiffDock adapters,
PoseBusters-backed checks, semantic artifact outputs, replay fixtures, and explicit interpretation.

## Non-negotiable scientific rules

- Do not call candidates drugs, leads, active compounds, or safe molecules without supporting experimental data.
- Do not flatten docking energy, pose confidence, structure confidence, binder probability, predicted affinity, and physical validity into one generic score.
- Distinguish 2D depictions, conformers, predicted poses, docked poses, and experimental complexes.
- Preserve raw upstream artifacts and normalization lineage.
- Represent failed and partial runs explicitly.
- Missing provenance must produce warnings, not invented metadata.
- Validation results are evidence; do not silently hide failures.
- Model predictions do not establish biological activity, selectivity, safety, synthesizability, or clinical value.

## Stack decisions

Backend and portable core:

- Python 3.13 for the application unless a scientific plugin requires its own pinned runtime;
- FastAPI for HTTP delivery;
- Pydantic for contracts;
- RDKit for chemistry semantics;
- pytest, Ruff, and strict Pyright;
- SQLAlchemy/Alembic only when the persistence milestone begins.

Frontend:

- React, TypeScript, and Vite;
- TanStack Table and generated OpenAPI types;
- 3Dmol.js for the existing conformer viewer;
- Mol* for protein, pocket, complex, and pose visualization;
- Vitest/Testing Library and Playwright.

Storage and deployment:

- local files before persistence;
- PostgreSQL for shared metadata and durable jobs when required;
- an S3-compatible artifact abstraction, with RustFS supported as a deployment;
- Docker Compose as the primary personal and production-capable single-server Team Server
  deployment when its roadmap milestone arrives;
- Helm on k3s/Kubernetes as the advanced cluster deployment only in the corresponding roadmap
  milestone;
- shared release images and application contracts across Compose and Helm packaging;
- application deployment and scientific executor selection remain independent.

Scientific execution:

- heavy tools run in independently versioned OCI plugin containers;
- FastAPI handlers never run heavy inference;
- provider-specific APIs remain behind executor adapters;
- do not add Java or rewrite mature Python scientific libraries.

## Architecture boundaries

Keep the project a modular monolith. Prefer small, responsibility-focused modules and enforced import directions.

The portable evidence core must not depend on FastAPI, PostgreSQL, Kubernetes, or a GPU. The CLI, API, workers, and reports should reuse the same schemas and adapters.

Do not make Kubernetes a prerequisite for personal or shared laboratory use. Do not assume that a
Kubernetes control-plane deployment must execute scientific work through Kubernetes Jobs, or that a
Compose deployment may use only local execution. Select fixture, local OCI, Kubernetes, remote GPU,
or Slurm execution through provider-neutral adapters and explicit deployment policy when the owning
milestone introduces each executor.

The React UI and a future AI agent are clients of the same typed application capabilities. FastAPI
handlers translate HTTP and authentication context; they do not own business workflows. Workers,
predefined workflows, and a future AI module reuse the same capability layer.

- Keep AI outside scientific plugins.
- Never give an AI direct database, object-storage, executor, cluster, or provider access.
- Do not automatically expose CRUD methods as agent tools.
- Give important capabilities stable IDs, versions, typed inputs/outputs, permission requirements,
  side-effect semantics, and risk metadata.
- Use the same plan, run, attempt, artifact, validation, claim, and decision concepts for human,
  service, plugin, and future agent activity.
- Record agent actors separately from delegating humans.
- Keep important plans, claims, decisions, approvals, and results in structured application state,
  not only chat history.
- Keep the full product usable without AI.

Do not move working code merely to resemble the target directory tree. Refactor when a feature needs a clear boundary and add architecture tests for that boundary.

Before implementing an important operation, ask whether it can be represented as a typed,
authorized, observable, reproducible application capability that both the UI and a future AI agent
can invoke. If the current milestone does not own the required persistence or execution substrate,
document the future contract and implement only the current acceptance criterion.

## Development workflow

For backend/core behavior:

1. Inspect relevant implementation and tests.
2. Write a focused failing test.
3. Confirm it fails for the expected reason.
4. Implement the smallest coherent behavior.
5. Run focused tests.
6. Run relevant broader checks.
7. Update documentation/contracts in the same change.

For frontend work:

1. Perform a design pass for major screens.
2. Keep components small and domain-oriented.
3. Use molecular visualization libraries rather than hand-rolled rendering.
4. Include loading, empty, partial, failed, and invalid-data states.
5. Verify important workflows through Playwright and browser screenshots.

Do not commit unless explicitly asked. Do not revert unrelated user changes.

## Commands

Backend:

```bash
cd backend
UV_CACHE_DIR=../.uv-cache uv run pytest
UV_CACHE_DIR=../.uv-cache uv run ruff check .
UV_CACHE_DIR=../.uv-cache uv run ruff format --check .
UV_CACHE_DIR=../.uv-cache uv run pyright
UV_CACHE_DIR=../.uv-cache uv run python -m scripts.export_openapi
UV_CACHE_DIR=../.uv-cache uv run molecule-atlas adapters
UV_CACHE_DIR=../.uv-cache uv run molecule-atlas inspect ../data/evidence-fixtures/succeeded
UV_CACHE_DIR=../.uv-cache uv run molecule-atlas schema --output ../schemas/run-manifest/0.1.0.schema.json
UV_CACHE_DIR=../.uv-cache uv run uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
npm run build
npm run lint
npm run generate:api
npm test
npm run e2e
```

Root:

```bash
make test
make lint
make api-contract-check
make evidence-contract-check
make e2e
make container-build
make container-smoke
```

If commands change, update this file in the same change.

## Testing expectations

Tests must be deterministic and offline unless explicitly marked as external integration tests.

Maintain coverage for:

- valid and invalid molecular input;
- canonicalization and descriptors;
- fingerprints, similarity, scaffolds, and conformers;
- strict API schemas and failure responses;
- generated OpenAPI/TypeScript contracts;
- architecture import boundaries;
- frontend loading/error/empty states;
- browser workbench behavior;
- production container smoke tests.

As new milestones are implemented, add tests for:

- run-manifest versioning and round trips;
- artifact hashing;
- typed prediction semantics;
- successful, partial, and failed imports;
- validator normalization and raw-output traceability;
- plugin input/output contracts;
- durable run/attempt state transitions;
- executor conformance;
- storage implementation conformance;
- stable capability IDs and explicit OpenAPI operation IDs;
- typed capability inputs and outputs;
- capability-level authorization and idempotency;
- hierarchical run/attempt lineage and actor identity;
- plan validation, approval policy, budgets, and resume behavior;
- typed domain-event envelopes and correlation/causation IDs.

Use tiny golden fixtures. Do not make normal CI download models or call external services.

## Documentation and decision records

Keep current:

- `README.md`: purpose, current capabilities, setup, caveats;
- `docs/product-vision.md`: durable product intent;
- `docs/roadmap.md`: milestone order and acceptance criteria;
- `docs/architecture.md`: current and target architecture;
- `docs/domain-model.md`: scientific concepts and relationships;
- `docs/scientific-contracts.md`: manifests, predictions, validation, plugins;
- `docs/ai-first-readiness.md`: shared capabilities, plans/runs, actors, events, and deferred AI scope;
- `data/README.md`: source, license, and provenance for fixtures;
- `AGENTS.md`: coding-agent rules and commands.

Create an ADR under `docs/adr/` for major irreversible or cross-cutting decisions. Do not use ADRs for ordinary implementation details.

## Completion checklist

Before finalizing a change:

- state which roadmap criterion it advances;
- run the most relevant tests and static checks;
- update generated API types when contracts change;
- preserve scientific caveats and raw provenance;
- preserve or introduce the shared capability boundary when the feature exposes an important action;
- state the capability ID, kind, side effects, and policy metadata for new public operations;
- document new data, tools, models, licenses, and deployment requirements;
- preserve the supported personal, Team Server, and Cluster profiles when changing deployment or
  executor behavior;
- explain any check that could not be run.
