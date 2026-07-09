# AGENTS.md

Instructions for coding agents working on Molecule Atlas.

## Project Mission

Molecule Atlas is an open-source, browser-based candidate review workbench for small-molecule design outputs.

The MVP is ligand-centric:

- load a molecule list;
- validate and canonicalize SMILES;
- compute RDKit descriptors, fingerprints, scaffolds, similarity, and simple triage flags;
- show molecules in a table, 2D structure view, detail panel, and basic mouse-rotatable 3D conformer view.

The long-term direction is target-aware review of generated, docked, or model-prioritized candidates, including protein-pocket poses and interaction fingerprints. Do not implement that long-term scope until the MVP is solid.

Read `docs/product-vision.md` before making product or architecture decisions.

## Non-Negotiable MVP Boundaries

Do not implement these in the MVP:

- docking engines;
- Boltz, Boltzina, DiffDock, GNINA, AutoDock Vina, or other model inference;
- GPU job orchestration;
- protein-pocket visualization as a required feature;
- retrosynthesis route planning;
- real ADME/PK or toxicity prediction claims;
- medicinal chemistry recommendations;
- Kubernetes or cloud deployment.

It is acceptable to design data structures that can later support `target_id`, `job_id`, `model_name`, `model_confidence`, `pose_file`, and provenance metadata.

## Stack Decisions

Backend:

- Python 3.13
- FastAPI
- Pydantic
- RDKit
- pandas or Polars
- scikit-learn for PCA
- pytest

Frontend:

- React
- TypeScript
- Vite
- TanStack Table
- backend-generated RDKit SVGs for 2D molecule depictions
- 3Dmol.js for the MVP small-molecule 3D conformer viewer
- Mol* later for protein and protein-ligand visualization
- Vitest and Testing Library for component tests
- Playwright for browser-level e2e tests once real screens exist

Persistence:

- MVP: bundled files plus in-memory processing.
- Next step if needed: file-backed uploaded candidate sets.
- Later: DuckDB or SQLite for local analytics.
- Postgres only if multi-user projects, annotations, auth, or shared job history become real requirements.

Do not add Java for the MVP. RDKit's heavy chemistry work is already native code under the Python API, and Python matches the target role and the scientific ecosystem.

## Expected Repository Shape

Planned structure:

```text
backend/
  app/
    main.py
    api/
    chem/
    models/
    services/
  tests/
frontend/
  src/
    api/
    components/
    views/
data/
docs/
```

Keep modules small and responsibility-focused. Prefer clear service boundaries over large files that mix API, chemistry, and UI concerns.

## Development Workflow

Use test-driven development for backend behavior:

1. Write a focused failing test.
2. Run the exact test and confirm it fails for the expected reason.
3. Implement the smallest useful code.
4. Run the focused test.
5. Run the relevant broader test suite.
6. Commit only coherent changes when asked to commit.

For frontend work:

1. Do a dedicated design pass before building major UI screens.
2. Keep visual components small and composable.
3. Use domain libraries for molecular rendering instead of hand-rolling chemistry rendering with raw canvas or Three.js.
4. Verify layout in browser screenshots once a dev server exists.

## Commands

Backend commands:

```bash
cd backend
UV_CACHE_DIR=../.uv-cache uv run pytest
UV_CACHE_DIR=../.uv-cache uv run pytest tests/test_api_health.py -v
UV_CACHE_DIR=../.uv-cache uv run ruff check .
UV_CACHE_DIR=../.uv-cache uv run ruff format --check .
UV_CACHE_DIR=../.uv-cache uv run pyright
UV_CACHE_DIR=../.uv-cache uv run python -m scripts.export_openapi
UV_CACHE_DIR=../.uv-cache uv run uvicorn app.main:app --reload
```

Frontend commands:

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

Root-level convenience commands:

```bash
make backend-test
make backend-lint
make backend-typecheck
make backend-openapi
make backend-dev
make frontend-test
make frontend-lint
make frontend-build
make frontend-api-types
make frontend-dev
make frontend-e2e
make test
make lint
make api-contract-check
make e2e
```

