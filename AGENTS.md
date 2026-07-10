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

## Milestone discipline

Implement the earliest incomplete roadmap milestone unless the user explicitly selects another one.

Do not implement future infrastructure merely because it appears in the long-term architecture. Each change should solve a current acceptance criterion and preserve the completed ligand-centric workbench.

The immediate next milestone after the current MVP is the portable evidence core: versioned run manifests, artifacts, typed predictions, validation results, reports, fixtures, and a CLI that requires no GPU or database.

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
- Docker Compose for local use;
- k3s/Kubernetes only in the corresponding roadmap milestone.

Scientific execution:

- heavy tools run in independently versioned OCI plugin containers;
- FastAPI handlers never run heavy inference;
- provider-specific APIs remain behind executor adapters;
- do not add Java or rewrite mature Python scientific libraries.

## Architecture boundaries

Keep the project a modular monolith. Prefer small, responsibility-focused modules and enforced import directions.

The portable evidence core must not depend on FastAPI, PostgreSQL, Kubernetes, or a GPU. The CLI, API, workers, and reports should reuse the same schemas and adapters.

Do not move working code merely to resemble the target directory tree. Refactor when a feature needs a clear boundary and add architecture tests for that boundary.

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
- durable job state transitions;
- executor conformance;
- storage implementation conformance.

Use tiny golden fixtures. Do not make normal CI download models or call external services.

## Documentation and decision records

Keep current:

- `README.md`: purpose, current capabilities, setup, caveats;
- `docs/product-vision.md`: durable product intent;
- `docs/roadmap.md`: milestone order and acceptance criteria;
- `docs/architecture.md`: current and target architecture;
- `docs/domain-model.md`: scientific concepts and relationships;
- `docs/scientific-contracts.md`: manifests, predictions, validation, plugins;
- `data/README.md`: source, license, and provenance for fixtures;
- `AGENTS.md`: coding-agent rules and commands.

Create an ADR under `docs/adr/` for major irreversible or cross-cutting decisions. Do not use ADRs for ordinary implementation details.

## Completion checklist

Before finalizing a change:

- state which roadmap criterion it advances;
- run the most relevant tests and static checks;
- update generated API types when contracts change;
- preserve scientific caveats and raw provenance;
- document new data, tools, models, licenses, and deployment requirements;
- explain any check that could not be run.
