#!/usr/bin/env sh
set -eu

for file in \
  .dockerignore \
  compose.yaml \
  backend/Dockerfile \
  frontend/Dockerfile \
  frontend/nginx.conf \
  scripts/container-smoke.sh
do
  test -f "$file"
done

grep -q "app.main:app" backend/Dockerfile
grep -q "COPY backend/core ./core" backend/Dockerfile
grep -q "libexpat1" backend/Dockerfile
grep -q "libxrender1" backend/Dockerfile
grep -q "libxext6" backend/Dockerfile
grep -q "VITE_API_BASE_URL" frontend/Dockerfile
grep -q "proxy_pass http://backend:8000" frontend/nginx.conf
grep -q "backend:" compose.yaml
grep -q "frontend:" compose.yaml
