# Stage 7.1 redesign report

Дата: 2026-05-27.

## 1. Проблемы старого дизайна

Интерфейс выглядел слишком демонстрационным: много жирного текста, крупные KPI-цифры, большие карточки, скругления 18-24px, яркие бейджи, тяжёлый sidebar и избыточные отступы. Для внутренней WFM/BI-системы контакт-центра это создавало ощущение demo UI, а не рабочего enterprise-инструмента.

## 2. Изменённые CSS/TSX-файлы

- `frontend/src/styles/theme.css`
- `frontend/src/styles/global.css`
- `frontend/src/styles/main.css`
- `frontend/src/components/DataTable.tsx`
- `frontend/src/components/StatusBadge.tsx`

Backend, API-контракты, авторизация, роли и данные не менялись.

## 3. Дизайн-токены

Добавлена строгая система переменных: `--color-bg`, `--color-surface`, `--color-border`, `--color-text`, `--color-primary`, `--color-accent`, `--radius-sm/md/lg`, `--shadow-card`, `--font-sans`.

Основные цвета переведены на спокойную enterprise-палитру: фон `#F6F8FB`, primary `#2563EB`, accent `#EA580C`, текст `#111827`.

## 4. Снижение жирности текста

В frontend CSS убраны `font-weight: 700/800/900`. Навигация и кнопки используют 500, заголовки и KPI-значения 600, обычный текст 400.

## 5. Sidebar, header, cards, tables, forms

Sidebar уменьшен до 248px, логомарк до 32px, пункты меню до 38px. Активный пункт стал спокойным: светло-синий фон, синий текст и тонкая левая полоска.

Header стал компактнее: белый фон, нижняя граница, маленькие status pills, обычная жирность имени пользователя и компактная кнопка выхода.

KPI-карточки уменьшены до 98px minimum height, radius 12px, padding 14-16px, value до 28px.

Таблицы стали плотнее: font-size 13px, компактные строки, header weight 500, числовые колонки выравниваются вправо.

Формы и фильтры приведены к height 38px, radius 8px, тонкому синему focus ring.

## 6. Проверенные страницы

Проверены через frontend HTTP и ключевые API: Login, Dashboard, Сотрудники/справочники через общий DataTable, Графики, Отчёты, Настройки, О системе. Также затронуты общие компоненты, поэтому единый стиль применяется к справочникам, журналу, интеграции и документации.

## 7. Сборки и тесты

Выполнено:

- `docker compose up -d --build` — успешно;
- `docker compose ps` — все сервисы запущены;
- `/health` и `/api/v1/version` — отвечают;
- frontend HTTP `/` — `200`;
- admin login — работает;
- protected API без token — `401`;
- protected API с token — `200`;
- `docker compose exec -T frontend npm run build` — успешно;
- `docker compose exec -T backend pytest -q` — `35 passed, 1 skipped`.

Локальная host-команда `npm --prefix frontend run build` не проходит из-за отсутствия локальных node dependencies (`tsc` не найден). Сетевые установки не выполнялись по ограничению этапа; каноническая проверка выполнена внутри существующего frontend-контейнера.

## 8. Что осталось улучшить

- провести ручную визуальную проверку в браузере на нескольких разрешениях;
- при необходимости добавить отдельные compact-варианты для очень широких таблиц;
- на следующем UX-этапе привести CRUD-формы справочников к единому enterprise-паттерну.
