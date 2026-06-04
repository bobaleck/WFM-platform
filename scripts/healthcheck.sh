#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/opt/wfm-naumen"
cd "$PROJECT_DIR"

failed=0

check_http() {
  local name="$1"
  local url="$2"
  local code
  code="$(curl -s -o /tmp/wfm-healthcheck -w "%{http_code}" "$url" || true)"
  if [[ "$code" == "200" ]]; then
    echo "OK $name"
  else
    echo "FAIL $name: HTTP $code" >&2
    failed=1
  fi
}

check_service() {
  local name="$1"
  local service="$2"
  local status
  status="$(docker compose ps --format json "$service" 2>/dev/null | tr -d '\n' || true)"
  if [[ "$status" == *'"State":"running"'* || "$status" == *'"Status":"running"'* || "$status" == *'"State":"healthy"'* ]]; then
    echo "OK $name"
  else
    if docker compose ps "$service" | grep -q "Up"; then
      echo "OK $name"
    else
      echo "FAIL $name" >&2
      failed=1
    fi
  fi
}

check_http "backend" "http://127.0.0.1/health"
check_http "frontend" "http://127.0.0.1/"
check_http "scheduler" "http://127.0.0.1/scheduler/health"
check_service "PostgreSQL" "postgres"
check_service "Redis" "redis"

exit "$failed"
