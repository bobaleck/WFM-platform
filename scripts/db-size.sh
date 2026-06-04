#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/opt/wfm-naumen"
cd "$PROJECT_DIR"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

docker compose exec -T postgres psql \
  -U "${POSTGRES_USER:-wfm_user}" \
  -d "${POSTGRES_DB:-wfm_naumen}" \
  -v ON_ERROR_STOP=1 \
  -c "SELECT pg_size_pretty(pg_database_size(current_database())) AS database_size;" \
  -c "SELECT relname AS table_name, pg_size_pretty(pg_total_relation_size(relid)) AS total_size FROM pg_catalog.pg_statio_user_tables ORDER BY pg_total_relation_size(relid) DESC LIMIT 20;"
