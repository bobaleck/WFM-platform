# Установка и обновление Windows 1C Gateway

WFM-сервер: `192.168.12.31`.

Сервер 1С/Gateway: `10.1.1.12`.

Codex работает только на WFM-сервере и не меняет Windows Server, COMConnector, 1С, Windows Firewall, IIS/Apache и планировщик заданий Windows.

## Файлы на WFM-сервере

Пакет подготовлен в:

```text
/opt/wfm-naumen/tools/onec-gateway
```

Содержимое:

- `gateway.ps1`
- `run-gateway.cmd`
- `install-scheduled-task.ps1`
- `test-gateway.ps1`
- `diagnose-employee-lookup.ps1`
- `README-WINDOWS.md`

## Что сделать вручную на Windows Server 10.1.1.12

1. Скопировать `gateway.ps1` и остальные файлы из WFM:

```text
/opt/wfm-naumen/tools/onec-gateway/gateway.ps1
```

в:

```text
C:\WFM1CGateway\gateway.ps1
```

2. Перезапустить задачу:

```powershell
schtasks /End /TN "WFM 1C Gateway"
schtasks /Run /TN "WFM 1C Gateway"
```

3. Проверить health:

```powershell
Invoke-RestMethod http://127.0.0.1:8088/health
```

4. Проверить подключение к 1С:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8088/api/v1/1c/check-connection -ContentType "application/json" -Body "{}"
```

5. Проверить сотрудника:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8088/api/v1/1c/check-employee-status -ContentType "application/json" -Body '{"inn":"450104295305"}'
```

6. Если физлицо найдено, но карточки не найдены:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\WFM1CGateway\diagnose-employee-lookup.ps1 -Inn 450104295305
```

Результат диагностики приложить для уточнения реквизитов справочника `Сотрудники` в конфигурации 1С.

Реальные пароли и строки подключения не включать в документацию и переписку.
