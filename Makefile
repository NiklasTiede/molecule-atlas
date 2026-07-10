.PHONY: backend-test backend-lint backend-typecheck backend-openapi backend-evidence-schema backend-dev frontend-test frontend-lint frontend-build frontend-api-types frontend-dev frontend-e2e api-contract-check evidence-contract-check container-config-test container-build container-smoke test lint e2e

backend-test:
	cd backend && UV_CACHE_DIR=../.uv-cache uv run pytest

backend-lint:
	cd backend && UV_CACHE_DIR=../.uv-cache uv run ruff check .
	cd backend && UV_CACHE_DIR=../.uv-cache uv run ruff format --check .

backend-typecheck:
	cd backend && UV_CACHE_DIR=../.uv-cache uv run pyright

backend-openapi:
	cd backend && UV_CACHE_DIR=../.uv-cache uv run python -m scripts.export_openapi

backend-evidence-schema:
	cd backend && UV_CACHE_DIR=../.uv-cache uv run molecule-atlas schema --contract run-manifest --output ../schemas/run-manifest/0.1.0.schema.json
	cd backend && UV_CACHE_DIR=../.uv-cache uv run molecule-atlas schema --contract artifact-manifest --output ../schemas/artifact-manifest/0.1.0.schema.json

backend-dev:
	cd backend && UV_CACHE_DIR=../.uv-cache uv run uvicorn app.main:app --reload

frontend-test:
	cd frontend && npm test

frontend-lint:
	cd frontend && npm run lint

frontend-build:
	cd frontend && npm run build

frontend-api-types:
	cd frontend && npm run generate:api

frontend-dev:
	cd frontend && npm run dev

frontend-e2e:
	cd frontend && npm run e2e

container-config-test:
	sh scripts/check-container-config.sh

container-build:
	docker build -f backend/Dockerfile -t molecule-atlas-backend:local .
	docker build -f frontend/Dockerfile -t molecule-atlas-frontend:local .

container-smoke:
	sh scripts/container-smoke.sh

test: backend-test frontend-test

lint: backend-lint backend-typecheck frontend-lint

api-contract-check: backend-openapi frontend-api-types
	git diff --exit-code -- frontend/openapi.json frontend/src/types/openapi.d.ts

evidence-contract-check: backend-evidence-schema
	git diff --exit-code -- schemas/run-manifest/0.1.0.schema.json schemas/artifact-manifest/0.1.0.schema.json

e2e: frontend-e2e
