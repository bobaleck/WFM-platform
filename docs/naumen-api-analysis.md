# Анализ локального PDF Naumen REST API

Источник: `/home/alex/ncc_rest_api_ru.pdf`.

Файл изучался локально. Внешние сайты, документация и сетевые запросы не использовались. Текст был извлечён в `/opt/wfm-naumen/docs/naumen-api-extracted.txt`. Извлечено примерно 763 текстовых блока/страницы и около 683 тыс. символов. Важные URL, JSON-примеры и curl-команды читаются, но значительная часть русскоязычных описаний повреждена из-за кодировки PDF, поэтому неподтверждённые endpoints помечены как `pending`.

## A. Общие принципы API

В PDF найдены форматы URL:

| Версия | Формат |
|---|---|
| current | `<protocol>://<host>:<port>/api/current/<endpoint>?<query_params>` |
| v2 | `<protocol>://<host>:<port>/api/v2/<endpoint>?<query_params>` |
| v1 | `<protocol>://<host>:<port>/fx/api/v1/<format>/<endpoint>?<query_params>` |

`Content-Type` в примерах: `application/json`, `application/xml`, `application/x-www-form-urlencoded`. Для текущей WFM-интеграции выбран JSON.

Типовые коды из текста и примеров: `200 OK`, `201 Created`, `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`, `409 Conflict`, `423 Locked`.

## B. Авторизация

В документе найдены два режима:

| Режим | Заголовки/пример | Комментарий |
|---|---|---|
| Basic | `--user wsrest:123` | Логин и пароль передаются стандартным Basic Auth. |
| API key | `Username: wsrest`, `X-API-Key: ...` | Для WFM реализован как предпочтительный режим. |

Также найден служебный заголовок `X-NCC-RUN-AS-USER` для выполнения операции от имени пользователя. В WFM на этапе 7.2 он не используется.

Ошибки авторизации: `401 Unauthorized`; при недостатке прав в API встречается `403 Forbidden`.

## Обновление Этапа 8

## Обновление Этапа 8.3: partners

Пользователь вручную подтвердил рабочий read-only запрос:

- `GET https://telesales-service.nau.team:8443/api/v2/partners/`
- заголовки `Content-Type: application/json`, `Username`, `X-API-Key`
- ответ содержит `response.items[]` с полями `uuid` и `title`.

Из этого следует, что `base_url` должен храниться как корневой адрес `https://telesales-service.nau.team:8443`, а backend сам добавляет `/api/v2` или `/api/current`.

`GET /partners/` теперь является базовой проверкой подключения и источником таблицы `naumen_partners`. Проверка через dummy `/projects/11111111111111111111111111111111` больше не используется. Endpoint списка проектов остаётся неподтверждённым; проекты и партнёры не смешиваются. В UI для пользовательского выбора используется термин «контур».

Для новой интеграции WFM используется только `v2` или `current`.
`v1` считается устаревшим и не используется в новом коде интеграции.

Правила, зафиксированные в backend client:

- `base_url` хранится как корневой адрес Naumen, без `/api/v2`;
- итоговый URL строится как `base_url + /api/v2 + endpoint` или `base_url + /api/current + endpoint`;
- для `v2/current` используется `Content-Type: application/json`;
- API key mode использует заголовки `Username` и `X-API-Key`;
- Basic mode использует стандартный HTTP Basic;
- все операции этапа read-only, write endpoints Naumen не вызываются.

Подтверждённые для реализации read-only endpoints:

| Method | Path | Назначение | Статус WFM |
|---|---|---|---|
| `GET` | `/projects/{uuid}` | Проверка и чтение проекта по UUID | `implemented` |
| `GET` | `/employees?removed=false` | Список сотрудников | `implemented` |
| `GET` | `/ous/root/subous` | Дочерние отделы/OU | `implemented` |
| `GET` | `/projects/{projectUuid}/agents` | Операторы проекта | `implemented`, возможен `501` при расширенном режиме назначения |
| `GET` | `/projects/{projectUuid}/agents/available` | Подходящие операторы проекта | `implemented` для диагностики |
| `GET` | `/projects/{projectUuid}/schedule` | Справочное расписание проекта | `implemented` |
| `GET` | `/partners/` | Список партнёров Naumen, подтверждён вручную | `implemented`, используется для check/sync partners |

Endpoint списка всех проектов в PDF не подтверждён. Поэтому WFM не использует dummy-проекты как проверку подключения; проекты добавляются вручную по UUID только после уточнения.

## C. Разделы API, важные для WFM

| Раздел | Статус по PDF | Значение для WFM |
|---|---|---|
| Сотрудники | подтверждён | Синхронизация справочника операторов, ролей/skills как metadata. |
| Отделы/OU | подтверждён `GET /ous/root/subous` | Маппинг в команды WFM. |
| Навыки/квалификации | найдены в ответе сотрудника как `skills` | Можно использовать для `skills` и `employee_skills`. |
| Projects/callcases | подтверждены | Полезно для обращений/кейсов, но не заменяет интервальную нагрузку. |
| Project agents | подтверждён `GET /projects/{projectUuid}/agents` | Состав операторов проекта; при расширенном режиме Naumen может вернуть `501`. |
| Project schedule | подтверждён `GET /projects/{projectUuid}/schedule` | Справочное расписание проекта, не индивидуальные WFM-графики. |
| Аудиозаписи вызовов | отдельный endpoint в извлечённом тексте не подтверждён | Pending. |
| Роли и права | встречаются как поля сотрудника `roles` | Для WFM не синхронизируются как системные RBAC. |

