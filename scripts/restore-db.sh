#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/opt/wfm-naumen"

usage() {
  echo "Использование: $0 <dump.sql> --confirm" >&2
}

dump_file="${1:-}"
confirm="${2:-}"

if [[ -z "$dump_file" || "$confirm" != "--confirm" ]]; then
  echo "Restore заменит данные в базе приложения. Для запуска нужен явный аргумент --confirm." >&2
  usage
  exit 1
fi

if [[ ! -f "$dump_file" ]]; then
  echo "Файл dump не найден: $dump_file" >&2
  exit 1
fi

cd "$PROJECT_DIR"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

echo "ВНИМАНИЕ: restore заменит данные в базе ${POSTGRES_DB:-wfm_naumen}. Docker volumes напрямую не изменяются."
docker compose exec -T postgres psql \
  -U "${POSTGRES_USER:-wfm_user}" \
  -d "${POSTGRES_DB:-wfm_naumen}" \
  -v ON_ERROR_STOP=1 \
  < "$dump_file"

echo "Restore завершён из файла: $dump_file"
