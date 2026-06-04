# Отчёт Этапа 2

Дата выполнения: 2026-05-25

## 1. Что было до изменений

Проект `/opt/wfm-naumen` уже содержал Docker Compose stack с backend, frontend, scheduler, PostgreSQL и Redis. Nginx открывал web UI через HTTP. Backend и scheduler имели health endpoints, а основные WFM-разделы frontend были skeleton-заглушками.

## 2. Что реализовано

- Добавлена рабочая MVP-модель внутренней WFM-системы.
- Добавлены SQLAlchemy-модели и автоматическое создание таблиц при старте backend.
- Добавлены Pydantic-схемы для основных сущностей.
- Добавлены CRUD API для внутренних WFM-разделов.
- Добавлен seed демо-данных при `DEMO_SEED=true`.
- Frontend переработан в рабочий кабинет с 13 разделами.
- Дизайн обновлён под бренд «Телесейлз Сервис».
- Scheduler оставлен заглушкой с понятным сообщением о следующем этапе.
- Раздел «Интеграция» оставлен информационной заглушкой без внешних подключений.

## 3. Созданные и используемые таблицы

- `users`
- `teams`
- `employees`
- `skills`
- `employee_skills`
- `queues`
- `workload_intervals`
- `staffing_requirements`
- `shifts`
- `schedule_assignments`
- `absences`
- `kpi_snapshots`
- `audit_log`

Alembic на этом этапе не подключался. Для MVP используется `Base.metadata.create_all`.

## 4. Добавленные внутренние маршруты

- `GET/POST /api/v1/employees`
- `GET/PUT/DELETE /api/v1/employees/{id}`
- `GET/POST /api/v1/teams`
- `GET/PUT/DELETE /api/v1/teams/{id}`
- `GET/POST /api/v1/skills`
- `GET/PUT/DELETE /api/v1/skills/{id}`
- `GET/POST /api/v1/queues`
- `GET/PUT/DELETE /api/v1/queues/{id}`
- `GET/POST /api/v1/workload`
- `GET/PUT/DELETE /api/v1/workload/{id}`
- `GET/POST /api/v1/staffing`
- `GET/PUT/DELETE /api/v1/staffing/{id}`
- `GET/POST /api/v1/shifts`
- `GET/PUT/DELETE /api/v1/shifts/{id}`
- `GET/POST /api/v1/schedules`
- `GET/PUT/DELETE /api/v1/schedules/{id}`
- `GET/POST /api/v1/absences`
- `GET/PUT/DELETE /api/v1/absences/{id}`
- `GET /api/v1/reports/summary`

## 5. Рабочие страницы frontend

- Дашборд
- Сотрудники
- Команды
- Навыки
- Очереди
- Нагрузка
- Потребность
- Смены
- Графики
- Отсутствия
- Отчёты
- Настройки
- Интеграция

Все страницы используют внутренние API или статические настройки MVP. Внешние адреса во frontend не используются.

## 6. Демо-данные

Добавлены:

- команды: «Продажи», «Поддержка», «Контроль качества»;
- навыки: «Входящие звонки», «Исходящие звонки», «Чаты», «VIP-клиенты», «Продажи»;
- очереди: «Входящая линия», «Исходящая линия», «Чат-поддержка»;
- 10 демо-сотрудников;
- смены: «Утро 09:00-18:00», «День 10:00-19:00», «Вечер 12:00-21:00»;
- интервальная нагрузка на текущую неделю;
- потребность по очередям;
- назначения графиков;
- одно демо-отсутствие;
- KPI snapshots.

## 7. Изменения дизайна

- Бренд: «Телесейлз Сервис».
- Название продукта: «WFM-платформа».
- Светлый B2B-интерфейс.
- Боковая навигация.
- Верхняя панель.
- KPI-карточки.
- Единый стиль таблиц, кнопок и статусов.
- Адаптивная вёрстка без тяжёлых UI-библиотек.

## 8. Проверки

Выполнены локальные проверки:

- `docker compose up -d --build`
- `docker compose ps`
- `curl -I http://127.0.0.1/`
- `curl -s http://127.0.0.1/health`
- `curl -s http://127.0.0.1/scheduler/health`
- `curl -s http://127.0.0.1/api/v1/employees`
- `curl -s http://127.0.0.1/api/v1/teams`
- `curl -s http://127.0.0.1/api/v1/skills`
- `curl -s http://127.0.0.1/api/v1/queues`
- `curl -s http://127.0.0.1/api/v1/workload`
- `curl -s http://127.0.0.1/api/v1/staffing`
- `curl -s http://127.0.0.1/api/v1/shifts`
- `curl -s http://127.0.0.1/api/v1/schedules`
- `curl -s http://127.0.0.1/api/v1/absences`
- `curl -s http://127.0.0.1/api/v1/reports/summary`
- `docker compose exec -T frontend npm run build`

## 9. Найденные проблемы и исправления

- Frontend build падал из-за устаревшего `moduleResolution`. Исправлено на `Bundler`.
- TypeScript не видел CSS imports. Добавлен `src/vite-env.d.ts`.
- Использование `JSX.Element` вызвало ошибку типов. Заменено на `ReactNode`.
- В демо-данных отсутствовали записи отсутствий. Добавлено демо-отсутствие и обновлён seed.

## 10. Что не делалось

- Внешние интеграции.
- Реальные подключения к сторонним системам.
- Работа с токенами, паролями, ключами и секретами.
- Авторизация пользователей.
- Промышленный расчёт графиков.
- Импорт CSV.
- Alembic migrations.
- Production TLS.
- Изменение SSH, mihomo, codex, firewall или системного доступа.

## 11. Что нужно сделать на Этапе 3

- Добавить расчёт потребности по интервальной нагрузке.
- Добавить импорт нагрузки из CSV.
- Реализовать первичную генерацию графиков.
- Добавить правила планирования и проверки конфликтов.
- Подготовить Alembic migrations.
- Подготовить авторизацию пользователей.

## 12. Итог

Этап 2 выполнен. Сайт открывается через Nginx, backend и scheduler отвечают на health endpoints, основные WFM-разделы работают с демо-данными. Проект готов к Этапу 3.
