#!/usr/bin/env sh
set -eu

export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-molecule-atlas-smoke}"

backend_port="${MOLECULE_ATLAS_BACKEND_PORT:-8000}"
frontend_port="${MOLECULE_ATLAS_FRONTEND_PORT:-8080}"
backend_url="http://127.0.0.1:${backend_port}"
frontend_url="http://127.0.0.1:${frontend_port}"

cleanup() {
  docker compose down --remove-orphans >/dev/null 2>&1 || true
}

wait_for() {
  url="$1"
  attempts=60
  while [ "$attempts" -gt 0 ]; do
    if curl -fsS "$url" >/dev/null; then
      return 0
    fi
    attempts=$((attempts - 1))
    sleep 1
  done

  echo "Timed out waiting for ${url}" >&2
  return 1
}

trap cleanup EXIT INT TERM

docker compose up --build -d

wait_for "${backend_url}/health"
wait_for "${frontend_url}/"
curl -fsS "${frontend_url}/api/candidate-sets/demo" | grep -q '"candidates"'
