# Stage 1 report: WFM Naumen bootstrap

Дата выполнения: 2026-05-25.

## 1. Предварительная проверка

Выполненные команды:

```bash
whoami
id
ls -la /opt
ls -la /opt/wfm-naumen
docker --version
docker compose version
df -hT / /opt
ss -ltnp | grep -E ':(8000|5173|5432|6379)\b' || true
```

Результат:

- Пользователь: `root`.
- `/opt` существует.
- `/opt/wfm-naumen` до начала этапа не существовал.
- Docker: `Docker version 28.1.1`.
- Docker Compose: `v2.35.1`.
- Свободное место: `/` и `/opt` на ext4, размер около `97G`, свободно около `76G`.
- Порты `8000`, `5173`, `5432`, `6379` до запуска проекта не были заняты.

## 2. Что создано

Создан базовый production-oriented skeleton проекта в:

```text
/opt/wfm-naumen
```

Компоненты:

- backend API: Python FastAPI;
- frontend cabinet: React + Vite + TypeScript;
- PostgreSQL 16;
- Redis 7;
- scheduler service placeholder;
- future Naumen adapter placeholder;
- Docker Compose;
- nginx example config;
- scripts для проверки, логов и рестарта;
- документация.

## 3. Созданные файлы

Ключевые файлы:

```text
.env
.env.example
README.md
docker-compose.yml
backend/Dockerfile
backend/requirements.txt
backend/app/main.py
backend/app/core/config.py
backend/app/db/session.py
backend/app/integrations/naumen/client.py
backend/app/wfm/README.md
frontend/Dockerfile
frontend/package.json
frontend/index.html
frontend/vite.config.ts
frontend/tsconfig.json
frontend/src/main.tsx
frontend/src/api/health.ts
frontend/src/components/StatusCard.tsx
frontend/src/layouts/AppLayout.tsx
frontend/src/pages/Dashboard.tsx
frontend/src/pages/Employees.tsx
frontend/src/pages/Workload.tsx
frontend/src/pages/Schedules.tsx
frontend/src/pages/Reports.tsx
frontend/src/pages/Settings.tsx
frontend/src/routes/App.tsx
frontend/src/styles/main.css
scheduler/Dockerfile
scheduler/requirements.txt
scheduler/app/main.py
scheduler/README.md
infra/nginx/wfm-naumen.conf.example
docs/architecture.md
docs/wfm-mvp-scope.md
docs/naumen-integration-contract.md
docs/database-model.md
docs/deployment-plan.md
docs/operations.md
docs/stage1-report.md
scripts/check.sh
scripts/logs.sh
scripts/restart.sh
```

Также созданы каталоги:

```text
data/imports
data/exports
tests
```

## 4. Env

Созданы:

- `/opt/wfm-naumen/.env.example`
- `/opt/wfm-naumen/.env`

В `.env` сгенерированы безопасные значения:

- `POSTGRES_PASSWORD`
- `JWT_SECRET`

Права на `.env`:

```text
chmod 600 /opt/wfm-naumen/.env
```

## 5. Docker Compose

Запуск:

```bash
cd /opt/wfm-naumen
docker compose up -d --build
```

Сервисы:

```text
wfm-naumen-postgres    postgres:16-alpine     healthy
wfm-naumen-redis       redis:7-alpine         healthy
wfm-naumen-backend     wfm-naumen-backend     healthy, 127.0.0.1:8000->8000
wfm-naumen-frontend    wfm-naumen-frontend    running, 127.0.0.1:5173->5173
wfm-naumen-scheduler   wfm-naumen-scheduler   healthy, 127.0.0.1:8010->8010
```

PostgreSQL и Redis наружу не опубликованы, доступны только во внутренней Docker-сети.

Сеть:

```text
wfm-naumen_wfm_internal
```

Volumes:

```text
wfm-naumen_wfm_postgres_data
wfm-naumen_wfm_redis_data
```

## 6. Healthchecks

Выполненные команды:

```bash
docker compose ps
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8000/api/v1/version
curl -s http://127.0.0.1:8000/api/v1/modules
curl -s http://127.0.0.1:8010/health
curl -s http://127.0.0.1:8010/api/v1/scheduler/status
curl -s -X POST http://127.0.0.1:8010/api/v1/scheduler/draft-schedule
curl -I http://127.0.0.1:5173
./scripts/check.sh
```

Результаты:

```json
{"status":"ok","service":"backend"}
```

```json
{"app":"wfm-naumen","version":"0.1.0","naumen_integration":"planned"}
```

```json
{"modules":["employees","teams","skills","queues","workload","staffing_requirements","schedules","absences","kpi_reports","naumen_adapter"]}
```

```json
{"status":"ok","service":"scheduler"}
```

```json
{"status":"idle","optimizer":"planned","service":"scheduler"}
```

```json
{"status":"not_implemented","message":"Оптимизатор расписаний будет подключён на следующих этапах"}
```

Frontend:

```text
HTTP/1.1 200 OK
```

## 7. Используемые порты

- Backend API: `127.0.0.1:8000`.
- Frontend Vite: `127.0.0.1:5173`.
- Scheduler API: `127.0.0.1:8010`.
- PostgreSQL: внутренний Docker port `5432`, наружу не опубликован.
- Redis: внутренний Docker port `6379`, наружу не опубликован.

Firewall, SSH и системные сетевые правила не менялись.

## 8. Что не было сделано на этом этапе

- Не подключался Naumen API.
- Не подключался Frappe HR.
- Не подключался Timefold.
- Не создавалась полноценная схема БД и миграции.
- Не реализовывались CRUD API.
- Не реализовывались алгоритмы расчёта графиков.
- Не настраивался production reverse proxy как обязательный сервис.
- Не настраивались TLS, backups, monitoring и внешняя авторизация.

## 9. Что нужно сделать на Этапе 2

- Выбрать миграционный инструмент, например Alembic.
- Создать SQLAlchemy/SQLModel модели.
- Реализовать таблицы из `docs/database-model.md`.
- Добавить seed-данные для ролей и тестовых справочников.
- Реализовать базовые CRUD API для сотрудников, команд, навыков и очередей.
- Добавить backend tests.
- Подготовить CSV/manual import contract.
- Уточнить роли доступа и модель пользователей.

## 10. Подтверждение защищённых компонентов

Проверено после запуска WFM:

```text
ssh.service active (running)
mihomo.service active (running)
codex processes active
/root/.codex exists
```

Не трогались:

- SSH/sshd;
- firewall/security rules;
- `mihomo.service`;
- `/etc/mihomo`;
- `/usr/local/bin/mihomo`;
- `codex`;
- `/root/.codex`.

## 11. Итог

Проект создан и запущен. Backend, scheduler, PostgreSQL и Redis имеют успешные healthchecks. Frontend доступен локально на `127.0.0.1:5173`. Skeleton готов к Этапу 2.
