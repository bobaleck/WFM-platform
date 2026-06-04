# Database Model

Таблицы MVP создаются автоматически при старте backend через `Base.metadata.create_all`, а недостающие поля добавляются безопасными `ALTER TABLE`. Alembic оставлен на Этап 6.

## users

Пользователи будущей системы авторизации.

Ключевые поля: `id`, `email`, `username`, `full_name`, `password_hash`, `role_id`, `role`, `is_active`, `is_superuser`, `last_login_at`, `created_at`, `updated_at`.

## roles

Роли RBAC.

Ключевые поля: `id`, `code`, `name`, `description`, `is_system`, `created_at`, `updated_at`.

## permissions

Права доступа.

Ключевые поля: `id`, `code`, `name`, `description`, `created_at`.

## role_permissions

Связь ролей и прав.

Ключевые поля: `id`, `role_id`, `permission_id`, `created_at`.

## teams

Команды контактного центра.

Ключевые поля: `id`, `name`, `description`, `supervisor_name`, `is_active`, `created_at`, `updated_at`.

## employees

Сотрудники и операторы.

Ключевые поля: `id`, `personnel_number`, `full_name`, `email`, `phone`, `position`, `team_id`, `employment_type`, `timezone`, `is_active`, `created_at`, `updated_at`.

## skills

Навыки обслуживания.

Ключевые поля: `id`, `name`, `description`, `is_active`, `created_at`, `updated_at`.

## employee_skills

Связь сотрудников и навыков.

Ключевые поля: `id`, `employee_id`, `skill_id`, `level`, `created_at`.

## queue_skills

Требуемые навыки очередей.

Ключевые поля: `id`, `queue_id`, `skill_id`, `min_level`, `is_required`, `created_at`, `updated_at`.

## queues

Очереди и каналы обслуживания.

Ключевые поля: `id`, `name`, `channel`, `description`, `service_level_target`, `target_answer_time_sec`, `is_active`, `created_at`, `updated_at`.

## workload_intervals

Интервальная нагрузка по очередям.

Ключевые поля: `id`, `interval_start`, `interval_end`, `queue_id`, `offered_contacts`, `handled_contacts`, `abandoned_contacts`, `average_handle_time_sec`, `service_level_percent`, `created_at`.

## import_batches

Пакеты CSV-импорта.

Ключевые поля: `id`, `import_type`, `filename`, `status`, `rows_total`, `rows_success`, `rows_failed`, `created_at`, `completed_at`, `error_message`.

## import_errors

Ошибки строк CSV-импорта.

Ключевые поля: `id`, `batch_id`, `row_number`, `error_message`, `raw_data`, `created_at`.

`import_type=actual_work_csv` используется для импорта фактической работы.

## staffing_requirements

Потребность и план по операторам.

Ключевые поля: `id`, `interval_start`, `interval_end`, `queue_id`, `required_agents`, `planned_agents`, `gap_agents`, `calculation_note`, `created_at`.

## planning_settings

Настройки расчёта потребности и базовых ограничений.

Ключевые поля: `id`, `target_occupancy`, `default_interval_minutes`, `min_agents_per_queue`, `max_hours_per_employee_per_week`, `min_rest_hours_between_shifts`, `created_at`, `updated_at`.

## schedule_rules

Правила планирования.

Ключевые поля: `id`, `name`, `value`, `description`, `is_active`, `created_at`, `updated_at`.

## shifts

Типовые смены.

Ключевые поля: `id`, `name`, `start_time`, `end_time`, `break_minutes`, `paid_hours`, `is_active`, `created_at`, `updated_at`.

## schedule_assignments

Назначения сотрудников на смены.

Ключевые поля: `id`, `work_date`, `employee_id`, `shift_id`, `queue_id`, `status`, `note`, `confirmed_at`, `published_at`, `cancelled_at`, `created_at`, `updated_at`.

## schedule_coverage

Покрытие потребности назначениями по интервалам.

Ключевые поля: `id`, `interval_start`, `interval_end`, `queue_id`, `required_agents`, `planned_agents`, `confirmed_agents`, `published_agents`, `gap_agents`, `coverage_percent`, `created_at`, `updated_at`.