## D. Endpoint-карта

| Method | Path | Parameters | Body | Response summary | Required permissions | WFM модуль | Статус |
|---|---|---|---|---|---|---|---|
| `GET` | `/api/v2/employees` | возможны query params по документации, точный список требует сверки | нет | список сотрудников, поля `uuid`, `login`, ФИО, email, телефоны, `department`, `roles`, `skills` | пользователь REST с правом чтения сотрудников | `employees`, `skills`, `employee_skills`, `teams` | `implement_now` |
| `GET` | `/api/v2/ous/root/subous` | нет | нет | список дочерних OU/отделов | право чтения OU | `teams` | `implement_now` |
| `GET` | `/api/v2/partners/` | нет | нет | `items[]` с `uuid`, `title` | право чтения партнёров | `naumen_partners`, connection check, контур | `implement_now` |
| `GET` | `/api/v2/projects/{uuid}` | `uuid` | нет | проект: `title`, `partner`, `state`, `dataChannel`, `clusterId` | право чтения проекта | `naumen_projects`, project selector | `implement_now` |
| `GET` | `/api/v2/projects/{projectUuid}/agents` | `projectUuid` | нет | операторы проекта, квалификация, состояние | право чтения проекта | `employees`, `external_mappings`, project context | `implement_now` |
| `GET` | `/api/v2/projects/{projectUuid}/agents/available` | `projectUuid` | нет | подходящие операторы проекта | право чтения проекта | диагностика интеграции | `later` |
| `GET` | `/api/v2/projects/{projectUuid}/schedule` | `projectUuid` | нет | правила расписания проекта: `restDay`, `timeFrom`, `timeTo`, `parameters`, `ruleType` | право чтения проекта | `naumen_project_schedule_rules` | `implement_now` |
| `GET` | `/api/v2/employees/{login}` | `login` | нет | карточка сотрудника с `skills`, `roles`, `department` | право чтения сотрудника | детализация сотрудника | `implement_now` |
| `POST` | `/api/v2/employees?genPass=true` | `genPass` | JSON сотрудника | создание сотрудника | право изменения сотрудников | не требуется для WFM | `not_needed` |
| `GET` | `/fx/api/v1/json/callcases/?project=<project>&state=<state>` | `project`, `state`, `operator`, `modifiedAfter`, `modifiedBefore`, `page`, `filterAttributes` | нет | список обращений/callcases | право чтения callcases | отчёты по обращениям, не интервальная нагрузка | `later` |
| `GET` | `/fx/api/v1/json/callcases/{case_uuid}` | `case_uuid` | нет | карточка обращения | право чтения callcase | отчёты/ссылки на обращения | `later` |
| `GET` | `/fx/api/v1/json/callcases/{case_uuid}/get-state` | `case_uuid` | нет | состояние обращения | право чтения/операции callcase | факт статусов не заменяет интервальный факт операторов | `later` |
| `POST` | `/fx/api/v1/json/callcases/{case_uuid}/set-state` | `case_uuid`, `state`, `operator`, `date` | form-urlencoded | изменение состояния | право изменения callcase | WFM не должен менять обращения | `not_needed` |
| `GET` | `/api/v2/projects/{project}/cases/{id}` | `project`, `id` | нет | обращение проекта | право чтения проекта/case | отчётные ссылки | `later` |
| `POST` | `/api/v2/projects/{project}/cases-batch/list` | `project` | фильтр/список | пакетный список обращений | право чтения проекта | отчёты по обращениям | `later` |
| `POST` | `/api/v2/projects/{project}/cases-batch/count` | `project` | фильтр | количество обращений | право чтения проекта | агрегаты | `later` |
| `GET/POST` | project agents | `project_uuid` | не подтверждено | не подтверждено | требует уточнения | очереди/операторы проекта | `pending` |
| `GET` | project schedule | `project_uuid` | не подтверждено | не подтверждено | требует уточнения | смены/справочная информация | `pending` |
| `GET` | call recording | `call_uuid` | не подтверждено | возможно audio/reference | требует уточнения | отчёты/recording links | `pending` |

## E. Что не найдено или не подтверждено

В доступном извлечённом тексте не удалось надёжно подтвердить прямые endpoints для:

- интервальной статистики нагрузки по очередям;
- фактических статусов операторов по интервалам;
- KPI contact center уровня SLA/AHT/ASA/occupancy/utilization/abandonment;
- расписания проекта в формате индивидуальных смен операторов, пригодном для прямого создания WFM `schedule_assignments`;
- скачивания или получения ссылки на аудиозапись вызова.

Альтернативы:

- CSV-импорт интервальной нагрузки и факта;
- отдельная выгрузка отчётов из Naumen;
- получение дополнительной актуальной документации Naumen;
- ручная настройка маппинга и тестового контура перед включением реальных запросов.
