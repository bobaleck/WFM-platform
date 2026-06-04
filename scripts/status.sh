#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/opt/wfm-naumen"
cd "$PROJECT_DIR"

echo "== Docker Compose =="
docker compose ps

echo
echo "== Health endpoints =="
backend_code="$(curl -s -o /tmp/wfm-health-backend -w "%{http_code}" http://127.0.0.1/health || true)"
version_code="$(curl -s -o /tmp/wfm-health-version -w "%{http_code}" http://127.0.0.1/api/v1/version || true)"
scheduler_code="$(curl -s -o /tmp/wfm-health-scheduler -w "%{http_code}" http://127.0.0.1/scheduler/health || true)"
echo "backend /health: $backend_code $(cat /tmp/wfm-health-backend 2>/dev/null || true)"
echo "backend /api/v1/version: $version_code $(cat /tmp/wfm-health-version 2>/dev/null || true)"
echo "scheduler /scheduler/health: $scheduler_code $(cat /tmp/wfm-health-scheduler 2>/dev/null || true)"

echo
echo "== Disk =="
df -h "$PROJECT_DIR"
du -sh "$PROJECT_DIR" 2>/dev/null || true
du -sh "$PROJECT_DIR/backups" 2>/dev/null || true

if [[ "$backend_code" != "200" || "$version_code" != "200" ]]; then
  echo
  echo "== Последние 20 строк логов backend =="
  docker compose logs --tail=20 backend || true
fi
