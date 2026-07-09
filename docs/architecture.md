# Molecule Atlas Architecture

## MVP Architecture

The backend is a FastAPI service with pure RDKit-backed chemistry modules. It loads a bundled candidate CSV into memory, validates structures, computes descriptors, fingerprints, scaffolds, similarity neighbors, 2D SVG depictions, 3D conformer mol blocks, and a PCA projection.

The frontend is a Vite React app. It fetches the demo candidate set from the backend and renders a workbench with a candidate table, selected-candidate detail panel, molecule depictions, 3D conformer viewer, triage flags, nearest neighbors, and chemical-space plot.

## Data Flow

1. `data/demo_candidates.csv` provides the candidate records.
2. `candidate_csv.py` normalizes pandas records into strict `CandidateInput` models.
3. `candidate_repository.py` validates and enriches each typed record.
4. `candidates.py` exposes typed API responses.
5. FastAPI generates `frontend/openapi.json`, which generates the frontend API types.
6. `frontend/src/api/candidates.ts` fetches the candidate set, projection, and conformer data.
7. React components render table, detail, molecular views, and projection.

## Backend Boundaries

- `backend/app/chem/`: RDKit operations such as parsing, descriptors, fingerprints, rendering, and triage flags.
- `backend/app/adapters/`: normalization boundaries for dynamic external data.
- `backend/app/models/`: Pydantic API models.
- `backend/app/services/`: candidate-set loading, similarity search, and projection.
- `backend/app/api/`: HTTP routes.

API models are strict, frozen Pydantic models. Valid and invalid candidates are
separate variants of a discriminated union, so valid candidates always contain
canonical SMILES, descriptors, triage flags, and a structure depiction. Dynamic
native-library APIs are contained behind narrow typed chemistry modules and
reviewed local stubs in `backend/typings/`.

`backend/tests/test_architecture.py` enforces inward import dependencies:

```text
main -> api -> services -> chem/adapters -> models
```

It also confines FastAPI to the HTTP layer, Pydantic to models, pandas to
adapters, and RDKit/NumPy to chemistry modules. The test fails when a new import
crosses one of these boundaries.

`backend/tests/test_tooling_contract.py` keeps Python 3.13 aligned across the
repository configuration and verifies that CI continues to run formatting,
linting, strict typing, unit/component tests, generated API checks, browser
tests, and container smoke tests.

The MVP uses bundled files and in-memory processing. There is no database yet.

## Frontend Boundaries

- `frontend/src/api/`: typed API client functions.
- `frontend/src/types/`: TypeScript API shapes matching Pydantic responses.
- `frontend/src/components/`: table, detail, 2D/3D molecule views, triage flags, and chemical-space plot.

Plotly and 3Dmol are lazy-loaded so the initial workbench shell and unit tests do not eagerly load heavy visualization libraries. Frontend API types are generated from the checked-in backend OpenAPI schema instead of being maintained by hand.

## Verification Layers

- Ruff and strict Pyright provide fast static feedback.
- Pydantic and typed CSV adapters validate runtime trust boundaries.
- Focused pytest tests cover chemistry, domain variants, services, API success and failure paths, architecture, tooling alignment, and OpenAPI output.
- Vitest covers frontend components and states.
- Playwright covers the browser workbench against the real FastAPI service.
- The Compose smoke test builds production images, checks service health, and verifies the frontend-to-backend proxy.

## Future Extension Points

- Uploaded candidate sets can replace the bundled CSV loader.
- DuckDB or SQLite can add local persistence for larger candidate sets.
- External docking or AI model jobs can import result packages with `job_id`, `model_name`, `model_confidence`, `target_id`, and `pose_file`.
- Mol* can be added for protein and protein-ligand visualization.
- PLIP or ProLIF can compute protein-ligand interaction fingerprints after pose support exists.
- Playwright e2e tests should be added next to verify the browser workflow across backend and frontend.
