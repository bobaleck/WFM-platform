# Этап 7.2 — корректировка UI, очистка demo data и подготовка Naumen-интеграции

Дата: 2026-05-27.

## 1. Что сделано по UI

- Левое меню выровнено по левому краю.
- Для `nav-item` добавлено явное `justify-content: flex-start`, фиксированная ширина иконки и левое выравнивание текста.
- Пустые состояния унифицированы: “Данные пока не загружены. Загрузите данные через интеграцию или CSV-импорт.”
- Раздел «Интеграция» переработан из информационной заглушки в страницу настроек Naumen.

Изменённые frontend-файлы:

- `frontend/src/styles/main.css`
- `frontend/src/components/DataTable.tsx`
- `frontend/src/components/EmptyState.tsx`
- `frontend/src/api/integration.ts`
- `frontend/src/pages/Integration.tsx`

## 2. Что исправлено в левом меню

Пункты меню больше не наследуют центрирование от базового стиля `button`. Иконка и текст начинаются с одной линии, активный пункт остаётся спокойным enterprise-элементом без жирного текста и тяжёлой рамки.

## 3. Как изучался PDF

PDF: `/home/alex/ncc_rest_api_ru.pdf`.

Файл только читался. Внешние источники и сетевые запросы не использовались. На сервере не было `pdfinfo`, `pdftotext` и готовых Python PDF-библиотек, поэтому текст извлечён локальным Python-экстрактором потоков PDF.

Результат:

- файл PDF: 2.9 MB;
- извлечённый текст: `/opt/wfm-naumen/docs/naumen-api-extracted.txt`;
- извлечено примерно 763 текстовых блока/страницы;
- объём текста: около 683 тыс. символов;
- URL, JSON и curl-примеры читаются;
- часть русскоязычных описаний повреждена кодировкой PDF.

## 4. Найденные релевантные разделы Naumen API

Подтверждены:

- форматы URL `/api/current`, `/api/v2`, `/fx/api/v1/<format>`;
- `Content-Type: application/json`;
- Basic auth;
- API key auth через `Username` и `X-API-Key`;
- ошибки `401`, `403`, `404`, `409`, `423`;
- сотрудники `/api/v2/employees`;
- сотрудник `/api/v2/employees/{login}`;
- callcases v1;
- project cases/cases-batch v2.

## 5. Реализованные endpoints WFM для Naumen

- `GET /api/v1/integrations/naumen/settings`
- `PUT /api/v1/integrations/naumen/settings`
- `POST /api/v1/integrations/naumen/check`
- `POST /api/v1/integrations/naumen/sync/employees`
- `POST /api/v1/integrations/naumen/sync/departments`
- `POST /api/v1/integrations/naumen/sync/project-agents`
- `POST /api/v1/integrations/naumen/sync/project-schedule`
- `GET /api/v1/integrations/naumen/sync-runs`
- `GET /api/v1/integrations/naumen/sync-runs/{id}`

Реальные внешние запросы на этапе 7.2 не выполняются. Dry run создаёт запись sync run и возвращает `not_configured` или `pending`.

## 6. Pending endpoints

Не удалось надёжно подтвердить по извлечённому PDF:

- отделы/OU отдельным endpoint;
- операторы проекта;
- расписание проекта;
- аудиозаписи;
- интервальная нагрузка;
- фактические статусы операторов;
- KPI SLA/AHT/ASA/occupancy/utilization/abandonment.

Эти направления описаны в `docs/naumen-api-analysis.md` и `docs/naumen-integration-map.md`.

## 7. Demo data удалены

Перед очисткой выполнены backup:

- `/opt/wfm-naumen/backups/db/wfm_naumen_20260527T071002Z.sql`
- `/opt/wfm-naumen/backups/db/wfm_naumen_20260527T071843Z.sql`

Добавлен и выполнен скрипт:

- `scripts/clear-demo-data.sh --confirm`

