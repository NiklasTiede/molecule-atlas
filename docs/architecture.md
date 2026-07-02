# Molecule Atlas Architecture

## MVP Architecture

The backend is a FastAPI service with pure RDKit-backed chemistry modules. It loads a bundled candidate CSV into memory, validates structures, computes descriptors, fingerprints, scaffolds, similarity neighbors, 2D SVG depictions, 3D conformer mol blocks, and a PCA projection.

The frontend is a Vite React app. It fetches the demo candidate set from the backend and renders a workbench with a candidate table, selected-candidate detail panel, molecule depictions, 3D conformer viewer, triage flags, nearest neighbors, and chemical-space plot.

## Data Flow

1. `data/demo_candidates.csv` provides the candidate records.
2. `candidate_repository.py` validates and enriches each record.
3. `candidates.py` exposes typed API responses.
4. `frontend/src/api/candidates.ts` fetches the candidate set, projection, and conformer data.
5. React components render table, detail, molecular views, and projection.

## Backend Boundaries

- `backend/app/chem/`: RDKit operations such as parsing, descriptors, fingerprints, rendering, and triage flags.
- `backend/app/models/`: Pydantic API models.
- `backend/app/services/`: candidate-set loading, similarity search, and projection.
- `backend/app/api/`: HTTP routes.

The MVP uses bundled files and in-memory processing. There is no database yet.

## Frontend Boundaries

- `frontend/src/api/`: typed API client functions.
- `frontend/src/types/`: TypeScript API shapes matching Pydantic responses.
- `frontend/src/components/`: table, detail, 2D/3D molecule views, triage flags, and chemical-space plot.

Plotly and 3Dmol are lazy-loaded so the initial workbench shell and unit tests do not eagerly load heavy visualization libraries.

## Future Extension Points

- Uploaded candidate sets can replace the bundled CSV loader.
- DuckDB or SQLite can add local persistence for larger candidate sets.
- External docking or AI model jobs can import result packages with `job_id`, `model_name`, `model_confidence`, `target_id`, and `pose_file`.
- Mol* can be added for protein and protein-ligand visualization.
- PLIP or ProLIF can compute protein-ligand interaction fingerprints after pose support exists.
- Playwright e2e tests should be added next to verify the browser workflow across backend and frontend.
