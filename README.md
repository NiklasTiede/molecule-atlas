# Molecule Atlas

Molecule Atlas is an open-source, self-hosted visual workbench for exploring small molecules, inspecting protein-ligand results, validating computational evidence, and building reproducible structure-based discovery workflows.

The current implementation is a ligand-centric candidate review workbench. It provides the foundation for a longer-term product that can import and compare docking or AI-model outputs, inspect protein pockets and poses, validate physical plausibility, preserve provenance, and eventually run workflows through local, Kubernetes, GPU-provider, or institutional-cluster executors.

Molecule Atlas is not a drug-discovery oracle. It does not claim that a candidate is active, safe, selective, synthesizable, or clinically viable.

## Current capabilities

- Bundled demo candidate set
- RDKit SMILES validation and canonicalization
- Molecular descriptors
- Morgan fingerprints and Tanimoto similarity
- Murcko scaffolds
- Lipinski- and Veber-style triage flags
- Backend-generated 2D SVG depictions
- Basic 3D conformer viewer
- PCA chemical-space projection
- React/TypeScript workbench backed by a typed FastAPI API
- Generated TypeScript API contracts
- Unit, component, Playwright, and container smoke tests

## Long-term direction

The intended product combines:

- molecule and candidate-set exploration;
- protein, pocket, complex, and pose visualization;
- imported Boltz, DiffDock, Vina, ProDock, and other model outputs;
- explicit score semantics and units;
- PoseBusters-backed validation evidence;
- interaction fingerprints;
- reproducible run manifests and reports;
- annotations, shortlists, and shared review;
- optional local, Kubernetes, remote GPU, and Slurm execution.

The visual workbench is the product. Trust, provenance, validation, and interoperability are its architectural foundation.

Read the project documentation before implementing long-term features:

- [Product vision](docs/product-vision.md)
- [Roadmap](docs/roadmap.md)
- [Architecture](docs/architecture.md)
- [Domain model](docs/domain-model.md)
- [Scientific contracts](docs/scientific-contracts.md)
- [Coding-agent instructions](AGENTS.md)

## Development

The backend is standardized on Python 3.13. `uv` reads the repository's `.python-version` file and creates a matching environment.

Install backend dependencies:

```bash
cd backend
UV_CACHE_DIR=../.uv-cache uv sync --dev
```

Install frontend dependencies:

```bash
cd frontend
npm install
```

Run the backend and frontend:

```bash
make backend-dev
make frontend-dev
```

Run verification:

```bash
make test
make lint
make api-contract-check
make e2e
cd frontend && npm run build
```

Backend verification includes Ruff, strict Pyright, pytest, architecture checks, and OpenAPI generation. Frontend verification includes ESLint, Vitest, generated API types, and Playwright.

Build and smoke-test production containers:

```bash
make container-build
make container-smoke
```

The Compose smoke test serves the frontend at `http://localhost:8080` and the backend at `http://localhost:8000`. The frontend proxies `/api/*` and `/health` to the backend.

Useful backend URLs:

- `http://localhost:8000/health`
- `http://localhost:8000/docs`
- `http://localhost:8000/api/candidate-sets/demo`
- `http://localhost:8000/api/candidate-sets/demo/projection`
- `http://localhost:8000/api/candidate-sets/demo/candidates/demo-1/neighbors`
- `http://localhost:8000/api/candidate-sets/demo/candidates/demo-1/conformer`

## Scientific caveats

- 3D conformers are not protein-bound poses.
- Predicted poses are not experimental structures.
- Pose confidence is not binding affinity.
- Predicted affinity is not measured affinity.
- Demo scores are mock values unless explicitly documented otherwise.
- Rule-based filters are triage aids, not medicinal-chemistry decisions.
- The current implementation does not yet run docking, protein-pocket modeling, or AI-model inference.

## Current implementation priority

The next planned milestone is a portable evidence core that can represent, inspect, hash, validate, and report existing model outputs without requiring a GPU, database, or managed execution system. See [the roadmap](docs/roadmap.md) for acceptance criteria and later milestones.
