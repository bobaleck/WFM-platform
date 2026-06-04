# Эксплуатация

## Запуск и проверка

```bash
cd /opt/wfm-naumen
docker compose up -d --build
docker compose ps
curl -s http://127.0.0.1/health
curl -s http://127.0.0.1/api/v1/version
curl -s http://127.0.0.1/scheduler/health
```

## Логи

```bash
cd /opt/wfm-naumen
docker compose logs --tail=200 backend
docker compose logs --tail=100 frontend
docker compose logs --tail=100 scheduler
```

В логах нельзя публиковать пароли, токены, JWT secret, строки подключения 1С и другие секреты.

## Backup

Перед крупными изменениями:

```bash
cd /opt/wfm-naumen
./scripts/backup-db.sh
./scripts/backup-files.sh
```

Restore выполняется только вручную и только с подтверждением:

```bash
./scripts/restore-db.sh backups/db/<dump.sql> --confirm
```

## Авторизация

Вход: `http://<server>/login`.

Администратор создаётся из `/opt/wfm-naumen/.env`. Пароль администратора и `JWT_SECRET` не выводить в отчёты и команды с публичным выводом.

## Ручной WFM

Рабочие данные ведутся через UI:

- сотрудники;
- команды;
- навыки;
- очереди;
- смены;
- отсутствия;
- нагрузка XLSX/CSV;
- потребность;
- графики;
- отчёты.

Активные источники данных: ручной ввод, XLSX/CSV-реестры, сверка с 1С и операционные данные Naumen. Naumen используется только как отдельный операционный источник: UUID операторов, операторы проекта и будущая статистика. Naumen не является кадровым источником и не заменяет WFM-сотрудников автоматически.

## 1С

На Linux используется режим `gateway_http`. Direct COM не поддерживается на текущем сервере.

База 1С не публикуется в Web. В настройках указываются параметры внутреннего подключения:

- внутренний адрес Windows Gateway;
- тип базы: серверная или файловая;
- сервер 1С и имя информационной базы для серверной базы;
- путь к файловой базе 1С для файлового режима;
- пользователь 1С;
- пароль 1С.

Проверка без настроенного Gateway должна возвращать понятную ошибку: «Укажите внутренний адрес Windows Gateway». Direct COM на Linux должен возвращать unsupported.

Gateway token и пароль 1С хранятся зашифрованно и не выводятся в API-ответах. Диагностика показывает только признаки `*_present` и `*_saved`.

## Импорт

Сотрудники:

- `GET /api/v1/employees/import/template.xlsx`;
- `POST /api/v1/employees/import/xlsx`.

Нагрузка:

- `GET /api/v1/workload/template.xlsx`;
- `POST /api/v1/workload/import/xlsx`;
- `POST /api/v1/workload/import/csv`.

Naumen:

- `POST /api/v1/naumen/operators/sync` — загрузка операторов проекта, если endpoint доступен;
- `POST /api/v1/employees/naumen/match` — сопоставление операторов с WFM-сотрудниками;
- `POST /api/v1/employees/{id}/check-naumen` — сверка одного сотрудника по UUID Naumen.

## Расчёты и графики

```bash
curl -H "Authorization: Bearer <token>" -H 'Content-Type: application/json' \
  -d '{"date_from":"2026-01-15","date_to":"2026-01-21"}' \
  http://127.0.0.1/api/v1/planning/calculate-staffing
```

Черновик графика:

```bash
curl -H "Authorization: Bearer <token>" -H 'Content-Type: application/json' \
  -d '{"date_from":"2026-01-15","date_to":"2026-01-21","queue_id":null}' \
  http://127.0.0.1/api/v1/schedules/generate-draft
```

## Регулярные проверки

```bash
cd /opt/wfm-naumen
./scripts/status.sh
./scripts/healthcheck.sh
./scripts/disk-usage.sh
./scripts/db-size.sh
npm --prefix frontend run build
docker compose exec -T backend pytest
```
# Актуализация этапа 9.4

Перед изменениями БД выполнен backup существующим скриптом. При похожих изменениях сначала проверять:

- количество сотрудников, команд и навыков;
- записи без проекта;
- активные рабочие контуры;
- наличие `employee_project_access` и `employee_team_memberships`.

Если сотрудники есть в БД, но не видны в UI, запрещено создавать дубли. Нужно восстановить видимость через `employee_project_access`.

Для Naumen сначала загрузить операторов проекта, затем запускать сопоставление по ФИО. Если UUID проекта Naumen не задан или операторы не загружены, кнопки должны показывать понятную ошибку.

Секреты 1С и Naumen не выводить в консоль, логи и отчёты.
# Актуализация этапа 9.7

Перед изменениями БД создан backup. После backend-тестов настройки 1С были восстановлены из backup, потому что тесты используют mock Gateway.

Для 1С:

- не считать `/health` бизнес-проверкой сотрудника;
- не оставлять у сотрудников `onec_status=ok`;
- при `gateway_unavailable` после восстановления Gateway запускать повторную сверку;
- при «Физлицо найдено, но карточки не найдены» обновить `gateway.ps1` на Windows Server и запустить диагностику lookup.

Для Windows Server `10.1.1.12` действия выполняет пользователь вручную по `docs/1c-gateway-installation.md`.

Для Naumen:

- сначала загрузить операторов проекта;
- первично сопоставлять по ФИО;
- UUID использовать как ручной fallback;
- fake-метрики не создавать без подтверждённого endpoint.
# Обновление этапа 9.8

Перед изменениями БД создан backup `/opt/wfm-naumen/backups/db/wfm_naumen_20260602T121406Z.sql`. После backend tests реальные настройки 1С восстановлены из backup, чтобы mock Gateway тестов не остался в рабочей базе. Сервер 1С и Windows Gateway не менялись.
