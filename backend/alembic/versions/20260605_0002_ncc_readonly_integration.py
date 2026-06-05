"""add read-only Naumen NCC integration cache fields

Revision ID: 20260605_0002
Revises: 20260526_0001
Create Date: 2026-06-05
"""

from alembic import op


revision = "20260605_0002"
down_revision = "20260526_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    statements = [
        "ALTER TABLE naumen_projects ADD COLUMN IF NOT EXISTS naumen_customer_uuid VARCHAR(80)",
        "ALTER TABLE naumen_projects ADD COLUMN IF NOT EXISTS naumen_project_uuid VARCHAR(80)",
        "ALTER TABLE naumen_projects ADD COLUMN IF NOT EXISTS manual_stats_enabled BOOLEAN NOT NULL DEFAULT TRUE",
        "ALTER TABLE naumen_sync_runs ADD COLUMN IF NOT EXISTS partner_uuid VARCHAR(80)",
        "ALTER TABLE naumen_sync_runs ADD COLUMN IF NOT EXISTS period_begin TIMESTAMP",
        "ALTER TABLE naumen_sync_runs ADD COLUMN IF NOT EXISTS period_end TIMESTAMP",
        "ALTER TABLE naumen_sync_runs ADD COLUMN IF NOT EXISTS rows_by_type TEXT",
        "ALTER TABLE naumen_sync_runs ADD COLUMN IF NOT EXISTS rows_customers INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE naumen_sync_runs ADD COLUMN IF NOT EXISTS rows_projects INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE naumen_sync_runs ADD COLUMN IF NOT EXISTS rows_queues INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE naumen_sync_runs ADD COLUMN IF NOT EXISTS rows_load INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE naumen_sync_runs ADD COLUMN IF NOT EXISTS rows_employees INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE naumen_sync_runs ADD COLUMN IF NOT EXISTS rows_operator_workload INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE naumen_sync_runs ADD COLUMN IF NOT EXISTS rows_forecast_profile INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE queues ADD COLUMN IF NOT EXISTS queue_uuid VARCHAR(80)",
        "ALTER TABLE queues ADD COLUMN IF NOT EXISTS source_system VARCHAR(40) NOT NULL DEFAULT 'manual'",
        "ALTER TABLE workload_intervals ADD COLUMN IF NOT EXISTS source_system VARCHAR(40) NOT NULL DEFAULT 'manual'",
        "ALTER TABLE workload_intervals ADD COLUMN IF NOT EXISTS import_run_id INTEGER",
        "ALTER TABLE naumen_operators ADD COLUMN IF NOT EXISTS metrics_data TEXT",
        """
        CREATE TABLE IF NOT EXISTS ncc_queues (
            id SERIAL PRIMARY KEY,
            contour_id INTEGER REFERENCES naumen_projects(id),
            partner_uuid VARCHAR(80),
            queue_uuid VARCHAR(80) NOT NULL,
            queue_name VARCHAR(255),
            data_channel VARCHAR(80),
            target_sl DOUBLE PRECISION,
            answer_sec INTEGER,
            state VARCHAR(80),
            imported_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (contour_id, queue_uuid)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS ncc_load_intervals (
            id SERIAL PRIMARY KEY,
            contour_id INTEGER REFERENCES naumen_projects(id),
            partner_uuid VARCHAR(80),
            interval_start TIMESTAMP NOT NULL,
            queue_uuid VARCHAR(80),
            queue_name VARCHAR(255),
            offered INTEGER NOT NULL DEFAULT 0,
            handled INTEGER NOT NULL DEFAULT 0,
            lost INTEGER NOT NULL DEFAULT 0,
            lost_rate DOUBLE PRECISION,
            aht_sec DOUBLE PRECISION,
            sl_percent DOUBLE PRECISION,
            import_run_id INTEGER,
            UNIQUE (contour_id, interval_start, queue_uuid)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS ncc_operator_workload (
            id SERIAL PRIMARY KEY,
            contour_id INTEGER REFERENCES naumen_projects(id),
            partner_uuid VARCHAR(80),
            interval_start TIMESTAMP NOT NULL,
            queue_uuid VARCHAR(80),
            queue_name VARCHAR(255),
            operator_login VARCHAR(160),
            handled INTEGER NOT NULL DEFAULT 0,
            aht_sec DOUBLE PRECISION,
            talk_sec_total DOUBLE PRECISION,
            import_run_id INTEGER
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS ncc_employees (
            id SERIAL PRIMARY KEY,
            contour_id INTEGER REFERENCES naumen_projects(id),
            partner_uuid VARCHAR(80),
            employee_uuid VARCHAR(80),
            login VARCHAR(160),
            employee_title VARCHAR(255),
            operator_name VARCHAR(255),
            ou_title VARCHAR(255),
            post VARCHAR(255),
            department VARCHAR(255),
            queues_count INTEGER,
            queues TEXT,
            handled_calls_count INTEGER NOT NULL DEFAULT 0,
            avg_answer_sec DOUBLE PRECISION,
            avg_talk_sec DOUBLE PRECISION,
            total_talk_sec DOUBLE PRECISION,
            sl_percent DOUBLE PRECISION,
            skills TEXT,
            statuses_seen TEXT,
            first_handled_at TIMESTAMP,
            last_handled_at TIMESTAMP,
            import_run_id INTEGER,
            UNIQUE (contour_id, employee_uuid, login)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS ncc_forecast_profile (
            id SERIAL PRIMARY KEY,
            contour_id INTEGER REFERENCES naumen_projects(id),
            partner_uuid VARCHAR(80),
            weekday_num INTEGER NOT NULL,
            weekday_name VARCHAR(40) NOT NULL,
            hour_num INTEGER NOT NULL,
            queue_uuid VARCHAR(80),
            queue_name VARCHAR(255),
            avg_offered DOUBLE PRECISION,
            avg_handled DOUBLE PRECISION,
            avg_lost DOUBLE PRECISION,
            avg_aht_sec DOUBLE PRECISION,
            avg_sl_percent DOUBLE PRECISION,
            import_run_id INTEGER,
            UNIQUE (contour_id, weekday_num, hour_num, queue_uuid)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS ncc_operator_interval_stats (
            id SERIAL PRIMARY KEY,
            project_id INTEGER REFERENCES naumen_projects(id),
            partner_uuid VARCHAR(80),
            interval_start TIMESTAMP NOT NULL,
            queue_uuid VARCHAR(80),
            queue_name VARCHAR(255),
            operator_login VARCHAR(160),
            handled INTEGER NOT NULL DEFAULT 0,
            aht_sec DOUBLE PRECISION,
            talk_sec_total DOUBLE PRECISION,
            import_run_id INTEGER,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS ncc_forecast_profiles (
            id SERIAL PRIMARY KEY,
            project_id INTEGER REFERENCES naumen_projects(id),
            partner_uuid VARCHAR(80),
            weekday_num INTEGER NOT NULL,
            weekday_name VARCHAR(40) NOT NULL,
            hour_num INTEGER NOT NULL,
            queue_uuid VARCHAR(80),
            queue_name VARCHAR(255),
            avg_offered DOUBLE PRECISION,
            avg_handled DOUBLE PRECISION,
            avg_lost DOUBLE PRECISION,
            avg_aht_sec DOUBLE PRECISION,
            avg_sl_percent DOUBLE PRECISION,
            import_run_id INTEGER,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE UNIQUE INDEX IF NOT EXISTS ux_active_employees_inn
        ON employees (inn)
        WHERE inn IS NOT NULL AND inn <> '' AND is_active = TRUE AND employment_status <> 'archived'
        """,
    ]
    for statement in statements:
        connection.exec_driver_sql(statement)


def downgrade() -> None:
    pass
