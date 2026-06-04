# Stage 5 Report

Дата выполнения: 2026-05-26

## 1. Что реализовано

Добавлены авторизация пользователей, RBAC, системные роли и права, страница входа, страница пользователей и ролей, журнал действий, импорт фактической работы из CSV, журнал экспортов и базовые меры application hardening.

Внешние интеграции, внешние запросы, реальные телефонии, SSH, mihomo, codex, firewall и системный доступ не изменялись.

## 2. Таблицы

Добавлены или расширены:

- `users`: `username`, `password_hash`, `role_id`, `is_superuser`, `last_login_at`;
- `roles`;
- `permissions`;
- `role_permissions`;
- `audit_log`: `actor_user_id`, `actor_username`, `details_json`, `ip_address`, `user_agent`;
- `export_log`;
- существующие `import_batches` и `import_errors` используются для `actual_work_csv`.

## 3. Роли и права

Созданы роли `admin`, `supervisor`, `analyst`, `customer`, `readonly`.

Созданы права: `dashboard:view`, `employees:view`, `employees:manage`, `teams:view`, `teams:manage`, `skills:view`, `skills:manage`, `queues:view`, `queues:manage`, `workload:view`, `workload:import`, `staffing:view`, `staffing:calculate`, `shifts:view`, `shifts:manage`, `schedules:view`, `schedules:generate`, `schedules:confirm`, `schedules:publish`, `schedules:manage`, `absences:view`, `absences:manage`, `actual:view`, `actual:import`, `actual:manage`, `reports:view`, `reports:export`, `settings:view`, `settings:manage`, `audit:view`, `users:view`, `users:manage`.

## 4. Auth endpoints

- `POST /api/v1/auth/login`;
- `GET /api/v1/auth/me`;
- `POST /api/v1/auth/logout`;
- `POST /api/v1/auth/change-password`.

Health, version и login публичны. Остальные внутренние API при `AUTH_ENABLED=true` требуют bearer token.

## 5. RBAC

Маршруты закрыты по правам для dashboard, справочников, нагрузки, расчёта потребности, графиков, отсутствий, факта, отчётов, пользователей, настроек и audit log.

Без token backend возвращает `401`, при недостатке прав - `403`.

## 6. Frontend

Добавлены `/login`, хранение bearer token в localStorage для MVP, добавление `Authorization` в API client, обработка 401/403, кнопка выхода, отображение пользователя и роли в шапке, фильтрация меню по правам, страницы «Пользователи и роли» и «Журнал действий».

Для production рекомендован переход на httpOnly cookie.

## 7. Users/Roles

Backend добавил `GET /api/v1/roles`, `GET /api/v1/permissions`, `GET/POST/PUT/DELETE /api/v1/users`. Пароли возвращаются только как факт установки, `password_hash` не отдаётся.

Создан MVP-администратор из `.env`. Для production пароль администратора нужно сменить.

## 8. Audit log

Логируются входы, ошибки входа, смена пароля, импорт нагрузки, импорт факта, расчёты, генерация графиков, публикация, CSV-экспорт и управление пользователями.

Маршрут: `GET /api/v1/audit-log`.

## 9. Импорт факта

Добавлен `POST /api/v1/imports/actual-work-csv`.

Формат:

```csv
date,employee_email,queue_name,interval_start,interval_end,status,actual_minutes
2026-01-15,operator1@telesales.local,Исходящая линия,10:00,10:30,worked,30
```

Повторная загрузка того же сотрудника, очереди, даты и интервала обновляет запись. Ошибки строк сохраняются в `import_errors`.

Пример файла: `data/imports/actual-work-sample.csv`.

## 10. Отчёты

Добавлены и улучшены:

- `GET /api/v1/reports/dashboard-summary`;
- `GET /api/v1/reports/schedule-coverage`;
- `GET /api/v1/reports/staffing-gaps`;
- `GET /api/v1/reports/export-log`;
- CSV-экспорты пишут запись в `export_log` и `audit_log`.

## 11. Security hardening

Включено:

- password hash;
- bearer token;
- RBAC;
- security headers: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`;
- CORS без wildcard;
- лимит CSV upload 10 MB;
- PostgreSQL и Redis не опубликованы наружу;
- `.env` должен храниться с правами `600`;
- секреты и пароли не выводятся в API-ответах.

## 12. Проверки

Проверялись:

- `docker compose ps`;
- `GET /health`;
- `GET /api/v1/version`;
- login admin;
- `GET /api/v1/auth/me`;
- `GET /api/v1/employees` без token возвращает `401`;
- login с неверным паролем возвращает `401`;
- пользователь `readonly` получает `403` на `/api/v1/users`;
- временный проверочный пользователь `stage5-readonly` после проверки деактивирован;
- `GET /api/v1/employees` с token возвращает данные;
- список ролей и пользователей;
- audit log после login;
- импорт `actual-work-sample.csv`;
- plan/fact после импорта;
- CSV export и `export_log`;
- security headers;
- `.env` имеет права `600`;
- PostgreSQL и Redis не опубликованы наружу;
- frontend build;
- backend tests.

## 13. Тесты

Добавлены тесты для расчёта, shrinkage, навыков, RBAC mapping, password hash, token roundtrip, CSV-строк факта и security headers.

Фактический результат: `15 passed`.

## 14. Ограничения MVP

- token хранится в localStorage;
- нет SSO;
- нет TLS;
- нет Alembic migrations;
- нет production backup и мониторинга;
- аудит покрывает ключевые операции, но не все изменения каждой сущности детализированы до diff.

## 15. Что не делалось

- внешние интеграции;
- реальные подключения к сторонним системам;
- TLS;
- production backup;
- SSO;
- httpOnly cookie auth;
- изменение SSH, mihomo, codex, firewall или системного доступа.

## 16. Этап 6

Следующий этап: миграции Alembic, резервное копирование, мониторинг, production deployment и подготовка адаптера внешних данных без реального подключения.
