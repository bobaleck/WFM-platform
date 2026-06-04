# Проекты Naumen в WFM

На Этапе 8 проекты Naumen стали отдельной сущностью WFM.

## Почему проект добавляется по UUID

В локальном PDF Naumen REST API не подтверждён read-only endpoint списка всех проектов.
Поэтому WFM не пытается получать общий список проектов автоматически.
Администратор вручную вводит UUID проекта, а backend проверяет его через подтверждённый endpoint:

```text
GET /api/v2/projects/{uuid}
GET /api/current/projects/{uuid}
```

Версия выбирается настройкой интеграции `api_version`: `v2` или `current`.

## Локальная модель

Таблица `naumen_projects` хранит:

- `project_uuid`;
- `title`;
- `partner_uuid`;
- `state`;
- `data_channel`;
- `cluster_id`;
- `is_active`;
- `is_default`;
- `last_checked_at`;
- `last_sync_at`.

Проект можно сделать default. Если пользователь не выбрал активный проект, backend возвращает default-проект, затем первый доступный проект, иначе `null`.

## API WFM

- `GET /api/v1/projects` — список доступных проектов.
- `POST /api/v1/projects/check` — проверка UUID через Naumen.
- `POST /api/v1/projects` — сохранение проекта.
- `GET /api/v1/projects/current` — активный проект пользователя.
- `PUT /api/v1/projects/current` — выбор активного проекта.
- `PUT /api/v1/projects/{id}` — изменение локальных свойств.
- `DELETE /api/v1/projects/{id}` — soft delete через `is_active=false`.

Управление проектами требует `settings:manage`.
Чтение списка и текущего проекта доступно авторизованному пользователю с базовым доступом к dashboard.

## Ограничения

- WFM не выполняет write-запросы в Naumen.
- `PUT /projects/{uuid}/state` не используется.
- Список проектов не загружается автоматически.
- Интервальная нагрузка, SLA/AHT и отсутствия не подтягиваются из проекта, потому что соответствующие endpoints не подтверждены в PDF.
