#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

docker compose ps
printf '\nBackend health:\n'
curl -fsS http://127.0.0.1:${BACKEND_PORT:-8000}/health || true
printf '\nScheduler health:\n'
curl -fsS http://127.0.0.1:${SCHEDULER_PORT:-8010}/health || true
printf '\nDisk:\n'
df -h
