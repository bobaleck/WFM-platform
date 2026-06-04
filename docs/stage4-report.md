# Отчёт Этапа 4

Дата выполнения: 2026-05-26

## 1. Что было до изменений

После Этапа 3 проект содержал CSV-импорт нагрузки, расчёт потребности по MVP-формуле, базовые правила планирования, черновую генерацию графиков, Dashboard и рабочие разделы WFM.

## 2. Что реализовано

- Связь очередей с требуемыми навыками.
- Генерация графиков с учётом обязательных навыков и уровней.
- Расчёт потребности с `shrinkage_percent`.
- Покрытие по интервалам.
- Подтверждение и публикация графиков за период.
- Поля времени подтверждения, публикации и отмены назначений.
- План/факт по опубликованному плану и ручному факту.
- CSV-экспорт графиков, покрытия и план/факт.
- Dashboard с покрытием, дефицитами, генерациями и план/факт.
- Frontend-блоки для навыков очередей, покрытия, публикации и отчётов.

## 3. Добавленные таблицы

- `queue_skills`
- `schedule_coverage`
- `schedule_generation_runs`
- `actual_work_intervals`

Также добавлены поля в существующие таблицы:

- `planning_settings.shrinkage_percent`
- `planning_settings.service_level_target`
- `planning_settings.average_patience_sec`
- `planning_settings.calculation_method`
- `schedule_assignments.confirmed_at`
- `schedule_assignments.published_at`
- `schedule_assignments.cancelled_at`

## 4. Добавленные маршруты

- `GET /api/v1/queues/{queue_id}/skills`
- `POST /api/v1/queues/{queue_id}/skills`
- `PUT /api/v1/queues/{queue_id}/skills/{id}`
- `DELETE /api/v1/queues/{queue_id}/skills/{id}`
- `POST /api/v1/schedules/recalculate-coverage`
- `GET /api/v1/coverage`
- `GET /api/v1/coverage/export.csv`
- `POST /api/v1/schedules/confirm-period`
- `POST /api/v1/schedules/publish-period`
- `GET /api/v1/actual-work`
- `POST /api/v1/actual-work`
- `PUT /api/v1/actual-work/{id}`
- `DELETE /api/v1/actual-work/{id}`
- `GET /api/v1/reports/plan-fact`
- `GET /api/v1/reports/plan-fact.csv`
- `GET /api/v1/schedules/export.csv`

## 5. Очереди и навыки

Таблица `queue_skills` задаёт обязательные навыки очереди, минимальный уровень и признак обязательности. В демо-данных:

- «Входящая линия» требует «Входящие звонки»;
- «Исходящая линия» требует «Исходящие звонки»;
- «Чат-поддержка» требует «Чаты».

Сотрудникам добавлены дополнительные навыки с уровнями от 1 до 5.

## 6. Улучшенный расчёт потребности

Расчёт сохраняет MVP-формулу, но добавляет shrinkage:

- `base_required = ceil(raw_agents / target_occupancy)`;
- `required_with_shrinkage = ceil(base_required / (1 - shrinkage_percent / 100))`.

В `calculation_note` записываются contacts, AHT, target occupancy, shrinkage и метод.

## 7. Генерация графика

Генератор:

- берёт активных сотрудников и смены;
- исключает отсутствующих;
- не назначает сотрудника дважды в день;
- проверяет обязательные навыки очереди;
- сортирует кандидатов по соответствию навыкам и текущей загрузке;
- не назначает неподходящих сотрудников при обязательном навыке;
- сохраняет warnings по дефицитам;
- пересчитывает coverage после генерации.

## 8. Покрытие

Coverage считается по каждому интервалу из `staffing_requirements`. Смена покрывает интервал, если интервал попадает внутрь времени смены. Учитываются только назначения с тем же `queue_id`.

## 9. Публикация графиков

- `confirm-period`: переводит `draft -> confirmed`;
- `publish-period`: переводит `confirmed -> published`;
- `cancelled` не трогается;
- после публикации coverage пересчитывается.

## 10. План/факт

Плановые часы считаются по опубликованным назначениям. Фактические часы считаются из `actual_work_intervals`. `adherence_percent = actual_hours / planned_hours * 100`.

## 11. CSV-экспорты

- `GET /api/v1/schedules/export.csv`
- `GET /api/v1/coverage/export.csv`
- `GET /api/v1/reports/plan-fact.csv`

CSV отдаётся в UTF-8 с BOM.

## 12. Изменённые страницы frontend

- Dashboard
- Очереди
- Потребность
- Графики
- Отчёты
- Настройки частично используют общие компоненты

## 13. Проверки

- `docker compose up -d --build`
- `docker compose ps`
- `curl -i http://127.0.0.1/api/v1/version`
- `curl -i http://127.0.0.1/api/v1/queues/1/skills`
- `curl -i http://127.0.0.1/api/v1/planning/settings`
- `curl -i -H 'Content-Type: application/json' -d '{"date_from":"2026-01-15","date_to":"2026-01-21"}' http://127.0.0.1/api/v1/planning/calculate-staffing`
- `curl -i -H 'Content-Type: application/json' -d '{"date_from":"2026-01-15","date_to":"2026-01-21","queue_id":null}' http://127.0.0.1/api/v1/schedules/generate-draft`
- `curl -i -H 'Content-Type: application/json' -d '{"date_from":"2026-01-15","date_to":"2026-01-21","queue_id":null}' http://127.0.0.1/api/v1/schedules/confirm-period`
- `curl -i -H 'Content-Type: application/json' -d '{"date_from":"2026-01-15","date_to":"2026-01-21","queue_id":null}' http://127.0.0.1/api/v1/schedules/publish-period`
- `curl -i http://127.0.0.1/api/v1/coverage`
- `curl -i 'http://127.0.0.1/api/v1/reports/plan-fact?date_from=2026-01-15&date_to=2026-01-21'`
- `curl -i http://127.0.0.1/api/v1/schedules/export.csv`
- `curl -i http://127.0.0.1/api/v1/coverage/export.csv`
- `curl -i 'http://127.0.0.1/api/v1/reports/plan-fact.csv?date_from=2026-01-15&date_to=2026-01-21'`
- `docker compose exec -T backend pytest -q`
- `docker compose exec -T frontend npm run build`

## 14. Тесты

Backend tests: 10 passed.

Проверены:

- расчёт с shrinkage;
- соответствие сотрудника навыкам очереди;
- отсутствие на дату;
- дефицит покрытия;
- публикация только `confirmed -> published`;
- plan/fact adherence.

## 15. Ограничения MVP

- Нет промышленного оптимизатора.
- Нет полной матрицы предпочтений и расписаний отдыха.
- Нет авторизации.
- Нет внешних интеграций.
- Факт вводится вручную или демо-данными.
- Alembic ещё не подключён; для MVP используется auto-create и безопасное добавление колонок.

## 16. Что не делалось

- Внешние интеграции.
- Реальные подключения к сторонним системам.
- Полноценная промышленная оптимизация.
- Авторизация пользователей.
- Изменение SSH, mihomo, codex, firewall или системного доступа.

## 17. Этап 5

Этап 5 — авторизация пользователей, роли, журнал действий, улучшенный импорт факта, подготовка к подключению внешнего источника данных и production hardening.

## 18. Итог

Этап 4 выполнен. Навыки очередей, расчёт с shrinkage, генерация с учётом навыков, покрытие, публикация, план/факт и CSV-экспорты работают локально. Проект готов к Этапу 5.
