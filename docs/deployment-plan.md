# Deployment Plan

1. Stage 1 bootstrap: skeleton, Docker Compose, healthchecks, docs.
2. Stage 1.1 access: Nginx reverse proxy and safe integration placeholder.
3. Stage 2 WFM MVP: database models, CRUD API, demo data, working frontend tabs, brand design.
4. Stage 3 planning logic: staffing calculation, workload import and draft schedule generation.
5. Stage 4 advanced scheduler: skill coverage, more accurate calculations, plan/fact reports and publishing workflow.
6. Stage 5 auth and hardening: выполнено. Добавлены users, roles, permissions, audit log, fact import, export log, RBAC, frontend login и базовый application hardening.
7. Stage 6 production foundation: Alembic migrations, backups, monitoring, production deployment and external data adapter preparation without real integration.
8. Stage 7 external integration: Naumen adapter after API confirmation.
9. Stage 8 reports/customer cabinet: advanced KPI, filters, exports and roles.
10. Stage 9 hardening/production: TLS, SSO/httpOnly auth, backups, monitoring and observability.
# Обновление Этапа 7

Внешние интеграции не подключались. Для production перед пилотом остаются TLS, backup cron, проверка restore, UAT-чеклист и пользовательская документация. Timefold не устанавливался.

# Обновление Этапа 7.2

Naumen-интеграция подготовлена как отключаемый модуль с настройками через UI и dry run. Реальные внешние подключения, TLS, SSO и production scheduler синхронизации не включались. Перед пилотом нужны тестовый контур Naumen, подтверждённые endpoints для интервальной нагрузки/KPI и регламент безопасного хранения параметров.
