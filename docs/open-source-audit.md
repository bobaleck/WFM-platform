# Open-source audit

Дата: 2026-05-26.

Проверка выполнена только по локальному проекту `/opt/wfm-naumen`: `requirements.txt`, `package.json`, `docker-compose.yml`, Dockerfile, README, docs и исходный код. Внешние сетевые запросы не выполнялись.

## Вывод

В проект не встроено готовое open-source WFM/HRM-решение. Проект является кастомной WFM-платформой, реализованной на open-source технологическом стеке.

Система является кастомным WFM-layer на open-source технологическом стеке.

Локальный поиск по проекту не выявил подключённых коробочных WFM/HRM-систем: Frappe HR, ERPNext HR, OrangeHRM, Open HRMS/Odoo, TimeTrex, Staffjoy, Timefold.

## Компоненты

| Компонент | Тип | Назначение | Open-source или custom | Где используется | Лицензия, если можно определить локально | Риск/комментарий |
|---|---|---|---|---|---|---|
| Python | Runtime | Backend и scheduler | Open-source | `backend`, `scheduler` Docker images | Требует дополнительной проверки | Базовая платформа исполнения |
| FastAPI | Backend framework | REST API | Open-source | `backend/app/main.py`, `scheduler/app/main.py` | Требует дополнительной проверки локально | Нужно отслеживать security updates |
| SQLAlchemy | ORM | Модели и доступ к БД | Open-source | `backend/app/models`, `backend/app/db` | MIT | Схема теперь зафиксирована baseline migration |
| Pydantic | Validation | Схемы API | Open-source | `backend/app/schemas`, `scheduler/app/main.py` | MIT | Используется через FastAPI |
| PostgreSQL | Database | Хранение данных WFM | Open-source | `docker-compose.yml` | Требует дополнительной проверки | Не опубликован наружу |
| Redis | Cache | Кэш/очередь для будущих задач | Open-source | `docker-compose.yml` | Требует дополнительной проверки | Не опубликован наружу |
| React | Frontend | UI приложения | Open-source | `frontend/src` | MIT | Версии берутся из локального container metadata |
| Vite | Build tool | Dev/build frontend | Open-source | `frontend/package.json` | MIT | В `package.json` указано `latest`; для production лучше закрепить версии |
| TypeScript | Language/tooling | Типизация frontend | Open-source | `frontend/src`, `tsconfig.json` | Apache-2.0 | В `package.json` указано `latest` |
| Lucide React | Icons | Иконки интерфейса | Open-source | `frontend/src/components`, pages | ISC | Низкий риск |
| Docker Compose | Runtime orchestration | Запуск сервисов | Open-source | `docker-compose.yml` | Требует дополнительной проверки | Self-hosted deployment |
| Nginx | Reverse proxy | Проксирование UI/API | Open-source | `infra/nginx` | Требует дополнительной проверки | TLS не настраивался на этом этапе |
| WFM models | Domain | Сотрудники, команды, навыки, очереди, графики | Custom | `backend/app/models/wfm.py` | Внутренняя разработка | Требует развития бизнес-правил |
| WFM API | Domain API | CRUD, import, planning, reports | Custom | `backend/app/api/wfm.py` | Внутренняя разработка | Нужно сохранять обратную совместимость |
| Расчёт потребности | WFM logic | MVP staffing calculation | Custom | `backend/app/services/planning.py` | Внутренняя разработка | MVP-формула, не промышленный оптимизатор |
| Генерация графиков | WFM logic | Черновые смены и покрытие | Custom | `backend/app/services/planning.py`, API | Внутренняя разработка | Требует расширения ограничений |
| Интерфейс | UI | Операционный web UI | Custom | `frontend/src/pages` | Внутренняя разработка | Не коробочная HRMS/WFM |
| План/факт и отчёты | Reporting | Сравнение плановых и фактических данных | Custom | `backend/app/api/wfm.py`, `frontend/src/pages/Reports.tsx` | Внутренняя разработка | Требует промышленной подготовки отчётов |
| Авторизация и RBAC | Security | Bearer token, роли, права | Custom на OSS-библиотеках | `backend/app/api/auth.py`, `backend/app/core/rbac.py` | Внутренняя разработка | Для production нужны доп. меры: TLS, rotation, cookie policy |
| Audit log | Security/ops | Журнал действий | Custom | `backend/app/models/wfm.py`, API | Внутренняя разработка | Нужно расширять покрытие событий |

## Custom-разработка

Кастомными являются модели WFM, API, расчёт потребности, генерация графиков, интерфейс, отчёты, план/факт, авторизация внутри приложения, RBAC и audit log. Они не импортированы из готового WFM/HRM-продукта.

## Соответствие требованию о наличии Workforce Management

Уже реализованы WFM-функции: сотрудники, команды, навыки, очереди, импорт нагрузки, расчёт потребности, генерация графиков, покрытие, подтверждение и публикация графиков, импорт факта, план/факт, CSV-экспорты, роли и audit log.

В статусе MVP остаются расчёт потребности, генерация графиков, покрытие, отчёты и интеграционные контракты. Они работоспособны для self-hosted MVP, но не являются промышленным оптимизационным движком.

Требуют доработки: расширенные ограничения расписаний, прогнозирование, сценарное планирование, richer reports, полноценная проверка восстановления, production monitoring, TLS и external data adapter.

Проект можно позиционировать как self-hosted WFM-platform, потому что он хранит доменную WFM-модель, поддерживает ключевой цикл workload -> staffing -> schedules -> coverage -> plan/fact и развёртывается локально в Docker Compose.

Проект не является коробочным Frappe/OrangeHRM/TimeTrex, потому что в локальном коде нет их зависимостей, контейнеров, модулей, миграций или UI. Используется собственный WFM-layer поверх open-source технологического стека.

## Рекомендация по готовым open-source компонентам

Frappe HR сейчас подключать не стоит: это усложнит архитектуру, модель данных, роли и эксплуатацию, не закрывая немедленно WFM-специфику контактного центра.

Timefold стоит рассмотреть позже как open-source оптимизационный движок для более сложного расписания, когда будут формализованы ограничения, hard/soft penalties и тестовые наборы.

Переписывать текущую систему на готовую HRMS сейчас нецелесообразно: уже создан WFM-domain layer, а HRMS не заменяет контакт-центровое планирование нагрузки и покрытия.

Рекомендуется оставить текущий кастомный WFM-layer, использовать open-source компоненты как технологическую базу и подключать специализированные OSS-компоненты только после отдельного архитектурного решения.

## Обновление Этапа 7

Система остаётся кастомным WFM-layer на open-source технологическом стеке. Timefold не подключён; подготовлен документ архитектурного решения для будущего optional optimizer. Frappe/Odoo/OrangeHRM и другие тяжёлые HRM/WFM-системы не внедрялись.

## Обновление Этапа 7.2

Naumen-интеграция является кастомным адаптером проекта, подготовленным по локальному PDF. Готовое open-source WFM/HRM-решение по-прежнему не встроено. Новые компоненты используют существующий Python/FastAPI/SQLAlchemy/React стек; внешние библиотеки и сервисы не подключались.