Скрипт не запускается без `--confirm`, не удаляет структуру БД, не трогает roles, permissions, role_permissions, admin, настройки, migrations, production/backups/docs/scripts.

## 8. Таблицы до/после

Контрольные значения до первой очистки:

| Таблица | До |
|---|---:|
| users | 3 |
| roles | 5 |
| permissions | 32 |
| employees | 10 |
| teams | 7 |
| skills | 6 |
| queues | 5 |
| workload_intervals | 259 |
| staffing_requirements | 259 |
| shifts | 8 |
| schedule_assignments | 17 |
| schedule_coverage | 4 |

После финальной очистки и отключения `DEMO_SEED`:

| Таблица | После |
|---|---:|
| users | 1 |
| roles | 5 |
| permissions | 32 |
| employees | 0 |
| teams | 0 |
| skills | 0 |
| queues | 0 |
| workload_intervals | 0 |
| staffing_requirements | 0 |
| shifts | 0 |
| schedule_assignments | 0 |
| schedule_coverage | 0 |

`DEMO_SEED=false` установлен в `.env` и `.env.example`, чтобы demo data не создавались повторно при старте backend.

## 9. Admin сохранён

Проверено через login и API: пользователь `admin` активен, вход работает, защищённые API с token работают. Все demo users удалены.

## 10. Как работает страница «Интеграция»

Страница показывает:

- статус enabled/disabled;
- последний результат проверки;
- base URL;
- auth mode `api_key`/`basic`;
- username;
- API key и Basic password с placeholder “Оставьте пустым, чтобы не менять”;
- masked secret, если он сохранён;
- timeout;
- verify SSL;
- project_uuid;
- кнопки check, dry run и sync;
- историю `naumen_sync_runs`.

Секреты не сохраняются в localStorage и не логируются frontend-кодом.

## 11. Как хранятся секретные параметры

Поля `api_key_encrypted` и `basic_password_encrypted` хранятся в `naumen_connection_settings` в зашифрованном виде через существующий `INTEGRATION_SECRET_KEY`. API возвращает только `api_key_masked` и `basic_password_masked`.

Если secret-поле в `PUT settings` пустое, старое значение не затирается.

## 12. Проверки выполнены

- `docker compose up -d --build`
- `docker compose ps`
- `curl -sS http://127.0.0.1/health`
- `curl -sS http://127.0.0.1/api/v1/version`
- `curl -I http://127.0.0.1/`
- protected Naumen settings без token возвращает `401`
- login admin работает
- business tables пустые
- roles/permissions сохранены
- новые таблицы Naumen созданы
- `GET settings` работает
- `check` при неполных настройках возвращает `not_configured`
- `sync/employees` dry run возвращает `not_configured`/`pending` и не создаёт сотрудников

## 13. Тесты

- Backend: `44 passed, 1 skipped`
- Frontend build внутри контейнера: успешно

Host-команда `npm --prefix frontend run build` ранее недоступна из-за отсутствия локального `node_modules`; каноническая проверка выполнена внутри Docker-контейнера frontend без внешних установок.

## 14. Ограничения

- Реальное подключение к Naumen не выполнялось.
- Безопасный read-only endpoint для production check не включён.
- Интервальная нагрузка, фактические статусы и KPI требуют дополнительного подтверждённого источника.
- Визуальная проверка выполнялась через локальные HTTP/build/API-проверки; браузерный Playwright в задаче не использовался.
- TLS, SSO и production cron не настраивались.

## 15. Что делать следующим этапом

- Получить тестовый контур Naumen и отдельные тестовые credentials.
- Подтвердить endpoints для интервальной статистики, KPI и статусов операторов.
- Включить read-only connection check.
- Реализовать безопасный dry run с реальным чтением тестового endpoint.
- Подготовить маппинг departments/project agents после подтверждения endpoints.
- Подготовить UAT сценарии пустого состояния и первого импорта.
