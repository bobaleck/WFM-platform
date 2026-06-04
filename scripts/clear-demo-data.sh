#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/opt/wfm-naumen"

if [[ "${1:-}" != "--confirm" ]]; then
  echo "Отказ: очистка demo/business data требует явный аргумент --confirm." >&2
  echo "Будут очищены бизнес-таблицы WFM, import/export/audit demo-журналы и пользователи кроме admin." >&2
  exit 1
fi

cd "$PROJECT_DIR"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

DB_USER="${POSTGRES_USER:-wfm_user}"
DB_NAME="${POSTGRES_DB:-wfm_naumen}"

echo "Будут очищены таблицы:"
echo "actual_work_intervals, absences, schedule_recommendations, schedule_coverage, schedule_assignments,"
echo "schedule_generation_runs, staffing_requirements, workload_intervals, queue_skills, employee_skills,"
echo "kpi_snapshots, import_errors, import_batches, export_log, audit_log, queues, skills, shifts, employees, teams."
echo "Пользователь admin, роли, permissions, role_permissions, настройки, alembic_version сохраняются."

docker compose exec -T postgres psql -v ON_ERROR_STOP=1 -U "$DB_USER" -d "$DB_NAME" <<'SQL'
BEGIN;

DELETE FROM actual_work_intervals;
DELETE FROM absences;
DELETE FROM schedule_recommendations;
DELETE FROM schedule_coverage;
DELETE FROM schedule_assignments;
DELETE FROM schedule_generation_runs;
DELETE FROM staffing_requirements;
DELETE FROM workload_intervals;
DELETE FROM queue_skills;
DELETE FROM employee_skills;
DELETE FROM kpi_snapshots;
DELETE FROM import_errors;
DELETE FROM import_batches;
DELETE FROM export_log;
DELETE FROM audit_log;
DO $$
BEGIN
  IF to_regclass('public.external_mappings') IS NOT NULL THEN
    DELETE FROM external_mappings WHERE source_system = 'naumen';
  END IF;
  IF to_regclass('public.naumen_sync_errors') IS NOT NULL THEN
    DELETE FROM naumen_sync_errors;
  END IF;
  IF to_regclass('public.naumen_sync_runs') IS NOT NULL THEN
    DELETE FROM naumen_sync_runs;
  END IF;
END $$;
DELETE FROM queues;
DELETE FROM skills;
DELETE FROM shifts;
DELETE FROM employees;
DELETE FROM teams;

DELETE FROM users
WHERE COALESCE(username, '') <> 'admin'
  AND COALESCE(email, '') <> 'admin@local';

UPDATE users
SET is_active = TRUE
WHERE COALESCE(username, '') = 'admin'
   OR COALESCE(email, '') = 'admin@local';

COMMIT;

SELECT 'users' AS table_name, count(*) FROM users
UNION ALL SELECT 'roles', count(*) FROM roles
UNION ALL SELECT 'permissions', count(*) FROM permissions
UNION ALL SELECT 'employees', count(*) FROM employees
UNION ALL SELECT 'teams', count(*) FROM teams
UNION ALL SELECT 'queues', count(*) FROM queues
UNION ALL SELECT 'workload_intervals', count(*) FROM workload_intervals
UNION ALL SELECT 'schedule_assignments', count(*) FROM schedule_assignments
UNION ALL SELECT 'kpi_snapshots', count(*) FROM kpi_snapshots
ORDER BY table_name;
SQL

echo "Очистка demo/business data завершена."
