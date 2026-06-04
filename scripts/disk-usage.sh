#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/opt/wfm-naumen"
cd "$PROJECT_DIR"

echo "== df -h =="
df -h

echo
echo "== Размер проекта =="
du -sh "$PROJECT_DIR" 2>/dev/null || true

echo
echo "== Размер backups =="
du -sh "$PROJECT_DIR/backups" 2>/dev/null || true

echo
echo "== Docker volumes =="
docker system df -v 2>/dev/null || true
