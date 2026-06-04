# Эксплуатация Naumen-интеграции

На этапе 8 интеграция подготовлена как read-only модуль Naumen REST API.
Внешние запросы выполняются только по явному действию администратора в UI: проверить подключение, проверить проект или запустить sync/dry run.
Write endpoints Naumen не используются.

## Настройки

UI: раздел «Интеграция».

API:

- `GET /api/v1/integrations/naumen/settings`
- `PUT /api/v1/integrations/naumen/settings`

Поля:

- `base_url`
- `api_version`: `v2` или `current`
- `auth_mode`: `api_key` или `basic`
- `username`
- `api_key`
- `basic_password`
- `request_timeout_seconds`
- `verify_ssl`
- `enabled`

`api_key` и `basic_password` не возвращаются открытым текстом. Если secret-поле отправлено пустым, старое значение не затирается.

## Проверка

`POST /api/v1/integrations/naumen/check`

Если настройки выключены или неполные, возвращается `not_configured` и список недостающих полей.
Если `base_url` содержит `/api/v2`, `/api/current`, `/catalogs` или другой path, возвращается `invalid_settings`: адрес должен быть корневым, например `https://host:8443`.
Если настройки заполнены, проверяется `GET /partners/`, потому что этот endpoint подтверждён вручную.
В ответе сохраняются статус, HTTP-код, `checked_endpoint` и время проверки.

`last_check_endpoint` должен быть `/api/v2/partners/` или `/api/current/partners/`.

## Диагностика

`POST /api/v1/integrations/naumen/diagnose`

Доступ: `settings:manage`.

Ответ показывает валидность настроек, нормализованный корневой адрес, выбранную версию API, режим авторизации, наличие username/secret, вычисленный безопасный URL, HTTP-код и количество элементов. API-токен, пароль, `Authorization` и значение `X-API-Key` не возвращаются.

## Партнёры Naumen

API:

- `GET /api/v1/integrations/naumen/partners`
- `POST /api/v1/integrations/naumen/partners/sync`
- `POST /api/v1/integrations/naumen/partners/{id}/default`
- `PUT /api/v1/integrations/naumen/partners/{id}`

`POST /partners/sync` принимает `{"dry_run": true}` или `{"dry_run": false}`.
При `dry_run=true` backend выполняет read-only `GET /partners/`, возвращает количество и первые элементы, но не сохраняет данные.
При `dry_run=false` backend создаёт или обновляет `naumen_partners` и пишет запуск в `naumen_sync_runs` с `sync_type="partners"`.

## Проекты

Endpoint списка всех проектов в PDF не подтверждён. Проекты добавляются вручную по UUID после уточнения.
Dummy-проекты `11111111111111111111111111111111` и `22222222222222222222222222222222` отключены и не используются для проверки подключения.

API:

- `GET /api/v1/projects`
- `POST /api/v1/projects/check`
- `POST /api/v1/projects`
- `GET /api/v1/projects/current`
- `PUT /api/v1/projects/current`
- `PUT /api/v1/projects/{id}`
- `DELETE /api/v1/projects/{id}` soft delete через `is_active=false`

Проверка проекта использует read-only endpoint Naumen `GET /projects/{uuid}` только для ручной проверки конкретного UUID. Базовая проверка подключения использует `GET /partners/`.
Обычный пользователь видит только проекты из `user_project_access`.
Admin и superuser видят все проекты.

## Dry run

```bash
curl -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"dry_run": true}' \
  http://127.0.0.1/api/v1/integrations/naumen/sync/employees
```

Доступные операции:

- `/sync/employees`
- `/sync/departments`
- `/sync/project-agents`
- `/sync/project-schedule`

Для проектных операций передаётся `project_id`; backend сам берёт `project_uuid` из `naumen_projects`.

## История

- `GET /api/v1/integrations/naumen/sync-runs`
- `GET /api/v1/integrations/naumen/sync-runs/{id}`

История показывает тип синхронизации, статус, время, количество полученных/созданных/обновлённых/ошибочных строк и ошибки.

## Ограничения

- адреса, логины, ключи и пароли не хардкодятся;
- интервальная нагрузка, фактические статусы и KPI требуют дополнительного источника или подтверждённого endpoint.
- endpoint списка всех проектов не подтверждён, поэтому используется ручное добавление проекта по UUID;
- sync сохраняет только read-only данные, write-запросы в Naumen не выполняются.