## schedule_generation_runs

Запуски генерации чернового графика.

Ключевые поля: `id`, `date_from`, `date_to`, `status`, `created_assignments`, `skipped_assignments`, `coverage_gaps`, `warnings_json`, `created_at`.

## absences

Отсутствия сотрудников.

Ключевые поля: `id`, `employee_id`, `absence_type`, `date_from`, `date_to`, `status`, `comment`, `created_at`, `updated_at`.

## kpi_snapshots

Снимки KPI по очередям.

Ключевые поля: `id`, `snapshot_date`, `queue_id`, `service_level_percent`, `average_speed_answer_sec`, `average_handle_time_sec`, `occupancy_percent`, `utilization_percent`, `abandonment_percent`, `created_at`.

## actual_work_intervals

Фактическая работа сотрудников по интервалам.

Ключевые поля: `id`, `work_date`, `employee_id`, `queue_id`, `interval_start`, `interval_end`, `status`, `actual_minutes`, `source`, `created_at`, `updated_at`.

## export_log

Журнал CSV-экспортов.

Ключевые поля: `id`, `user_id`, `report_type`, `filename`, `rows_count`, `created_at`.

## audit_log

Журнал действий пользователей и системных операций.

Ключевые поля: `id`, `actor_user_id`, `actor_username`, `actor`, `action`, `entity_type`, `entity_id`, `details`, `details_json`, `ip_address`, `user_agent`, `created_at`.
# Обновление Этапа 7

В модель добавлены поля `planning_settings`: `max_consecutive_work_days`, `preferred_shift_balance_enabled`, `weekend_balance_enabled`, `skill_priority_weight`, `fairness_weight`, `coverage_weight`. Добавлена таблица `schedule_recommendations` для рекомендаций планировщика.

# Обновление Этапа 7.2

Добавлены таблицы подготовки Naumen-интеграции:

- `naumen_connection_settings`: base URL, auth mode, username, зашифрованные API key/Basic password, timeout, verify SSL, enabled, last check status/message/time.
- `naumen_sync_runs`: история запусков sync/dry run, статус и счётчики строк.
- `naumen_sync_errors`: ошибки строк синхронизации.
- `external_mappings`: связь внешних идентификаторов Naumen с внутренними сущностями WFM.

Секретные поля не возвращаются открытым текстом через API. Demo/business data очищаются скриптом `scripts/clear-demo-data.sh --confirm` без удаления таблиц, ролей, permissions, admin и миграций.

# Обновление Этапа 8

Добавлена проектная модель Naumen и контекст активного проекта:

- `naumen_projects`: UUID проекта Naumen, название, partner UUID, state, data channel, cluster id, active/default flags, даты проверки и синхронизации.
- `user_project_access`: доступ пользователя к проектам, флаги `can_view` и `can_sync`.
- `user_preferences`: выбранный пользователем активный проект.
- `naumen_project_schedule_rules`: справочные правила расписания проекта из `GET /projects/{projectUuid}/schedule`.

В `naumen_connection_settings` добавлены `api_version`, `last_check_http_status`, `last_check_endpoint`.
В `naumen_sync_runs` добавлен `project_id`.
В `external_mappings` добавлен `project_id`.

В основные WFM-таблицы добавлен nullable `project_id` для фильтрации бизнес-данных по активному проекту: `employees`, `teams`, `queues`, `shifts`, `workload_intervals`, `staffing_requirements`, `schedule_assignments`, `schedule_coverage`, `absences`, `kpi_snapshots`, `actual_work_intervals`, `import_batches`.

# Обновление Этапа 9

Naumen переведён в архивный источник. Новая рабочая интеграция — сверка кадрового статуса с 1С по ИНН через Windows Gateway.

В `employees` добавлены поля: `inn`, `snils`, `birth_date`, `source_type`, `external_1c_id`, `onec_status`, `onec_status_label`, `onec_last_checked_at`, `onec_last_check_message`, `onec_active_cards_count`, `onec_dismissed_cards_count`, `hire_date`, `dismissal_date`, `employment_status`, `comment`.

Новые таблицы:

