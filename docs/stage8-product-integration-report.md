# Этап 8 — продуктовая доводка и Naumen REST API

## Recovery после обрыва предыдущей сессии Codex

Дата recovery: 2026-05-27.

Состояние сервисов на старте recovery:

- `backend`: запущен, `healthy`, порт `127.0.0.1:8000`;
- `frontend`: запущен, порт `127.0.0.1:5173`;
- `postgres`: запущен, `healthy`;
- `redis`: запущен, `healthy`;
- `scheduler`: запущен, `healthy`;
- `/health`: отвечает `{"status":"ok","service":"backend"}`;
- `/api/v1/version`: отвечает, приложение `wfm-naumen`, окружение `development`.

Файлы, изменённые предыдущей сессией и проверенные в recovery:

- `frontend/src/pages/Users.tsx`;
- `frontend/src/components/Sidebar.tsx`;
- `frontend/src/api/wfm.ts`;
- `frontend/src/pages/Reports.tsx`;
- `frontend/src/pages/Schedules.tsx`;
- `frontend/src/pages/GenericTablePage.tsx`;
- `frontend/src/pages/Integration.tsx`;
- `frontend/src/pages/Settings.tsx`;
- `backend/app/models/integration_settings.py`;
- `backend/app/models/wfm.py`;
- `backend/app/db/schema.py`;
- `backend/app/schemas/integration.py`;
- `backend/app/services/integration_settings.py`;
- `backend/app/integrations/naumen/client.py`;
- `backend/app/integrations/naumen/service.py`;
- `backend/app/api/integration.py`;
- `backend/app/api/admin.py`;
- `backend/app/core/rbac.py`.

Найдено при recovery:

- ожидаемая host-сборка `npm --prefix frontend run build` недоступна из-за отсутствия локального `node_modules`; проект проверяется через Docker;
- подозрение на ошибку `.current` в `Users.tsx` не подтвердилось: spread уже был корректным;
- прямые CSV-ссылки в `Reports.tsx` и `Schedules.tsx` были заменены на авторизованный fetch helper;
- `MVP / Internal` в frontend не найден, заменён на `Внутренняя система`;
- для WFM list endpoints найден риск с `request: Request = None`, исправлено на явную injection-сигнатуру `request: Request`;
- stage8 backend test был неидемпотентным по username, исправлен на уникальный username;
- stage7.2 test был слишком строгим к числу пользователей после добавления пользовательских сценариев, скорректирован на проверку сохранённого admin.

Проверки recovery:

- Python compile изменённых backend-файлов внутри контейнера: успешно;
- frontend build внутри контейнера: успешно;
- backend стартует после уже внесённых изменений.

## Итог recovery

Recovery выполнен до продолжения задач Этапа 8.

Исправленные и стабилизированные зоны:

- frontend: `Users.tsx`, `Sidebar.tsx`, `Reports.tsx`, `Schedules.tsx`, `GenericTablePage.tsx`, `Integration.tsx`, `Settings.tsx`, `api/wfm.ts`, `api/integration.ts`;
- backend: `integration_settings.py`, `wfm.py`, `schema.py`, `integration.py`, `admin.py`, `rbac.py`, Naumen `client.py` и `service.py`;
- документация: README, architecture, database model, operations, Naumen integration docs, frontend checklist.

Явная ошибка `.current` в `Users.tsx` не обнаружена: код уже содержал корректный spread `...current`.
Незакрытых JSX-компонентов и неправильных frontend imports после recovery не осталось: Docker build frontend проходит.
Backend runtime-ошибок schema/model/import после recovery не показал: контейнер стартует и health отвечает.

## Что реализовано по Этапу 8

### Логотип и бренд

- логотип `/home/alex/cvet_tss.svg` скопирован в `frontend/public/assets/cvet_tss.svg`;
- favicon настроен через SVG;
- title вкладки: `WFM-платформа | Телесейлз Сервис`;
- sidebar использует логотип, а не синий квадрат `ТС`;
- яркий `MVP / Internal` заменён на спокойный статус `Внутренняя система`.

### Naumen REST API v2/current

Backend-клиент Naumen использует только `v2` или `current`.
`v1` для новой интеграции не используется.

Поддержанные read-only endpoints:

- `GET /projects/{uuid}`;
- `GET /employees?removed=false`;
- `GET /ous/root/subous`;
- `GET /projects/{projectUuid}/agents`;
- `GET /projects/{projectUuid}/agents/available`;
- `GET /projects/{projectUuid}/schedule`.

Write-запросы в Naumen не реализовывались и не выполнялись.

### Проекты Naumen

- добавлена таблица `naumen_projects`;
- добавлены endpoints `/api/v1/projects`;
- проект добавляется вручную по UUID, потому что endpoint списка всех проектов в PDF не подтверждён;
- проверка проекта выполняется через `GET /projects/{uuid}`;
- `/api/v1/projects/current` объявлен до `/api/v1/projects/{project_id}`;
- текущий проект сохраняется в `user_preferences`;
- sidebar получил selector активного проекта.

