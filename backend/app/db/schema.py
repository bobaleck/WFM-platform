from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


def ensure_stage4_schema(engine: Engine) -> None:
    def add_column(table: str, column: str, ddl: str) -> None:
        inspector = inspect(engine)
        if table not in inspector.get_table_names():
            return
        existing = {item["name"] for item in inspector.get_columns(table)}
        if column in existing:
            return
        with engine.begin() as connection:
            connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}"))

    add_column("planning_settings", "shrinkage_percent", "DOUBLE PRECISION NOT NULL DEFAULT 25")
    add_column("planning_settings", "service_level_target", "DOUBLE PRECISION NOT NULL DEFAULT 80")
    add_column("planning_settings", "average_patience_sec", "INTEGER NOT NULL DEFAULT 20")
    add_column("planning_settings", "calculation_method", "VARCHAR(40) NOT NULL DEFAULT 'mvp'")
    add_column("planning_settings", "max_consecutive_work_days", "INTEGER NOT NULL DEFAULT 5")
    add_column("planning_settings", "preferred_shift_balance_enabled", "BOOLEAN NOT NULL DEFAULT TRUE")
    add_column("planning_settings", "weekend_balance_enabled", "BOOLEAN NOT NULL DEFAULT TRUE")
    add_column("planning_settings", "skill_priority_weight", "INTEGER NOT NULL DEFAULT 50")
    add_column("planning_settings", "fairness_weight", "INTEGER NOT NULL DEFAULT 30")
    add_column("planning_settings", "coverage_weight", "INTEGER NOT NULL DEFAULT 100")
    add_column("schedule_assignments", "confirmed_at", "TIMESTAMP")
    add_column("schedule_assignments", "published_at", "TIMESTAMP")
    add_column("schedule_assignments", "cancelled_at", "TIMESTAMP")
    add_column("users", "username", "VARCHAR(120)")
    add_column("users", "password_hash", "TEXT")
    add_column("users", "role_id", "INTEGER")
    add_column("users", "is_superuser", "BOOLEAN NOT NULL DEFAULT FALSE")
    add_column("users", "last_login_at", "TIMESTAMP")
    add_column("audit_log", "actor_user_id", "INTEGER")
    add_column("audit_log", "actor_username", "VARCHAR(160)")
    add_column("audit_log", "details_json", "TEXT")
    add_column("audit_log", "ip_address", "VARCHAR(80)")
    add_column("audit_log", "user_agent", "TEXT")
    add_column("naumen_connection_settings", "api_version", "VARCHAR(32) NOT NULL DEFAULT 'v2'")
    add_column("naumen_connection_settings", "last_check_http_status", "INTEGER")
    add_column("naumen_connection_settings", "last_check_endpoint", "VARCHAR(512)")
    add_column("naumen_projects", "partner_id", "INTEGER")
    add_column("naumen_projects", "naumen_customer_uuid", "VARCHAR(80)")
    add_column("naumen_projects", "naumen_project_uuid", "VARCHAR(80)")
    add_column("naumen_projects", "manual_stats_enabled", "BOOLEAN NOT NULL DEFAULT TRUE")
    add_column("user_preferences", "selected_partner_id", "INTEGER")
    add_column("naumen_sync_runs", "project_id", "INTEGER")
    add_column("naumen_sync_runs", "partner_uuid", "VARCHAR(80)")
    add_column("naumen_sync_runs", "period_begin", "TIMESTAMP")
    add_column("naumen_sync_runs", "period_end", "TIMESTAMP")
    add_column("naumen_sync_runs", "rows_by_type", "TEXT")
    add_column("external_mappings", "project_id", "INTEGER")
    add_column("queues", "queue_uuid", "VARCHAR(80)")
    add_column("queues", "source_system", "VARCHAR(40) NOT NULL DEFAULT 'manual'")
    add_column("workload_intervals", "source_system", "VARCHAR(40) NOT NULL DEFAULT 'manual'")
    add_column("workload_intervals", "import_run_id", "INTEGER")
    add_column("naumen_operators", "metrics_data", "TEXT")
    for table in (
        "employees",
        "teams",
        "queues",
        "shifts",
        "workload_intervals",
        "staffing_requirements",
        "schedule_assignments",
        "schedule_coverage",
        "absences",
        "kpi_snapshots",
        "actual_work_intervals",
        "import_batches",
    ):
        add_column(table, "project_id", "INTEGER")

    with engine.begin() as connection:
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS naumen_partners (
                id SERIAL PRIMARY KEY,
                partner_uuid VARCHAR(80) UNIQUE NOT NULL,
                title VARCHAR(255) NOT NULL,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                is_default BOOLEAN NOT NULL DEFAULT FALSE,
                last_sync_at TIMESTAMP,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS naumen_projects (
                id SERIAL PRIMARY KEY,
                project_uuid VARCHAR(80) UNIQUE NOT NULL,
                partner_id INTEGER REFERENCES naumen_partners(id),
                title VARCHAR(255) NOT NULL,
                partner_uuid VARCHAR(80),
                state VARCHAR(80),
                data_channel VARCHAR(80),
                cluster_id INTEGER,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                is_default BOOLEAN NOT NULL DEFAULT FALSE,
                last_checked_at TIMESTAMP,
                last_sync_at TIMESTAMP,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        connection.execute(text("""
            UPDATE naumen_projects
            SET is_active = FALSE, is_default = FALSE, updated_at = CURRENT_TIMESTAMP
            WHERE project_uuid IN ('11111111111111111111111111111111', '22222222222222222222222222222222')
        """))
        connection.execute(text("""
            DELETE FROM user_project_access
            WHERE naumen_project_id IN (
                SELECT id FROM naumen_projects
                WHERE project_uuid IN ('11111111111111111111111111111111', '22222222222222222222222222222222')
            )
        """))
        connection.execute(text("""
            UPDATE user_preferences
            SET selected_project_id = NULL, updated_at = CURRENT_TIMESTAMP
            WHERE selected_project_id IN (
                SELECT id FROM naumen_projects
                WHERE project_uuid IN ('11111111111111111111111111111111', '22222222222222222222222222222222')
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS schedule_recommendations (
                id SERIAL PRIMARY KEY,
                generation_run_id INTEGER REFERENCES schedule_generation_runs(id),
                work_date DATE NOT NULL,
                queue_id INTEGER NOT NULL REFERENCES queues(id),
                employee_id INTEGER REFERENCES employees(id),
                recommendation_type VARCHAR(80) NOT NULL,
                message TEXT NOT NULL,
                severity VARCHAR(40) NOT NULL DEFAULT 'warning',
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS naumen_connection_settings (
                id SERIAL PRIMARY KEY,
                base_url VARCHAR(512),
                api_version VARCHAR(32) NOT NULL DEFAULT 'v2',
                auth_mode VARCHAR(32) NOT NULL DEFAULT 'api_key',
                username VARCHAR(255),
                api_key_encrypted TEXT,
                basic_password_encrypted TEXT,
                request_timeout_seconds INTEGER NOT NULL DEFAULT 30,
                verify_ssl BOOLEAN NOT NULL DEFAULT TRUE,
                enabled BOOLEAN NOT NULL DEFAULT FALSE,
                last_check_status VARCHAR(80),
                last_check_message TEXT,
                last_check_http_status INTEGER,
                last_check_endpoint VARCHAR(512),
                last_check_at TIMESTAMP,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        connection.execute(text("""
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
        """))
        connection.execute(text("""
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
        """))
        connection.execute(text("""
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
        """))
        connection.execute(text("""
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
        """))
        connection.execute(text("""
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
        """))
        connection.execute(text("""
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
        """))
        connection.execute(text("""
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
        """))
        connection.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS ux_active_employees_inn
            ON employees (inn)
            WHERE inn IS NOT NULL AND inn <> '' AND is_active = TRUE AND employment_status <> 'archived'
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS naumen_sync_runs (
                id SERIAL PRIMARY KEY,
                sync_type VARCHAR(80) NOT NULL,
                project_id INTEGER REFERENCES naumen_projects(id),
                status VARCHAR(80) NOT NULL,
                started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                finished_at TIMESTAMP,
                rows_received INTEGER NOT NULL DEFAULT 0,
                rows_created INTEGER NOT NULL DEFAULT 0,
                rows_updated INTEGER NOT NULL DEFAULT 0,
                rows_failed INTEGER NOT NULL DEFAULT 0,
                error_message TEXT
            )
        """))
        for statement in [
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
        ]:
            connection.execute(text(statement))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS naumen_sync_errors (
                id SERIAL PRIMARY KEY,
                sync_run_id INTEGER NOT NULL REFERENCES naumen_sync_runs(id),
                entity_type VARCHAR(80) NOT NULL,
                external_id VARCHAR(255),
                error_message TEXT NOT NULL,
                raw_data TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS naumen_project_schedule_rules (
                id SERIAL PRIMARY KEY,
                project_id INTEGER NOT NULL REFERENCES naumen_projects(id),
                rest_day VARCHAR(80),
                time_from VARCHAR(40),
                time_to VARCHAR(40),
                parameters_json TEXT,
                rule_type VARCHAR(80),
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS user_project_access (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                naumen_project_id INTEGER NOT NULL REFERENCES naumen_projects(id),
                can_view BOOLEAN NOT NULL DEFAULT TRUE,
                can_sync BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                id SERIAL PRIMARY KEY,
                user_id INTEGER UNIQUE NOT NULL REFERENCES users(id),
                selected_project_id INTEGER REFERENCES naumen_projects(id),
                selected_partner_id INTEGER REFERENCES naumen_partners(id),
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS external_mappings (
                id SERIAL PRIMARY KEY,
                source_system VARCHAR(80) NOT NULL DEFAULT 'naumen',
                entity_type VARCHAR(80) NOT NULL,
                external_id VARCHAR(255) NOT NULL,
                internal_id VARCHAR(80) NOT NULL,
                project_id INTEGER REFERENCES naumen_projects(id),
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))


def ensure_stage9_schema(engine: Engine) -> None:
    def add_column(table: str, column: str, ddl: str) -> None:
        inspector = inspect(engine)
        if table not in inspector.get_table_names():
            return
        existing = {item["name"] for item in inspector.get_columns(table)}
        if column in existing:
            return
        with engine.begin() as connection:
            connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}"))

    for column, ddl in (
        ("inn", "VARCHAR(12) UNIQUE"),
        ("snils", "VARCHAR(32)"),
        ("birth_date", "DATE"),
        ("source_type", "VARCHAR(64) NOT NULL DEFAULT 'manual'"),
        ("external_1c_id", "VARCHAR(255)"),
        ("onec_status", "VARCHAR(40)"),
        ("onec_status_label", "VARCHAR(80)"),
        ("onec_last_checked_at", "TIMESTAMP"),
        ("onec_last_check_message", "TEXT"),
        ("onec_metadata", "TEXT"),
        ("onec_active_cards_count", "INTEGER NOT NULL DEFAULT 0"),
        ("onec_dismissed_cards_count", "INTEGER NOT NULL DEFAULT 0"),
        ("hire_date", "DATE"),
        ("dismissal_date", "DATE"),
        ("employment_status", "VARCHAR(40) NOT NULL DEFAULT 'unknown'"),
        ("comment", "TEXT"),
        ("naumen_uuid", "VARCHAR(80)"),
        ("naumen_login", "VARCHAR(160)"),
        ("naumen_project_uuid", "VARCHAR(80)"),
        ("naumen_project_title", "VARCHAR(255)"),
        ("naumen_status", "VARCHAR(40) NOT NULL DEFAULT 'not_linked'"),
        ("naumen_status_label", "VARCHAR(80) NOT NULL DEFAULT 'Не сопоставлен'"),
        ("naumen_last_checked_at", "TIMESTAMP"),
        ("naumen_last_check_message", "TEXT"),
        ("naumen_last_sync_at", "TIMESTAMP"),
        ("naumen_metadata", "TEXT"),
    ):
        add_column("employees", column, ddl)
    add_column("skills", "project_id", "INTEGER")
    add_column("naumen_operators", "normalized_last_name", "VARCHAR(120)")
    add_column("naumen_operators", "normalized_first_name", "VARCHAR(120)")
    add_column("naumen_operators", "normalized_middle_name", "VARCHAR(120)")

    with engine.begin() as connection:
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS onec_connection_settings (
                id SERIAL PRIMARY KEY,
                connection_mode VARCHAR(40) NOT NULL DEFAULT 'gateway_http',
                gateway_url VARCHAR(512),
                gateway_token_encrypted TEXT,
                infobase_type VARCHAR(20) NOT NULL DEFAULT 'server',
                onec_server VARCHAR(255),
                onec_database VARCHAR(255),
                onec_cluster VARCHAR(255),
                file_base_path VARCHAR(512),
                onec_username VARCHAR(255),
                onec_password_encrypted TEXT,
                infobase_path VARCHAR(512),
                server VARCHAR(255),
                database VARCHAR(255),
                cluster VARCHAR(255),
                username VARCHAR(255),
                password_encrypted TEXT,
                auth_type VARCHAR(40) NOT NULL DEFAULT 'password',
                request_timeout_seconds INTEGER NOT NULL DEFAULT 30,
                enabled BOOLEAN NOT NULL DEFAULT FALSE,
                verify_tls BOOLEAN NOT NULL DEFAULT TRUE,
                auto_disable_dismissed BOOLEAN NOT NULL DEFAULT FALSE,
                check_on_employee_create BOOLEAN NOT NULL DEFAULT FALSE,
                enable_weekly_1c_status_check BOOLEAN NOT NULL DEFAULT TRUE,
                weekly_1c_status_check_day VARCHAR(8) NOT NULL DEFAULT 'SUN',
                weekly_1c_status_check_time VARCHAR(5) NOT NULL DEFAULT '03:00',
                onec_check_batch_size INTEGER NOT NULL DEFAULT 50,
                onec_check_pause_ms INTEGER NOT NULL DEFAULT 200,
                last_check_status VARCHAR(80),
                last_check_message TEXT,
                last_check_at TIMESTAMP,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS employee_import_batches (
                id SERIAL PRIMARY KEY,
                filename VARCHAR(255) NOT NULL,
                status VARCHAR(64) NOT NULL DEFAULT 'processing',
                rows_total INTEGER NOT NULL DEFAULT 0,
                rows_created INTEGER NOT NULL DEFAULT 0,
                rows_updated INTEGER NOT NULL DEFAULT 0,
                rows_failed INTEGER NOT NULL DEFAULT 0,
                created_by_user_id INTEGER REFERENCES users(id),
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                error_message TEXT
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS employee_import_errors (
                id SERIAL PRIMARY KEY,
                batch_id INTEGER NOT NULL REFERENCES employee_import_batches(id),
                row_number INTEGER NOT NULL,
                field VARCHAR(80),
                error_message TEXT NOT NULL,
                raw_data TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS employee_project_access (
                id SERIAL PRIMARY KEY,
                employee_id INTEGER NOT NULL REFERENCES employees(id),
                project_id INTEGER NOT NULL REFERENCES naumen_projects(id),
                can_work BOOLEAN NOT NULL DEFAULT TRUE,
                is_primary BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        connection.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS ux_employee_project_access_employee_project
            ON employee_project_access (employee_id, project_id)
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS employee_team_memberships (
                id SERIAL PRIMARY KEY,
                employee_id INTEGER NOT NULL REFERENCES employees(id),
                team_id INTEGER NOT NULL REFERENCES teams(id),
                project_id INTEGER NOT NULL REFERENCES naumen_projects(id),
                is_primary BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        connection.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS ux_employee_team_memberships_employee_project
            ON employee_team_memberships (employee_id, project_id)
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS onec_status_check_runs (
                id SERIAL PRIMARY KEY,
                run_type VARCHAR(40) NOT NULL DEFAULT 'manual',
                status VARCHAR(40) NOT NULL DEFAULT 'running',
                started_by_user_id INTEGER REFERENCES users(id),
                started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                finished_at TIMESTAMP,
                employees_total INTEGER NOT NULL DEFAULT 0,
                employees_checked INTEGER NOT NULL DEFAULT 0,
                employees_working INTEGER NOT NULL DEFAULT 0,
                employees_dismissed INTEGER NOT NULL DEFAULT 0,
                employees_not_found INTEGER NOT NULL DEFAULT 0,
                employees_failed INTEGER NOT NULL DEFAULT 0,
                error_message TEXT
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS onec_status_check_errors (
                id SERIAL PRIMARY KEY,
                run_id INTEGER NOT NULL REFERENCES onec_status_check_runs(id),
                employee_id INTEGER REFERENCES employees(id),
                inn VARCHAR(12),
                error_message TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        target_project = connection.execute(text("""
            SELECT id
            FROM naumen_projects
            WHERE title = 'X5 Retail group' AND is_active = TRUE
            ORDER BY id
            LIMIT 1
        """)).scalar()
        if target_project is None:
            target_project = connection.execute(text("""
                SELECT id
                FROM naumen_projects
                WHERE is_active = TRUE
                ORDER BY is_default DESC, id
                LIMIT 1
            """)).scalar()
        if target_project is not None:
            connection.execute(text("""
                INSERT INTO employee_project_access (employee_id, project_id, can_work, is_primary)
                SELECT e.id, COALESCE(e.project_id, :target_project), TRUE, TRUE
                FROM employees e
                WHERE NOT EXISTS (
                    SELECT 1 FROM employee_project_access access
                    WHERE access.employee_id = e.id
                    AND access.project_id = COALESCE(e.project_id, :target_project)
                )
            """), {"target_project": target_project})
            connection.execute(text("""
                UPDATE employees
                SET project_id = :target_project, updated_at = CURRENT_TIMESTAMP
                WHERE project_id IS NULL
            """), {"target_project": target_project})
            connection.execute(text("""
                UPDATE teams
                SET project_id = :target_project, updated_at = CURRENT_TIMESTAMP
                WHERE project_id IS NULL
            """), {"target_project": target_project})
            connection.execute(text("""
                INSERT INTO employee_team_memberships (employee_id, team_id, project_id, is_primary)
                SELECT e.id, e.team_id, COALESCE(t.project_id, e.project_id, :target_project), TRUE
                FROM employees e
                LEFT JOIN teams t ON t.id = e.team_id
                WHERE e.team_id IS NOT NULL
                AND NOT EXISTS (
                    SELECT 1 FROM employee_team_memberships m
                    WHERE m.employee_id = e.id
                    AND m.project_id = COALESCE(t.project_id, e.project_id, :target_project)
                )
            """), {"target_project": target_project})
        connection.execute(text("UPDATE skills SET project_id = NULL WHERE project_id IS NOT NULL"))
        for skill_name in (
            "Входящие звонки",
            "Исходящие звонки",
            "Холодные звонки",
            "Горячие звонки",
            "Чаты",
            "Email",
            "Backoffice",
            "Контроль качества",
            "Продажи",
            "Поддержка",
            "VIP-линия",
            "Претензионная работа",
            "Удержание",
            "РГ",
            "РО",
        ):
            connection.execute(text("""
                INSERT INTO skills (name, description, is_active, created_at, updated_at)
                SELECT CAST(:name AS VARCHAR), 'Стандартный глобальный операторский навык', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                WHERE NOT EXISTS (SELECT 1 FROM skills WHERE lower(name) = lower(CAST(:name AS VARCHAR)))
            """), {"name": skill_name})
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS app_settings (
                id SERIAL PRIMARY KEY,
                key VARCHAR(120) UNIQUE NOT NULL,
                value TEXT,
                value_type VARCHAR(40) NOT NULL DEFAULT 'string',
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS naumen_operators (
                id SERIAL PRIMARY KEY,
                project_id INTEGER REFERENCES naumen_projects(id),
                naumen_uuid VARCHAR(80) NOT NULL,
                project_uuid VARCHAR(80),
                partner_uuid VARCHAR(80),
                full_name VARCHAR(255),
                normalized_last_name VARCHAR(120),
                normalized_first_name VARCHAR(120),
                normalized_middle_name VARCHAR(120),
                login VARCHAR(160),
                email VARCHAR(255),
                phone VARCHAR(64),
                state VARCHAR(80),
                substate VARCHAR(80),
                skills TEXT,
                raw_data TEXT,
                last_seen_at TIMESTAMP,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        connection.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS ux_naumen_operators_project_uuid
            ON naumen_operators ((COALESCE(project_id, 0)), naumen_uuid)
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS employee_daily_stats (
                id SERIAL PRIMARY KEY,
                project_id INTEGER REFERENCES naumen_projects(id),
                employee_id INTEGER NOT NULL REFERENCES employees(id),
                stat_date DATE NOT NULL,
                source_system VARCHAR(40) NOT NULL DEFAULT 'manual',
                handled_contacts INTEGER NOT NULL DEFAULT 0,
                offered_contacts INTEGER NOT NULL DEFAULT 0,
                average_handle_time_sec INTEGER NOT NULL DEFAULT 0,
                service_level_percent DOUBLE PRECISION NOT NULL DEFAULT 0,
                occupancy_percent DOUBLE PRECISION NOT NULL DEFAULT 0,
                adherence_percent DOUBLE PRECISION NOT NULL DEFAULT 0,
                login_time_sec INTEGER NOT NULL DEFAULT 0,
                productive_time_sec INTEGER NOT NULL DEFAULT 0,
                not_ready_time_sec INTEGER NOT NULL DEFAULT 0,
                raw_data TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS employee_interval_stats (
                id SERIAL PRIMARY KEY,
                project_id INTEGER REFERENCES naumen_projects(id),
                employee_id INTEGER NOT NULL REFERENCES employees(id),
                interval_start TIMESTAMP NOT NULL,
                interval_end TIMESTAMP NOT NULL,
                queue_id INTEGER REFERENCES queues(id),
                source_system VARCHAR(40) NOT NULL DEFAULT 'manual',
                handled_contacts INTEGER NOT NULL DEFAULT 0,
                average_handle_time_sec INTEGER NOT NULL DEFAULT 0,
                service_level_percent DOUBLE PRECISION NOT NULL DEFAULT 0,
                occupancy_percent DOUBLE PRECISION NOT NULL DEFAULT 0,
                raw_data TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS employee_attendance_facts (
                id SERIAL PRIMARY KEY,
                project_id INTEGER REFERENCES naumen_projects(id),
                employee_id INTEGER NOT NULL REFERENCES employees(id),
                work_date DATE NOT NULL,
                planned_shift_id INTEGER REFERENCES shifts(id),
                planned_start TIMESTAMP,
                planned_end TIMESTAMP,
                actual_start TIMESTAMP,
                actual_end TIMESTAMP,
                status VARCHAR(40) NOT NULL DEFAULT 'unknown',
                source_system VARCHAR(40) NOT NULL DEFAULT 'manual',
                raw_data TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        connection.execute(text("""
            UPDATE employees
            SET onec_status = 'not_checked',
                onec_status_label = 'Не проверялся',
                onec_last_check_message = 'Требуется повторная сверка через полноценный 1С Gateway.'
            WHERE onec_status = 'ok'
        """))
        connection.execute(text("""
            UPDATE employees
            SET onec_last_check_message = 'Требуется повторная сверка через полноценный 1С Gateway.'
            WHERE onec_last_check_message ILIKE '%test listener works%'
        """))
        connection.execute(text("""
            UPDATE employees
            SET onec_last_check_message = 'Требуется повторная сверка. Ранее Gateway был недоступен, сейчас подключение 1С нужно проверить заново.'
            WHERE onec_status = 'gateway_unavailable'
              AND EXISTS (
                SELECT 1 FROM onec_connection_settings
                WHERE last_check_status IN ('ok', 'connected')
              )
        """))
        connection.execute(text("""
            UPDATE naumen_projects
            SET title = 'X5 Retail Group (неактивный дубль)',
                project_uuid = 'archived-x5-duplicate-corebo00000000000p2hcq728jesuk0o',
                is_active = FALSE
            WHERE project_uuid = 'corebo00000000000p2hcq728jesuk0o'
              AND lower(title) <> lower('X5 Retail group')
        """))
        connection.execute(text("""
            UPDATE naumen_projects
            SET title = 'X5 Retail Group',
                project_uuid = 'corebo00000000000p2hcq728jesuk0o',
                is_active = TRUE
            WHERE lower(title) = lower('X5 Retail group')
               OR title = 'X5 Retail Group'
        """))
        connection.execute(text("UPDATE integration_settings SET enabled = FALSE, updated_at = CURRENT_TIMESTAMP WHERE display_name = 'Naumen' OR provider = 'telephony'"))

    for column, ddl in (
        ("gateway_token_encrypted", "TEXT"),
        ("infobase_type", "VARCHAR(20) NOT NULL DEFAULT 'server'"),
        ("onec_server", "VARCHAR(255)"),
        ("onec_database", "VARCHAR(255)"),
        ("onec_cluster", "VARCHAR(255)"),
        ("file_base_path", "VARCHAR(512)"),
        ("onec_username", "VARCHAR(255)"),
        ("onec_password_encrypted", "TEXT"),
    ):
        add_column("onec_connection_settings", column, ddl)

    with engine.begin() as connection:
        connection.execute(text("""
            UPDATE onec_connection_settings
            SET
                onec_server = COALESCE(onec_server, server),
                onec_database = COALESCE(onec_database, database),
                onec_cluster = COALESCE(onec_cluster, cluster),
                file_base_path = COALESCE(file_base_path, infobase_path),
                onec_username = COALESCE(onec_username, username),
                onec_password_encrypted = COALESCE(onec_password_encrypted, password_encrypted)
        """))
