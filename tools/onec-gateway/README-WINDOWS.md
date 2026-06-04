# WFM 1C Gateway для Windows Server

Версия пакета: `2026-06-02.2`.

Эти файлы подготовлены на WFM-сервере `192.168.12.31`. Codex не устанавливает и не запускает их на Windows Server. Пользователь вручную копирует пакет на сервер 1С/Gateway `10.1.1.12`.

## Куда копировать

Скопируйте содержимое `/opt/wfm-naumen/tools/onec-gateway` на Windows Server в:

```text
C:\WFM1CGateway
```

## Переменные окружения

Gateway может получать параметры базы из тела запроса WFM или из переменных окружения Windows:

```text
WFM_1C_INFOBASE_TYPE=server
WFM_1C_SERVER=1c-server.local
WFM_1C_DATABASE=TSS_MAIN
WFM_1C_USERNAME=<пользователь 1С>
WFM_1C_PASSWORD=<пароль 1С>
```

Для файловой базы используйте:

```text
WFM_1C_INFOBASE_TYPE=file
WFM_1C_FILE_BASE_PATH=\\server\share\1c_base
```

Не сохраняйте реальные пароли в документации и не публикуйте Gateway наружу.

## Перезапуск задачи

```powershell
schtasks /End /TN "WFM 1C Gateway"
schtasks /Run /TN "WFM 1C Gateway"
```

Если задачи ещё нет:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\WFM1CGateway\install-scheduled-task.ps1
```

## Проверки на Windows Server

```powershell
Invoke-RestMethod http://127.0.0.1:8088/health
```

Проверка подключения:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\WFM1CGateway\test-gateway.ps1
```

Диагностика сотрудника:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\WFM1CGateway\diagnose-employee-lookup.ps1 -Inn 450104295305
```

## Что изменено

Endpoint `POST /api/v1/1c/check-employee-status` и диагностический endpoint `POST /api/v1/1c/diagnose-employee-lookup` используют несколько стратегий поиска карточек сотрудника:

1. `Справочник.Сотрудники.ФизическоеЛицо = &ФизическоеЛицо`
2. `Справочник.Сотрудники.ФизическоеЛицо.ИНН = &ИНН`
3. `Справочник.Сотрудники.ФизЛицо = &ФизическоеЛицо`
4. `Справочник.Сотрудники.Владелец = &ФизическоеЛицо`

Если физлицо найдено, но карточки сотрудников не найдены, Gateway возвращает предупреждения и ошибки стратегий. Эти данные нужно приложить к обращению для уточнения реквизитов конфигурации 1С.
