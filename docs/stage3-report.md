# Отчёт Этапа 3

Дата выполнения: 2026-05-26

## 1. Что было до изменений

После Этапа 2 проект уже имел рабочие базовые страницы WFM, backend CRUD API, PostgreSQL, Redis, scheduler-заглушку и Nginx-доступ к сайту.

## 2. Что реализовано

- CSV-импорт интервальной нагрузки.
- Таблицы пакетов импорта и ошибок строк.
- Расчёт потребности операторов по MVP-формуле.
- Настройки планирования.
- Правила планирования.
- Черновая генерация графиков.
- Подтверждение, публикация и отмена назначений.
- Dashboard с блоками потребности, покрытия, последних импортов и графиков на сегодня.
- Scheduler preview endpoint для расчёта required agents.
- Базовые backend-тесты.

## 3. Добавленные таблицы

- `import_batches`
- `import_errors`
- `planning_settings`
- `schedule_rules`

## 4. Добавленные маршруты

- `POST /api/v1/imports/workload-csv`
- `GET /api/v1/imports`
- `GET /api/v1/imports/{id}`
- `GET /api/v1/planning/settings`
- `POST /api/v1/planning/settings`
- `POST /api/v1/planning/calculate-staffing`
- `GET /api/v1/schedule-rules`
- `POST /api/v1/schedule-rules`
- `PUT /api/v1/schedule-rules/{id}`
- `POST /api/v1/schedules/generate-draft`
- `POST /api/v1/schedules/{id}/confirm`
- `POST /api/v1/schedules/{id}/publish`
- `POST /api/v1/schedules/{id}/cancel`
- `POST /api/v1/scheduler/calculate-preview`

## 5. CSV-импорт

Файл должен содержать колонки:

`date, interval_start, interval_end, queue_name, offered_contacts, handled_contacts, abandoned_contacts, average_handle_time_sec, service_level_percent`.

Очередь сопоставляется по `queue_name`. Если очередь не найдена, строка не импортируется, а ошибка сохраняется в `import_errors`. Повторная загрузка того же интервала и очереди обновляет существующую запись.

Пример: `data/imports/workload-sample.csv`.

## 6. Расчёт потребности

Формула MVP:

- `workload_seconds = offered_contacts * average_handle_time_sec`;
- `interval_seconds = длительность интервала`;
- `raw_agents = workload_seconds / interval_seconds`;
- `required_agents = ceil(raw_agents / target_occupancy)`.

По умолчанию `target_occupancy = 0.85`.

## 7. Генерация чернового графика

Алгоритм берёт активных сотрудников, активные смены и рассчитанную потребность за период. Для каждой даты и очереди используется пиковая потребность. Сотрудники с отсутствием на дату исключаются. Один сотрудник не назначается дважды в один день. `confirmed` и `published` назначения не удаляются; пересоздаются только `draft` назначения выбранного периода.

## 8. Изменённые страницы frontend

- Dashboard: добавлены реальные блоки сводки.
- Нагрузка: добавлен CSV-импорт.
- Потребность: добавлен выбор периода и кнопка расчёта.
- Графики: добавлена генерация черновика и действия со статусами.
- Настройки: добавлены правила планирования.

## 9. Проверки

- `docker compose up -d --build`
- `docker compose ps`
- `docker compose exec -T backend pytest -q`
- `docker compose exec -T frontend npm run build`
- `curl -i http://127.0.0.1/api/v1/version`
- `curl -i -F file=@data/imports/workload-sample.csv http://127.0.0.1/api/v1/imports/workload-csv`
- `curl -i -H 'Content-Type: application/json' -d '{"date_from":"2026-01-15","date_to":"2026-01-21"}' http://127.0.0.1/api/v1/planning/calculate-staffing`
- `curl -i -H 'Content-Type: application/json' -d '{"date_from":"2026-01-15","date_to":"2026-01-21","queue_id":null}' http://127.0.0.1/api/v1/schedules/generate-draft`
- `curl -i -H 'Content-Type: application/json' -d '{"offered_contacts":120,"average_handle_time_sec":240,"interval_minutes":30,"target_occupancy":0.85}' http://127.0.0.1/scheduler/api/v1/scheduler/calculate-preview`

Результаты:

- backend и scheduler отвечают;
- sample CSV импортирован: 4 строки успешно, 0 ошибок;
- потребность рассчитана: 4 интервала;
- draft-график создан: 10 назначений;
- scheduler preview вернул `required_agents = 19`;
- backend tests: 4 passed;
- frontend build успешен.

## 10. Ограничения MVP

- Нет промышленного оптимизатора.
- Покрытие навыков учитывается только архитектурно, без сложной матрицы queue-skill.
- Нет прогноза нагрузки.
- Нет авторизации.
- Нет Alembic migrations.
- Нет внешних интеграций.

## 11. Что не делалось

- Внешние интеграции.
- Реальные подключения к сторонним системам.
- Работа с токенами, логинами, паролями и секретами.
- Промышленный оптимизатор.
- Полноценная авторизация.
- Сложные графики и прогнозирование.
- Изменение SSH, mihomo, codex, firewall или системного доступа.

## 12. Этап 4

Этап 4 — улучшенный планировщик, покрытие по навыкам, более точный расчёт, публикация графиков и отчёты план/факт.

## 13. Итог

Этап 3 выполнен. Импорт, расчёт потребности и генерация чернового графика работают локально. Проект готов к Этапу 4.
