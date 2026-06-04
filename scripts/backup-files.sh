#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/opt/wfm-naumen"
BACKUP_DIR="$PROJECT_DIR/backups/files"

cd "$PROJECT_DIR"
mkdir -p "$BACKUP_DIR"

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
archive="$BACKUP_DIR/wfm-files_${timestamp}.tar.gz"

tar \
  --exclude=".env" \
  --exclude="frontend/node_modules" \
  --exclude="**/__pycache__" \
  --exclude="backups" \
  -czf "$archive" \
  docs .env.example docker-compose.yml backend frontend scheduler infra scripts

if [[ ! -s "$archive" ]]; then
  echo "Ошибка: архив не создан или пустой: $archive" >&2
  exit 1
fi

echo "Backup файлов создан: $archive"
