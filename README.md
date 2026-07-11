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
- Initial typed application capability catalog with permission and execution-policy metadata
- Bounded local evidence run-summary API with explicit correlation IDs
- Safe, idempotent portable evidence ZIP import into temporary local storage
- FastAPI-independent portable evidence core
- Versioned run and semantic artifact manifests with typed prediction and validation semantics
- SHA-256 artifact inventory and offline verification
- Canonical JSON, JSON Schema, and deterministic Markdown or self-contained HTML reports
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
- `http://localhost:8000/api/evidence/runs/fixture-succeeded`
- `POST http://localhost:8000/api/evidence/imports`

The import operation accepts one `multipart/form-data` field named `bundle`, with media type
`application/zip`, plus a required `Idempotency-Key` header. A bundle root contains
`molecule-atlas-run.json`, optional `molecule-atlas-artifacts.json`, and its referenced artifact
paths. The current local profile limits the compressed upload to 10 MiB, 256 members, 25 MiB per
member, and 100 MiB total uncompressed content. It rejects unsafe paths, symbolic links, encrypted
or duplicate members, unsupported compression, invalid contracts, and missing or mismatched
artifact bytes.

Imported data and idempotency records are temporary and disappear when the API process restarts.
This is intentional for Milestone 3; persistent multi-user projects begin in Milestone 5.

## Portable evidence CLI

The evidence core is a separate Python package under `backend/core`. It depends on Pydantic but not
FastAPI, RDKit, a database, a GPU runtime, or any external model service. From `backend/`, inspect the
bundled deterministic fixtures with:

```bash
UV_CACHE_DIR=../.uv-cache uv run molecule-atlas adapters
UV_CACHE_DIR=../.uv-cache uv run molecule-atlas inspect ../data/evidence-fixtures/succeeded
UV_CACHE_DIR=../.uv-cache uv run molecule-atlas audit ../data/evidence-fixtures/partial --adapter manifest --output /tmp/molecule-atlas-run.json
UV_CACHE_DIR=../.uv-cache uv run molecule-atlas report ../data/evidence-fixtures/failed/molecule-atlas-run.json --format markdown
UV_CACHE_DIR=../.uv-cache uv run molecule-atlas report ../data/evidence-fixtures/succeeded/molecule-atlas-run.json --format html --output /tmp/molecule-atlas-report.html
```

Export the checked-in JSON Schemas with:

```bash
UV_CACHE_DIR=../.uv-cache uv run molecule-atlas schema --contract run-manifest --output ../schemas/run-manifest/0.1.0.schema.json
UV_CACHE_DIR=../.uv-cache uv run molecule-atlas schema --contract artifact-manifest --output ../schemas/artifact-manifest/0.1.0.schema.json
```

The current typed adapter catalog intentionally registers only `manifest`, which validates an
existing `molecule-atlas-run.json` file or directory and verifies local artifact hashes. Milestone 2
has added a companion `ArtifactManifest 0.1.0` and adapter-result `0.2.0`, which binds logical names,
semantic artifact types, content digests, and derivation lineage to the run inventory. An
unregistered Boltz 2.2.1 parser is tested against an explicitly non-scientific documented-layout
fixture. It will not be advertised until genuine redistributable output proves the declared
compatibility. An equally unregistered DiffDock 1.1.3 parser maps ranked SDF filenames only to pose
confidence, never affinity. Both importers remain dependency-free and offline; genuine fixture
capture and public registration are still pending. PoseBusters 0.6.5 validation is implemented as a
portable full-report CSV normalizer with an optional local CPU runner. Normal CI replays a genuine
captured report and does not install the optional validator.

Install the optional CPU validator only when executing new checks locally:

```bash
cd backend
UV_CACHE_DIR=../.uv-cache uv sync --extra validation
```

## Scientific caveats

- 3D conformers are not protein-bound poses.
- Predicted poses are not experimental structures.
- Pose confidence is not binding affinity.
- Predicted affinity is not measured affinity.
- Demo scores are mock values unless explicitly documented otherwise.
- Rule-based filters are triage aids, not medicinal-chemistry decisions.
- The current implementation does not yet run docking, protein-pocket modeling, or AI-model inference.

## Current implementation priority

Milestones 1 and 2 are implemented: the portable core includes typed external-output normalization,
PoseBusters-backed checks, semantic artifact lineage, and deterministic Markdown/HTML evidence
reports. Milestone 3 is in progress. Its first two slices introduce the shared capability boundary,
a bounded local run-summary API, and safe temporary evidence-bundle upload. Artifact and validation
inspection is next, followed by the evidence review UI. Genuine Boltz/DiffDock execution fixtures
and adapter registration remain with Milestone 8. AI integration remains deferred until the
governed-assistance milestone. See
[the roadmap](docs/roadmap.md) for later acceptance criteria.
