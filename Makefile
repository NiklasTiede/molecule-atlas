.PHONY: backend-test backend-lint backend-dev frontend-test frontend-lint frontend-build frontend-dev frontend-e2e test lint e2e

backend-test:
	cd backend && UV_CACHE_DIR=../.uv-cache uv run pytest

backend-lint:
	cd backend && UV_CACHE_DIR=../.uv-cache uv run ruff check .

backend-dev:
	cd backend && UV_CACHE_DIR=../.uv-cache uv run uvicorn app.main:app --reload

frontend-test:
	cd frontend && npm test

frontend-lint:
	cd frontend && npm run lint

frontend-build:
	cd frontend && npm run build

frontend-dev:
	cd frontend && npm run dev

frontend-e2e:
	cd frontend && npm run e2e

test: backend-test frontend-test

lint: backend-lint frontend-lint

e2e: frontend-e2e
