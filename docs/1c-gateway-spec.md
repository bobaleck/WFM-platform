# Спецификация Windows 1C Gateway

Gateway — внутренний HTTP-сервис, который ставится на Windows-сервер с установленной платформой 1С и доступом к нужной информационной базе. Gateway не публикует базу 1С в интернет и не заменяет сервер 1С. Он принимает запросы только из локальной сети от WFM и подключается к 1С через COMConnector.

## Где работает

- Windows-сервер;
- установлена платформа 1С;
- зарегистрирован COMConnector;
- есть сетевой доступ к серверу 1С или файловой базе;
- firewall разрешает доступ к Gateway только от WFM-сервера.

## Endpoints

`GET /health`

```json
{
  "status": "ok",
  "service": "1c-gateway"
}
```

`POST /api/v1/1c/check-connection`

Body для серверной базы:

```json
{
  "infobase_type": "server",
  "server": "1c-server.local",
  "database": "TSS_MAIN",
  "cluster": "",
  "username": "user",
  "password": "secret"
}
```

Body для файловой базы:

```json
{
  "infobase_type": "file",
  "file_base_path": "\\\\server\\share\\1c_base",
  "username": "user",
  "password": "secret"
}
```

Gateway должен проверить доступность COMConnector, подключение к базе и возможность выполнить безопасный read-only запрос.

`POST /api/v1/1c/check-employee-status`

```json
{
  "inn": "123456789012"
}
```

Response:

```json
{
  "status": "working|dismissed|not_found|error",
  "status_label": "Работает|Уволен|Не найден|Ошибка",
  "found": true,
  "active_cards_count": 1,
  "dismissed_cards_count": 0,
  "message": ""
}
```

## COMConnector connection string

Серверная база:

```text
Srvr="1c-server.local";Ref="TSS_MAIN";Usr="USER";Pwd="PASSWORD";
```

Файловая база:

```text
File="\\server\share\1c_base";Usr="USER";Pwd="PASSWORD";
```

Пароль не логировать и не возвращать в HTTP-ответах.

## Логика статуса

Gateway подключается к 1С через COMConnector, ищет физлицо по ИНН, получает все карточки сотрудников этого физлица и анализирует дату увольнения.

- есть карточка без даты увольнения — `working`;
- все карточки с датой увольнения — `dismissed`;
- ничего не найдено — `not_found`;
- ошибка запроса — `error`.

Ориентиры по регистрам и справочникам: `Справочник.ФизическиеЛица`, `Справочник.Сотрудники`, `РегистрСведений.ТекущиеКадровыеДанныеСотрудниковУНФ`, `РегистрСведений.ТекущиеКадровыеДанныеСотрудников`, `РегистрСведений.КадроваяИсторияСотрудников`.

## Безопасность

- Gateway доступен только внутри локальной сети;
- желательно использовать Gateway token;
- WFM хранит Gateway token зашифрованно;
- firewall Gateway разрешает доступ только от WFM-сервера;
- логи Gateway не содержат пароль 1С, token, полную строку подключения и лишние персональные данные.
# Актуализация этапа 9.7

Gateway — внутренний Windows-сервис на `10.1.1.12`, доступный WFM-серверу `192.168.12.31`. Gateway не публикует базу 1С в интернет.

Текущая рекомендуемая версия: `2026-06-02.2`.

## Обязательные endpoints

- `GET /health`
- `POST /api/v1/1c/check-connection`
- `POST /api/v1/1c/check-employee-status`
- `POST /api/v1/1c/diagnose-employee-lookup`

`/health` означает только доступность процесса Gateway. Успешная сверка сотрудника возможна только через `/check-employee-status`.

## Расширенный ответ check-employee-status

```json
{
  "status": "working|dismissed|not_found|error",
  "status_label": "Работает|Уволен|Не найден|Ошибка",
  "found": true,
  "inn": "123456789012",
  "full_name": "...",
  "active_cards_count": 1,
  "dismissed_cards_count": 0,
  "message": "",
  "lookup_strategy_used": "Справочник.Сотрудники.ФизическоеЛицо = &ФизическоеЛицо",
  "cards": [],
  "query_warnings": [],
  "query_errors": [],
  "gateway_version": "2026-06-02.2"
}
```

Если физлицо найдено, но карточки сотрудников не найдены, Gateway должен вернуть `found=true`, `status=not_found`, `status_label=Карточки сотрудника не найдены` и диагностические поля.