- `onec_connection_settings`: режим подключения, gateway URL, параметры базы 1С, username, encrypted password, timeout, enabled, TLS, настройки автоматической сверки, last check;
- `employee_import_batches`: история Excel-импортов сотрудников;
- `employee_import_errors`: ошибки строк Excel-импорта;
- `onec_status_check_runs`: массовые сверки статусов с 1С;
- `onec_status_check_errors`: ошибки массовой сверки.

Исторические таблицы Naumen не удаляются. `naumen_connection_settings.enabled` и legacy `integration_settings.enabled` переводятся в `false`.

# Обновление Этапа 9.1

Naumen удалён из рабочего UI и активной регистрации API. Исторические таблицы и legacy-код не удалялись, чтобы не ломать backup/history.

Добавлена ручная модель рабочего контура поверх существующей проектной таблицы: API `/api/v1/contours` возвращает пользовательские поля `id`, `name`, `description`, `is_active`, `is_default`, `created_at`, `updated_at`.

Добавлена таблица `app_settings` для пользовательских настроек приложения. Секреты в ней не хранятся.

Для ручного MVP используются:

- `employees`: ручная карточка сотрудника, WFM-статус, ИНН и поля сверки 1С;
- `teams`, `skills`, `queues`, `shifts`, `absences`: ручные справочники с архивированием через `is_active/status`;
- `employee_import_batches`, `employee_import_errors`: XLSX-реестры сотрудников;
- `workload_intervals`: XLSX/CSV-нагрузка;
- `planning_settings`, `staffing_requirements`: расчёт потребности;
- `schedule_assignments`, `schedule_coverage`, `schedule_generation_runs`: графики и покрытие;
- `onec_connection_settings`, `onec_status_check_runs`, `onec_status_check_errors`: настройки и история сверки с 1С.

# Обновление Этапа 9.3

Сотрудник стал связанной моделью WFM + 1С + Naumen. В `employees` добавлены поля Naumen: `naumen_uuid`, `naumen_login`, `naumen_project_uuid`, `naumen_project_title`, `naumen_status`, `naumen_status_label`, `naumen_last_checked_at`, `naumen_last_check_message`, `naumen_last_sync_at`, `naumen_metadata`.

Добавлены таблицы:

- `naumen_operators`: локально загруженные операторы Naumen по рабочему контуру;
- `employee_daily_stats`: дневная статистика сотрудника;
- `employee_interval_stats`: интервальная статистика сотрудника;
- `employee_attendance_facts`: фактические выходы сотрудника.

`skills` получил `project_id`, чтобы навыки фильтровались по рабочему контуру. `onec_status='ok'` нормализуется в `check_error`.
# Актуализация этапа 9.4

Добавлены таблицы:

- `employee_project_access`: доступ сотрудника к нескольким рабочим контурам.
- `employee_team_memberships`: членство сотрудника в проектной команде.

`employees.project_id` сохранён как legacy/primary поле совместимости, но пользовательская видимость сотрудников определяется через `employee_project_access`.

`teams.project_id` остаётся обязательной бизнес-связью: команда принадлежит одному рабочему контуру.

`skills.project_id` больше не используется пользовательской логикой. Навыки глобальные, связи сотрудников с навыками хранятся в `employee_skills`, требования очередей — в `queue_skills`.

В `naumen_operators` добавлены нормализованные части ФИО: `normalized_last_name`, `normalized_first_name`, `normalized_middle_name`. Они используются для сопоставления WFM-сотрудника с оператором Naumen внутри проекта.

Legacy-поля `employees.snils` и `employees.naumen_login` могут оставаться в таблице nullable, но удалены из интерфейса, шаблонов импорта и новых пользовательских сценариев.
# Обновление этапа 9.8

Активный проект `X5 Retail Group` связан с Naumen UUID `corebo00000000000p2hcq728jesuk0o`; неактивный дубль проекта сохранён отдельно. Сотрудники фильтруются по `employee_project_access`. Команды используют `employee_team_memberships`. Навыки глобальные и назначаются через `employee_skills`. Архив сотрудников реализован через локальные WFM-флаги без изменения 1С и Naumen.
