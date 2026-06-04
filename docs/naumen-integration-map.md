# Карта интеграции Naumen -> WFM

Интеграция подготовлена по локальному PDF `/home/alex/ncc_rest_api_ru.pdf`.
На Этапе 8 backend-клиент переведён на read-only endpoints `v2/current`.
Write-запросы в Naumen не выполняются.

## Партнёры Naumen

На этапе 8.3 вручную подтверждён endpoint `GET /api/v2/partners/`.

| Naumen field | WFM table.field | Правило |
|---|---|---|
| `uuid` | `naumen_partners.partner_uuid` | Уникальный внешний идентификатор партнёра. |
| `title` | `naumen_partners.title` | Название партнёра хранится как UTF-8. |
| наличие в ответе | `naumen_partners.is_active` | При загрузке партнёр активируется. |
| время загрузки | `naumen_partners.last_sync_at` | Заполняется при `dry_run=false`. |

Партнёр не называется проектом в backend-модели. Если в бизнес-терминах партнёр позже станет рабочим проектом/контуром, маппинг должен выполняться явно. В UI для выбора области данных используется термин «контур».

## Сотрудники

| Naumen field | WFM table.field | Правило |
|---|---|---|
| `uuid` | `external_mappings.external_id` | Источник `naumen`, entity `employee`. |
| `login` | `employees.personnel_number` | Использовать как стабильный локальный табельный идентификатор, если нет отдельного номера. |
| активный проект | `employees.project_id` | Заполняется при sync в контексте проекта. |
| `title` или ФИО | `employees.full_name` | Собирать из `lastName`, `firstName`, `middleName`, если `title` нет. |
| `email` | `employees.email` | Опционально. |
| `internalPhoneNumber`, `mobilePhoneNumber`, `workPhoneNumber` | `employees.phone` | Приоритет: internal, work, mobile. |
| `department`/`ou` | `employees.team_id` через `teams` | Требует маппинга отдела в команду. |
| `removed` | `employees.is_active` | `removed=true` -> inactive. |

## Отделы

| Naumen source | WFM table.field | Статус |
|---|---|---|
| `GET /ous/root/subous`, `uuid` | `external_mappings.external_id` для `team` | `implemented`. |
| `title` | `teams.name` | `implemented`. |
| `head`, `supervisors`, `responsibleEmployees` | `teams.supervisor_name` или metadata | частично, зависит от ответа Naumen. |

## Навыки/квалификации

| Naumen field | WFM table.field | Правило |
|---|---|---|
| `skills[].code` | `external_mappings.external_id` | Источник `naumen`, entity `skill`. |
| `skills[].title` | `skills.name` | Создавать/обновлять справочник навыков. |
| `skills[].level` | `employee_skills.level` | Уровень навыка сотрудника. |
| `skills[].minLevel`, `maxLevel` | справочная metadata | На этапе 7.2 не сохраняется отдельно. |

## Операторы проекта

| Naumen source | WFM mapping | Статус |
|---|---|---|
| `GET /projects/{projectUuid}/agents` | `employees`, `external_mappings`, `employees.project_id` | `implemented`; если Naumen использует расширенный режим назначения операторов, возможен `501`. |
| `projectQualification`, `state`, `substate` | metadata сотрудника/маппинга | `later`: хранение расширенной metadata требует отдельного поля. |

## Расписание проекта

| Naumen source | WFM mapping | Статус |
|---|---|---|
| `GET /projects/{projectUuid}/schedule` | `naumen_project_schedule_rules` | `implemented` как справочное расписание проекта. |
| индивидуальные смены операторов | `schedule_assignments` | `pending`: PDF не подтверждает read-only endpoint индивидуального графика операторов. |

## Аудиозаписи

| Naumen source | WFM mapping | Статус |
|---|---|---|
| call recording endpoint/reference | `reports`/recording links | `pending`: endpoint не подтверждён; скачивание файлов не реализовано. |

## KPI и интервальная нагрузка

| Данные | WFM table | Статус |
|---|---|---|
| offered/handled/abandoned/AHT/SL по интервалам | `workload_intervals` | `pending`: прямой endpoint не найден; использовать CSV или отдельную выгрузку отчётов. |
| фактические статусы операторов | `actual_work_intervals` | `pending`: endpoint не найден; использовать CSV/отчётную выгрузку. |
| SLA/AHT/ASA/occupancy/utilization/abandonment | `kpi_snapshots` | `pending`: endpoint не найден; использовать CSV/отчётную выгрузку. |

## Что реализовано на Этапе 8

- настройки подключения Naumen через UI;
- выбор версии API `v2/current`;
- безопасное хранение API key/Basic password в зашифрованном виде;
- построение заголовков Basic/API key;
- проекты Naumen как отдельная сущность WFM;
- ручное добавление проекта по UUID;
- проверка проекта через `GET /projects/{uuid}`;
- project selector в sidebar;
- доступ пользователей к проектам;
- авторизованные CSV-выгрузки через frontend fetch.

## Что добавлено на Этапе 8.3

- базовая проверка подключения через `GET /partners/`;
- таблица `naumen_partners`;
- `GET /api/v1/integrations/naumen/partners`;
- `POST /api/v1/integrations/naumen/partners/sync`;
- `POST /api/v1/integrations/naumen/partners/{id}/default`;
- `PUT /api/v1/integrations/naumen/partners/{id}`;
- диагностика `POST /api/v1/integrations/naumen/diagnose` без вывода секретов;
- отключение dummy-проектов `111...` и `222...`.

## Что требует уточнения

- аудиозаписи;
- интервальная статистика, фактические статусы, KPI.

## Что нельзя реализовать только по текущему PDF

- полноценный WFM forecast/fact import напрямую из Naumen без дополнительного источника интервальной статистики;
- автоматическое построение графиков из Naumen project schedule;
- загрузка записей разговоров;
- промышленная синхронизация без тестового контура и прав read-only.
