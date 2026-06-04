#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/opt/wfm-naumen"
BACKUP_DIR="$PROJECT_DIR/backups/db"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-14}"

cd "$PROJECT_DIR"
mkdir -p "$BACKUP_DIR"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
dump_file="$BACKUP_DIR/${POSTGRES_DB:-wfm_naumen}_${timestamp}.sql"

docker compose exec -T postgres pg_dump \
  -U "${POSTGRES_USER:-wfm_user}" \
  -d "${POSTGRES_DB:-wfm_naumen}" \
  --no-owner \
  --no-privileges \
  > "$dump_file"

if [[ ! -s "$dump_file" ]]; then
  echo "Ошибка: dump не создан или пустой: $dump_file" >&2
  exit 1
fi

find "$BACKUP_DIR" -type f -name "*.sql" -mtime "+$RETENTION_DAYS" -delete

echo "Backup БД создан: $dump_file"