### Доступ пользователей к проектам

- добавлена таблица `user_project_access`;
- admin/superuser видит все проекты;
- обычный пользователь видит только назначенные проекты;
- list endpoints основных WFM-разделов фильтруются по `project_id`;
- запрос проекта без доступа возвращает `403`.

### Пользователи и роли

- random user creation убран;
- кнопка «Создать пользователя» открывает модальное окно;
- форма принимает ФИО, username, email, роль, активность, временный пароль и проекты;
- backend сохраняет `project_ids`;
- добавлены endpoints чтения/редактирования пользователя, сброса пароля и управления проектами пользователя;
- отключение последнего admin запрещено.

### Интеграция

- страница «Интеграция» видна только пользователям с `settings:manage`;
- настройки содержат `base_url`, `api_version`, `auth_mode`, `username`, secret fields, timeout, verify SSL, enabled;
- secret fields не возвращаются открытым текстом;
- пустой secret при сохранении не затирает сохранённое значение;
- check connection возвращает endpoint, HTTP status, сообщение и время проверки;
- если интеграция выключена или неполная, возвращается `not_configured`;
- после финальных проверок интеграция оставлена выключенной, чтобы не выполнять случайные обращения.

### Справочники и рабочие сценарии

- ручное создание справочников сотрудников, команд, навыков, очередей и смен в UI отключено;
- страницы объясняют, что данные ожидаются из Naumen sync или CSV fallback;
- «Нагрузка» описана как интервальная статистика и оставлена через CSV fallback;
- «Потребность» объясняет AHT, shrinkage и target occupancy;
- «Графики» получили блок «Как пользоваться»;
- «Отсутствия» оставлены как ручной ввод для admin/supervisor, потому что endpoint отсутствий в PDF не подтверждён.

### Выгрузки

- кнопки CSV в UI заменены на «Выгрузить»;
- прямые ссылки на `.csv` в новой вкладке убраны;
- frontend использует `downloadCsv()` с bearer token;
- API по-прежнему защищает CSV endpoints и возвращает `401` без token;
- успешная проверка с admin-token вернула `text/csv` для executive summary.

### Настройки

- раздел «Настройки» расширен секциями общих параметров, планирования, доступа, интеграции и экспорта;
- часть настроек пока отображается как MVP UI без полноценного persistent `app_settings`;
- секреты интеграции не хранятся в app settings.

## Проверки

Финально выполнено:

- `docker compose up -d --build --force-recreate frontend`;
- `docker compose ps`;
- `curl -s http://127.0.0.1/health`;
- `curl -s http://127.0.0.1/api/v1/version`;
- `docker compose exec -T frontend npm run build`;
- `docker compose exec -T backend pytest`;
- проверка protected `/api/v1/projects` без token: `401`;
- login admin без вывода пароля;
- `/api/v1/auth/me` с token: `200`;
- `/api/v1/projects` с token: `200`;
- `/api/v1/projects/current` с token: `200`;
- `/api/v1/integrations/naumen/settings` с token: `200`;
- `/api/v1/reports/executive-summary.csv` с token: `200`, `text/csv`;
- `/api/v1/projects/check` после выключения интеграции: `not_configured`.

Результаты тестов:

- backend tests: `48 passed, 1 skipped`;
- frontend build: успешно.

## Документы

Созданы или обновлены:

- `docs/naumen-projects-integration.md`;
- `docs/user-project-access.md`;
- `docs/naumen-api-analysis.md`;
- `docs/naumen-integration-map.md`;
- `docs/naumen-integration-operations.md`;
- `docs/database-model.md`;
- `docs/operations.md`;
- `docs/architecture.md`;
- `docs/frontend-pages-checklist.md`;
- `README.md`.

## Ограничения

- реальный тестовый контур Naumen не задан, поэтому внешняя проверка проекта и синхронизация с реальным Naumen не выполнялись;
- интеграция оставлена `enabled=false`;
- endpoint списка всех проектов в PDF не подтверждён;
- endpoint интервальной нагрузки, SLA/AHT по интервалам, отсутствий сотрудников и отдельного справочника очередей в PDF не подтверждён;
- sync employees/departments/project agents/project schedule подготовлен на уровне client/API/UI, но промышленное сохранение всех полей требует тестовых ответов Naumen;
- persistent `app_settings` для всех настроек UI пока не доведён до полноценной модели;
- визуальная проверка выполнялась через сборку и доступность UI/API, без браузерного Playwright-сценария.

## Что делать дальше

- подключить тестовый read-only контур Naumen через UI без хардкода секретов;
- проверить реальные ответы `GET /projects/{uuid}`, `/employees`, `/ous/root/subous`, `/projects/{projectUuid}/agents`, `/projects/{projectUuid}/schedule`;
- уточнить источник интервальной нагрузки, SLA/AHT и отсутствий;
- довести `app_settings` до полноценного persistent API;
- подготовить UAT-сценарии для администратора, супервизора и аналитика;
- настроить production backup cron и регламент проверки восстановления.
