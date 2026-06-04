# Этап 9.7. WFM-side стабилизация 1С Gateway и Naumen-сопоставления

## Границы работ

Codex работал только на WFM-сервере `192.168.12.31` в каталоге `/opt/wfm-naumen`. Windows Server `10.1.1.12`, COMConnector, 1С, Windows Firewall, IIS/Apache и планировщик заданий Windows не изменялись.

## Диагностика WFM

- Backend, frontend, scheduler, PostgreSQL и Redis работают.
- `/health` отвечает `ok`.
- `/api/v1/version` отвечает версией WFM.
- Backup БД создан: `/opt/wfm-naumen/backups/db/wfm_naumen_20260602T105358Z.sql`.
- Общая 1С-интеграция имела успешный статус последней проверки `ok`.
- У сотрудников не было `onec_status = ok`.
- У 27 сотрудников оставался старый `gateway_unavailable`; он помечен сообщением «Требуется повторная сверка».
- Сообщений `test listener works` в сотрудниках не найдено.

WFM при кнопке «Сверить с 1С» вызывает `POST /api/v1/1c/check-employee-status` через внутренний Windows Gateway.

## Почему подключение работало, но статус сотрудника был неверным

Сеть и общий Gateway уже работали: проверка подключения к 1С проходила. Ошибка «Физлицо найдено, но карточки сотрудников не найдены» означает проблему в логике поиска карточек сотрудников внутри PowerShell Gateway на Windows Server, а не в WFM и не в сети.

## Что изменено в WFM

- Добавлено поле `employees.onec_metadata` для расширенной диагностики Gateway.
- Ответ Gateway теперь принимает `lookup_strategy_used`, `cards`, `query_warnings`, `query_errors`, `gateway_version`.
- Статус `ok` запрещён для карточки сотрудника.
- Если Gateway возвращает `not_found` + `found=true` + сообщение про карточки, WFM ставит `not_found_person_cards` с лейблом «Карточки сотрудника не найдены».
- Если Gateway version ниже `2026-06-02.2`, WFM добавляет предупреждение «Gateway устарел».
- Добавлен WFM endpoint `POST /api/v1/integrations/onec/diagnose-employee-lookup`.
- В UI 1С добавлена диагностика поиска сотрудника по ИНН.
- В карточке сотрудника показаны active/dismissed cards и стратегия поиска из metadata.

## Gateway package

Подготовлен пакет для ручного копирования на Windows Server:

- `/opt/wfm-naumen/tools/onec-gateway/gateway.ps1`
- `/opt/wfm-naumen/tools/onec-gateway/run-gateway.cmd`
- `/opt/wfm-naumen/tools/onec-gateway/install-scheduled-task.ps1`
- `/opt/wfm-naumen/tools/onec-gateway/test-gateway.ps1`
- `/opt/wfm-naumen/tools/onec-gateway/diagnose-employee-lookup.ps1`
- `/opt/wfm-naumen/tools/onec-gateway/README-WINDOWS.md`

Версия Gateway package: `2026-06-02.2`.

## Что пользователь делает на Windows Server

Пользователь вручную копирует пакет на `10.1.1.12` в `C:\WFM1CGateway`, перезапускает задачу `WFM 1C Gateway`, проверяет `/health`, `/check-connection`, `/check-employee-status` и при проблеме запускает `/diagnose-employee-lookup`.

## Naumen

Naumen-сверка исправлена: первичная кнопка «Сверить с Naumen» теперь сопоставляет сотрудника по ФИО внутри текущего проекта. UUID используется отдельной кнопкой «Проверить UUID» как ручной fallback.

По документации Naumen подтверждён контур загрузки операторов проекта в WFM. Endpoints детальной статистики сотрудника, AHT/SLA/обращений и фактических выходов остаются неподтверждёнными; fake-метрики не создавались.

## UI

- В «Интеграции / 1С» добавлена диагностика поиска сотрудника.
- В карточке сотрудника блок 1С показывает диагностические поля.
- В «Команды» реализовано раскрытие состава и назначение сотрудников команды.
- В «Сотрудники» первичное Naumen-действие переименовано в «Сверить по ФИО», UUID проверяется отдельной кнопкой.

## Проверки

- Backend tests: `47 passed, 19 skipped`.
- Frontend build: успешно.
- После тестов реальные настройки 1С восстановлены из backup без вывода секретов.

## Ограничения

- Gateway на `10.1.1.12` пользователь обновляет вручную.
- Реальные 1С-реквизиты связи справочника `Сотрудники` с `ФизическиеЛица` нужно подтвердить диагностикой на Windows Server.
- Детальная статистика Naumen требует подтверждённых API endpoints.
