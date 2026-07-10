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
- FastAPI-independent portable evidence core
- Versioned run and semantic artifact manifests with typed prediction and validation semantics
- SHA-256 artifact inventory and offline verification
- Canonical JSON, JSON Schema, and deterministic Markdown reports
- Successful, partial, and failed synthetic evidence fixtures
- `molecule-atlas` CLI for adapter discovery, manifest inspection, audit, and reporting
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

Molecule Atlas is also designed for future governed AI assistance without making AI a prerequisite.
The React UI and a future AI module will use the same typed application capabilities; the backend
will remain responsible for validation, authorization, execution, limits, persistence, and audit.
Scientific plugins will not contain agent logic, and an agent will not receive direct infrastructure
access.

Read the project documentation before implementing long-term features:

- [Product vision](docs/product-vision.md)
- [Roadmap](docs/roadmap.md)
- [Architecture](docs/architecture.md)
- [Domain model](docs/domain-model.md)
- [Scientific contracts](docs/scientific-contracts.md)
- [AI-first readiness](docs/ai-first-readiness.md)
- [ADR 0001: shared application capability boundary](docs/adr/0001-shared-application-capability-boundary.md)
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
make evidence-contract-check
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

## Portable evidence CLI

The evidence core is a separate Python package under `backend/core`. It depends on Pydantic but not
FastAPI, RDKit, a database, a GPU runtime, or any external model service. From `backend/`, inspect the
bundled deterministic fixtures with:

```bash
UV_CACHE_DIR=../.uv-cache uv run molecule-atlas adapters
UV_CACHE_DIR=../.uv-cache uv run molecule-atlas inspect ../data/evidence-fixtures/succeeded
UV_CACHE_DIR=../.uv-cache uv run molecule-atlas audit ../data/evidence-fixtures/partial --adapter manifest --output /tmp/molecule-atlas-run.json
UV_CACHE_DIR=../.uv-cache uv run molecule-atlas report ../data/evidence-fixtures/failed/molecule-atlas-run.json --format markdown
```

Export the checked-in JSON Schemas with:

```bash
UV_CACHE_DIR=../.uv-cache uv run molecule-atlas schema --contract run-manifest --output ../schemas/run-manifest/0.1.0.schema.json
UV_CACHE_DIR=../.uv-cache uv run molecule-atlas schema --contract artifact-manifest --output ../schemas/artifact-manifest/0.1.0.schema.json
```

The current typed adapter catalog intentionally registers only `manifest`, which validates an
existing `molecule-atlas-run.json` file or directory and verifies local artifact hashes. Milestone 2
has added a companion `ArtifactManifest 0.1.0` for logical names, semantic artifact types, content
digests, and derivation lineage. Fixture-backed Boltz and DiffDock imports plus PoseBusters validation
remain incremental; those adapters are not advertised until their supported layouts are implemented
and tested.

## Scientific caveats

- 3D conformers are not protein-bound poses.
- Predicted poses are not experimental structures.
- Pose confidence is not binding affinity.
- Predicted affinity is not measured affinity.
- Demo scores are mock values unless explicitly documented otherwise.
- Rule-based filters are triage aids, not medicinal-chemistry decisions.
- The current implementation does not yet run docking, protein-pocket modeling, or AI-model inference.

## Current implementation priority

Milestone 1, the portable evidence core, is implemented. The next planned milestone is real-output
import and validation with at least two model families and PoseBusters-backed normalized checks. It
must continue to preserve raw upstream evidence and explicit prediction semantics while adding typed
adapter outputs, semantic artifact types, and explicit lineage. The shared application capability
layer begins with web evidence import in Milestone 3; AI integration remains deferred until the
governed-assistance milestone. See [the roadmap](docs/roadmap.md) for acceptance criteria and later
milestones.
