# Этап 9 — ручной WFM, Excel-реестры и сверка с 1С

Дата проверки: 2026-05-31.

## 1. Текущее состояние

Сервер: Ubuntu 20.04.6 LTS, Linux kernel `5.4.0-216-generic`.

После пересборки `docker compose up -d --build` работают:

- backend: `healthy`, `GET /health` возвращает `{"status":"ok","service":"backend"}`;
- frontend: порт `127.0.0.1:5173`, HTTP 200;
- scheduler: `healthy`, `GET /health` возвращает `{"status":"ok","service":"scheduler"}`;
- PostgreSQL: `healthy`;
- Redis: `healthy`;
- admin login: проверен успешно;
- `/api/v1/version`: `naumen_integration=archived`, `onec_integration=gateway_http`.

## 2. Обработка 1С

Файл обработки 1С на сервере не найден в проверенных местах `/home/alex`, `/opt/wfm-naumen/docs` и ближайших подкаталогах. Работа выполнена по бизнес-правилу задачи.

## 3. Почему Naumen отключён

Naumen больше не является актуальным источником данных. Модуль сохранён как архивный, исторические таблицы и `sync_runs` не удалялись. Активные кнопки синхронизации убраны из основного интерфейсного сценария, настройки Naumen переводятся в `enabled=false`.

## 4. Как теперь ведутся данные WFM

Сотрудники, команды, навыки, очереди, смены, нагрузка, графики и отсутствия ведутся вручную или через реестры. В интерфейсных текстах Naumen заменён на ручной контур и сверку с 1С по ИНН.

## 5. Ручное создание сотрудников

В разделе «Сотрудники» добавлены кнопки:

- «Создать сотрудника»;
- «Шаблон»;
- «Загрузить реестр»;
- «Сверить всех с 1С».

Backend принимает поля ФИО, ИНН, СНИЛС, дату рождения, email, телефон, должность, занятость, часовой пояс, WFM-статус и комментарий. ИНН валидируется как 12 цифр, дубли по ИНН блокируются.

## 6. Excel-реестры

Реализованы:

- `GET /api/v1/employees/import/template.xlsx`;
- `POST /api/v1/employees/import/xlsx`;
- таблицы `employee_import_batches`, `employee_import_errors`.

Импорт создаёт/обновляет сотрудников по ИНН, создаёт команды и навыки при необходимости, возвращает счётчики строк и ошибки.

## 7. Сверка с 1С по ИНН

Правило статуса:

- есть карточка без даты увольнения — `Работает`;
- все карточки имеют дату увольнения — `Уволен`;
- ИНН не найден — `Не найден`;
- ошибка запроса — `Ошибка сверки`.

Реализованы поля сотрудников для статуса 1С: `onec_status`, `onec_status_label`, `onec_last_checked_at`, `onec_last_check_message`, `onec_active_cards_count`, `onec_dismissed_cards_count`, `hire_date`, `dismissal_date`, `employment_status`.

## 8. Почему нужен Windows Gateway

Текущий сервер Linux. COM-соединение с 1С напрямую доступно только на Windows-хосте с установленной платформой 1С/COMConnector. Для Linux-сервера нужен отдельный Windows 1C Gateway/Agent.

Целевая схема: `WFM backend -> HTTP -> Windows 1C Gateway -> COMConnector -> база 1С`.

## 9. Настройки 1С

Добавлена таблица `onec_connection_settings` и API:

- `GET /api/v1/integrations/onec/settings`;
- `PUT /api/v1/integrations/onec/settings`;
- `POST /api/v1/integrations/onec/check`;
- `POST /api/v1/integrations/onec/diagnose`.

Пароль 1С хранится зашифрованно и не возвращается открытым текстом. `direct_com` на Linux возвращает понятное сообщение: «Direct COM недоступен на Linux. Используйте Windows 1C Gateway.»

## 10. Одиночная и массовая сверка

Одиночная сверка: `POST /api/v1/employees/{employee_id}/check-1c-status`.

Массовая сверка: `POST /api/v1/employees/check-all-1c-status`, создаёт `onec_status_check_runs` и ошибки в `onec_status_check_errors`. При не настроенном Gateway возвращается понятная ошибка и статус `check_error`.

## 11. Еженедельная сверка

В настройках 1С добавлены параметры:

- `enable_weekly_1c_status_check`;
- `weekly_1c_status_check_day`;
- `weekly_1c_status_check_time`;
- `onec_check_batch_size`;
- `onec_check_pause_ms`.

Интерфейс управления расписанием добавлен. Production-запуск фоновой задачи требует следующего этапа доработки scheduler worker, сейчас настройки сохраняются и автоматический контур не падает.

## 12. Роли и права

Добавлены permissions:

- `employees:import`;
- `employees:sync_1c`;
- `onec:settings:view`;
- `onec:settings:manage`;
- `onec:status-check`;
- `onec:status-check-all`.

Администратор получает все права. Аналитик и управляющий получают импорт и сверку без права изменения системных настроек 1С. Заказчик и только просмотр не получают права сверки.

## 13. Документы и Gateway

Созданы/обновлены:

- `docs/1c-integration.md`;
- `docs/employee-registry-import.md`;
- `docs/1c-gateway-spec.md`;
- `docs/examples/onec_gateway_example.ps1`;
- `docs/database-model.md`;
- `docs/frontend-pages-checklist.md`;
- `docs/operations.md`.

## 14. Проверки

Пройдены:

- `python3 -m compileall backend/app`;
- `npm run build`;
- `docker compose up -d --build`;
- `docker compose ps`;
- backend health;
- scheduler health;
- frontend HTTP 200;
- admin login;
- получение настроек 1С без открытого пароля;
- диагностика `gateway_http` без Gateway: понятное `not_configured`;
- диагностика `direct_com` на Linux: `unsupported`;
- скачивание xlsx-шаблона;
- ручное создание сотрудника;
- xlsx-импорт сотрудника;
- одиночная сверка без Gateway: `check_error`;
- массовая сверка без Gateway: run со статусом `partial_success`;
- backend tests: `53 passed, 1 skipped`.

## 15. Ограничения

- Production Windows 1C Gateway пока не реализован, подготовлена спецификация и пример-скелет.
- Реальные 1С-запросы нужно проверить на тестовой базе 1С.
- Структуру конкретной 1С нужно уточнить: физлица, сотрудники, кадровые регистры, дата увольнения.
- Еженедельный scheduler сохранён в настройках и UI, но production worker запуска массовой сверки нужно выделить следующим этапом.

## 16. Следующий этап

- реализовать production Windows 1C Gateway;
- проверить реальные 1С-запросы на тестовой базе;
- уточнить структуру 1С: физлица, сотрудники, регистры кадровых данных;
- добавить реальные управленческие отчёты.
