# Dependency inventory

Дата: 2026-05-26.

Инвентаризация выполнена по локальным файлам и установленным пакетам внутри текущих контейнеров. Лицензии не проверялись через интернет; если metadata локально не содержит лицензию, указано "требует дополнительной проверки".

## Backend

`backend/requirements.txt`:

| Название | Версия | Назначение | Лицензия | Комментарий |
|---|---:|---|---|---|
| fastapi | 0.115.6 | HTTP API framework | требует дополнительной проверки | Используется backend API |
| uvicorn | 0.34.0 | ASGI server | BSD-3-Clause | Запуск backend |
| psycopg / psycopg-binary | 3.2.3 | PostgreSQL driver | LGPLv3 | Доступ к PostgreSQL |
| redis | 5.2.1 | Redis client | MIT | Подготовка к cache/job scenarios |
| sqlalchemy | 2.0.36 | ORM | MIT | Модели и SQL |
| cryptography | 44.0.0 | Crypto primitives | Apache-2.0 OR BSD-3-Clause | Шифрование integration settings |
| python-multipart | 0.0.20 | Multipart upload | Apache-2.0 | CSV upload |
| pytest | 8.3.4 | Tests | MIT | Backend tests |

Дополнительно установлены зависимости FastAPI/uvicorn/pytest: `pydantic 2.13.4`, `starlette 0.41.3`, `anyio`, `click`, `h11`, `uvloop`, `watchfiles`, `websockets`, `PyYAML`, `typing_extensions` и другие транзитивные пакеты.

## Frontend

`frontend/package.json` использует `latest`, но локально в контейнере установлены:

| Название | Версия | Назначение | Лицензия | Комментарий |
|---|---:|---|---|---|
| react | 19.2.6 | UI library | MIT | Основной UI |
| react-dom | 19.2.6 | DOM renderer | MIT | Рендеринг UI |
| vite | 8.0.14 | Dev/build tool | MIT | Frontend build/dev server |
| typescript | 6.0.3 | Type checking | Apache-2.0 | Типизация |
| @vitejs/plugin-react | 6.0.2 | React plugin for Vite | требует дополнительной проверки | Build plugin |
| lucide-react | 1.16.0 | Icons | ISC | Иконки UI |
| @types/react | 19.2.15 | Type definitions | MIT | Dev types |
| @types/react-dom | 19.2.3 | Type definitions | MIT | Dev types |

Lock-файл в локальном проекте отсутствует. Для production рекомендуется добавить lock-файл и закрепить версии вместо `latest`.

## Docker images

| Image | Версия/tag | Назначение | Лицензия | Комментарий |
|---|---|---|---|---|
| postgres | 16-alpine | PostgreSQL | требует дополнительной проверки | Используется сервисом `postgres` |
| redis | 7-alpine | Redis | требует дополнительной проверки | Используется сервисом `redis` |
| python | 3.12-slim | Base image backend/scheduler | требует дополнительной проверки | Через Dockerfile |
| node | 22-alpine | Base image frontend | требует дополнительной проверки | Через Dockerfile |
| wfm-naumen-backend | latest | Собранный backend | custom | Локальный image |
| wfm-naumen-frontend | latest | Собранный frontend | custom | Локальный image |
| wfm-naumen-scheduler | latest | Собранный scheduler | custom | Локальный image |

## Комментарии

Лицензии требуют отдельной юридической проверки перед production. На текущем этапе не выявлено локально встроенного коробочного open-source WFM/HRM-приложения.
