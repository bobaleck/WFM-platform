# Stage 6 report

Дата: 2026-05-26.

## 1. Что реализовано

Выполнен аудит open-source основы проекта, добавлены документы `open-source-audit.md`, `dependency-inventory.md`, `production-checklist.md`, подготовлена Alembic-структура с baseline migration, добавлены backup/restore и monitoring scripts, обновлена эксплуатационная документация, добавлены frontend-страницы «О системе» и «Документация», расширены backend-тесты.

## 2. Результат open-source audit

Готовое open-source WFM/HRM-решение в проект не встроено. Локально не обнаружены Frappe HR, ERPNext HR, OrangeHRM, Open HRMS/Odoo, TimeTrex, Staffjoy или Timefold.

Используются open-source компоненты: Python, FastAPI, SQLAlchemy, Pydantic, PostgreSQL, Redis, React, Vite, TypeScript, Docker Compose, Nginx и вспомогательные backend/frontend зависимости.

Custom-части: WFM-модели, API, расчёт потребности, генерация графиков, покрытие, интерфейс, отчёты, план/факт, авторизация внутри приложения, роли и audit log.

## 3. Вывод

Проект является кастомной WFM-платформой на open-source технологическом стеке. Интеграция с готовым open-source WFM/HRM сейчас не требуется; Timefold можно рассмотреть позже как отдельный оптимизационный движок.

## 4. Созданные документы

- `docs/open-source-audit.md`
- `docs/dependency-inventory.md`
- `docs/production-checklist.md`
- `docs/stage6-report.md`

## 5. Alembic

Добавлены `backend/alembic.ini`, `backend/alembic/env.py`, `backend/alembic/versions/20260526_0001_baseline.py`. Baseline migration использует текущую SQLAlchemy metadata и `checkfirst=True`, чтобы не пересоздавать существующие таблицы. Для существующей БД выбран подход stamp head: создаётся `alembic_version` со значением `20260526_0001`, без `drop_all`, без пересоздания БД и без удаления volumes.

Из-за запрета внешних сетевых запросов новый пакет Alembic не устанавливался из внешнего индекса. Структура миграций подготовлена; для production нужно закрепить установку Alembic из утверждённого локального/внутреннего источника либо разрешённого dependency pipeline.

## 6. Backup/restore

Добавлены:

- `scripts/backup-db.sh`
- `scripts/restore-db.sh`
- `scripts/backup-files.sh`

`backup-db.sh` создаёт `pg_dump` в `backups/db` и чистит старые dump старше 14 дней, если `BACKUP_RETENTION_DAYS` не задан. `restore-db.sh` требует `--confirm` и не работает случайно. `backup-files.sh` архивирует важные файлы проекта без `.env`, `node_modules`, `__pycache__` и `backups`.

## 7. Monitoring

Добавлены:

- `scripts/status.sh`
- `scripts/healthcheck.sh`
- `scripts/disk-usage.sh`
- `scripts/db-size.sh`

Скрипты проверяют сервисы Docker Compose, health endpoints, диск, backups, размер БД и основные таблицы.

## 8. Frontend

Добавлена страница «О системе» с версией, окружением, статусами backend/scheduler/БД, списком модулей, open-source основой и честной формулировкой: «Система реализована как кастомный WFM-layer на open-source технологическом стеке».

Добавлена страница «Документация» с краткими инструкциями по нагрузке, потребности, графикам, публикации, факту, план/факт и CSV export.

## 9. Выполненные проверки

Проверялись `docker compose ps`, `/health`, `/api/v1/version`, `/scheduler/health`, frontend HTTP 200, авторизация admin, доступ к защищённым API с token и 401 без token, baseline stamp `20260526_0001`, создание DB/files backup, отказ restore без `--confirm`, monitoring scripts, backend tests и frontend build.

## 10. Тесты

Backend tests: `24 passed, 1 skipped`. Skipped test относится к запуску `healthcheck.sh` внутри backend-контейнера, где нет Docker CLI; сам `scripts/healthcheck.sh` был отдельно запущен на host и вернул OK по backend, frontend, scheduler, PostgreSQL и Redis. Frontend build выполнен успешно: `npm run build`.

## 11. Ограничения

Alembic dependency не установлен из внешнего индекса из-за ограничения этапа на сетевые запросы. Frontend не имеет lock-файла, а `package.json` использует `latest`. TLS, SSO, промышленная ротация логов и проверка restore на отдельной БД остаются вне рамок этапа.

## 12. Что не делалось

Не выполнялись внешние интеграции, реальные подключения к сторонним системам, установка тяжёлых HRM/WFM-систем, настройка TLS, SSO и промышленного оптимизатора.

## 13. Этап 7

На Этапе 7: улучшение UX, промышленная подготовка отчётов, расширение планировщика, подготовка адаптера внешнего источника данных как отключённого модуля, принятие решения по Timefold как open-source оптимизационному движку.