If commands change, update `AGENTS.md` in the same change.

## Chemistry Implementation Notes

Use RDKit for chemistry semantics:

- SMILES parsing and canonicalization;
- descriptor calculation;
- Morgan fingerprints;
- Tanimoto similarity;
- Bemis-Murcko scaffolds;
- 2D depictions;
- simple 3D conformer generation.

Treat invalid SMILES as data quality issues, not server crashes. Return structured validation notes that the UI can display.

Distinguish clearly between:

- 2D depictions;
- generated 3D conformers;
- docked binding poses;
- experimentally observed protein-ligand structures;
- model-predicted poses.

For the MVP, the 3D viewer shows conformers, not binding poses.

## API Design Notes

Use typed Pydantic models for all request and response payloads.

Prefer candidate-oriented names:

- `Candidate`
- `CandidateSet`
- `DescriptorSet`
- `SimilarityNeighbor`
- `ValidationNote`
- `TriageFlags`

Avoid names that imply unsupported claims, such as `Drug`, `Lead`, `ActiveCompound`, or `SafeMolecule`.

Keep APIs simple at first:

- list bundled candidate set;
- upload or process candidate CSV later;
- get candidate detail;
- compute/query similarity;
- get generated conformer data or structure file for viewer.

## Frontend Design Notes

The first real UI should be a workbench, not a landing page.

Likely layout:

- left/main: molecule table with filters and sorting;
- right: selected candidate detail panel;
- detail tabs or sections: 2D, 3D, descriptors, nearest neighbors, validation notes;
- later: chemical-space map and scaffold summaries.

Use restrained, information-dense UI suitable for scientific review. Avoid marketing-style hero sections, decorative gradients, and oversized cards.

Do not put cards inside cards. Use cards only for repeated molecule/detail items or genuinely framed tools.

## Testing Expectations

Backend tests should cover:

- valid SMILES parsing;
- invalid SMILES handling;
- canonical SMILES stability for known examples;
- descriptor calculation for known molecules;
- fingerprint generation;
- Tanimoto similarity ordering;
- Murcko scaffold extraction;
- triage flag calculation;
- conformer generation success and failure paths;
- API response schemas for main endpoints.
- API not-found, invalid-candidate, and expected chemistry failure responses;
- enforced backend import directions and third-party dependency ownership;
- Python-version alignment across project metadata, lockfile, tooling, Docker, and CI;
- presence of all required lint, type, test, browser, and container gates in CI.

Frontend tests should cover:

- API client parsing;
- table rendering with candidate rows;
- filter and sort behavior;
- selected candidate detail rendering;
- empty/error/loading states.
- Playwright e2e smoke tests for loading the workbench, selecting a candidate, seeing detail content, opening the 3D conformer tab, seeing the chemical-space plot, and keeping invalid SMILES non-fatal.

Use a tiny deterministic fixture dataset for tests. Do not make tests depend on external network calls.

CI must run backend and frontend static checks and tests, generated API contract
checks, Playwright browser tests, container configuration checks, and the
Compose production-image smoke test.

## Data And Scientific Claims

Document dataset provenance in `data/README.md` once data is added.

Any demo scores must be clearly marked as demo, mock, or sourced from a documented method. Do not imply measured affinity, clinical safety, synthetic feasibility, or biological activity unless the dataset supports it.

Rule-based flags such as Lipinski or Veber checks are triage signals only. They are not pass/fail drug discovery decisions.

## Documentation Expectations

Keep these documents current:

- `README.md`: setup, project purpose, screenshots, scientific caveats;
- `docs/architecture.md`: backend/frontend/data flow and future extension points;
- `data/README.md`: dataset source and license/provenance;
- `AGENTS.md`: commands and agent workflow.

## Git Hygiene

The worktree may contain user changes. Do not revert unrelated changes.

Before editing, inspect relevant files. Before finalizing, run the most relevant available tests or explain why they cannot be run.

Do not commit unless explicitly asked.
