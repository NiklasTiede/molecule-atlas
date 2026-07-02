# Molecule Atlas

Molecule Atlas is an open-source fullstack workbench for reviewing small-molecule candidate sets. It combines a React/TypeScript interface with a FastAPI/RDKit backend to help users inspect structures, compute descriptors, search by molecular similarity, group molecules by scaffold, and explore candidate properties through interactive views.

The project is intentionally scoped as a public learning and portfolio project. It does not make medicinal chemistry decisions, predict clinical success, or run docking/model inference. It demonstrates building blocks behind scientist-facing molecular design tools: SMILES handling, descriptors, fingerprints, Tanimoto similarity, scaffold analysis, 2D/3D molecular visualization, and a data model that can later ingest docking or AI-model outputs.

See [docs/product-vision.md](docs/product-vision.md) for the longer-term direction.

## MVP Features

- Bundled demo candidate set
- RDKit SMILES validation and canonicalization
- Descriptor calculation
- Morgan fingerprints and Tanimoto similarity
- Murcko scaffolds
- Lipinski and Veber-style triage flags
- Backend-generated 2D SVG depictions
- Basic 3D conformer viewer
- PCA chemical-space projection

## Development

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

Run the backend:

```bash
make backend-dev
```

Run the frontend:

```bash
make frontend-dev
```

Run verification:

```bash
make test
make lint
make e2e
cd frontend && npm run build
```

Useful backend URLs:

- `http://localhost:8000/health`
- `http://localhost:8000/docs`
- `http://localhost:8000/api/candidate-sets/demo`
- `http://localhost:8000/api/candidate-sets/demo/projection`
- `http://localhost:8000/api/candidate-sets/demo/candidates/demo-1/neighbors`
- `http://localhost:8000/api/candidate-sets/demo/candidates/demo-1/conformer`

## Scientific Caveats

- 3D conformers are not binding poses.
- Demo scores are mock values, not measured affinities.
- Rule-based flags are triage aids, not drug-discovery decisions.
- The MVP does not run docking, protein-pocket modeling, or AI molecule generation.
