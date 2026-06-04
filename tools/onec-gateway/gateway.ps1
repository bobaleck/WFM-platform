param(
    [string]$ListenPrefix = "http://+:8088/",
    [string]$GatewayToken = ""
)

$GatewayVersion = "2026-06-02.2"

function Write-GatewayLog {
    param([string]$Message)
    Write-Host ("[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message)
}

function Read-JsonBody {
    param($Request)
    $reader = New-Object System.IO.StreamReader($Request.InputStream, $Request.ContentEncoding)
    $raw = $reader.ReadToEnd()
    if ([string]::IsNullOrWhiteSpace($raw)) { return @{} }
    return $raw | ConvertFrom-Json
}

function Send-Json {
    param($Response, [object]$Data, [int]$StatusCode = 200)
    $Response.StatusCode = $StatusCode
    $Response.ContentType = "application/json; charset=utf-8"
    $json = $Data | ConvertTo-Json -Depth 20
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
    $Response.OutputStream.Write($bytes, 0, $bytes.Length)
    $Response.OutputStream.Close()
}

function Assert-Token {
    param($Request)
    if ([string]::IsNullOrWhiteSpace($GatewayToken)) { return $true }
    $header = $Request.Headers["Authorization"]
    return $header -eq "Bearer $GatewayToken"
}

function New-ConnectionString {
    param($Payload)
    $usr = [string]$Payload.username
    $pwd = [string]$Payload.password
    if ($Payload.infobase_type -eq "file") {
        return 'File="{0}";Usr="{1}";Pwd="{2}";' -f $Payload.file_base_path, $usr, $pwd
    }
    return 'Srvr="{0}";Ref="{1}";Usr="{2}";Pwd="{3}";' -f $Payload.server, $Payload.database, $usr, $pwd
}

function Get-ConnectionPayload {
    param($Body)
    if ($Body.server -or $Body.database -or $Body.file_base_path) { return $Body }
    return [pscustomobject]@{
        infobase_type = if ($env:WFM_1C_INFOBASE_TYPE) { $env:WFM_1C_INFOBASE_TYPE } else { "server" }
        server = $env:WFM_1C_SERVER
        database = $env:WFM_1C_DATABASE
        file_base_path = $env:WFM_1C_FILE_BASE_PATH
        username = $env:WFM_1C_USERNAME
        password = $env:WFM_1C_PASSWORD
    }
}

function Connect-1C {
    param($Payload)
    $connector = New-Object -ComObject "V83.COMConnector"
    $connectionString = New-ConnectionString -Payload $Payload
    return $connector.Connect($connectionString)
}

function Normalize-EmptyDate {
    param($Value)
    if ($null -eq $Value) { return $null }
    $text = [string]$Value
    if ([string]::IsNullOrWhiteSpace($text)) { return $null }
    if ($text -match "^0001|^0000|^0101") { return $null }
    return $text
}

function Invoke-QueryRows {
    param($Connection, [string]$QueryText, [hashtable]$Params)
    $query = $Connection.NewObject("Запрос")
    $query.Текст = $QueryText
    foreach ($key in $Params.Keys) {
        $query.УстановитьПараметр($key, $Params[$key])
    }
    $result = $query.Выполнить()
    $selection = $result.Выбрать()
    $rows = @()
    while ($selection.Следующий()) {
        $row = @{}
        foreach ($prop in $selection.GetType().GetProperties()) {
            try { $row[$prop.Name] = $selection.$($prop.Name) } catch {}
        }
        $rows += $selection
    }
    return $rows
}

function Find-PhysicalPersonByInn {
    param($Connection, [string]$Inn)
    $query = $Connection.NewObject("Запрос")
    $query.Текст = @"
ВЫБРАТЬ ПЕРВЫЕ 1
    ФизическиеЛица.Ссылка КАК Ссылка,
    ФизическиеЛица.Наименование КАК Наименование,
    ФизическиеЛица.ИНН КАК ИНН
ИЗ
    Справочник.ФизическиеЛица КАК ФизическиеЛица
ГДЕ
    ФизическиеЛица.ИНН = &ИНН
"@
    $query.УстановитьПараметр("ИНН", $Inn)
    $selection = $query.Выполнить().Выбрать()
    if ($selection.Следующий()) {
        return @{ Ref = $selection.Ссылка; FullName = [string]$selection.Наименование; Inn = [string]$selection.ИНН }
    }
    return $null
}

function Find-EmployeeCards {
    param($Connection, [string]$Inn, $PhysicalPerson)
    $warnings = @()
    $errors = @()
    $strategies = @(
        @{ Name = "Справочник.Сотрудники.ФизическоеЛицо = &ФизическоеЛицо"; Text = "ВЫБРАТЬ Сотрудники.Ссылка КАК Ссылка, Сотрудники.Наименование КАК Наименование, Сотрудники.ДатаУвольнения КАК ДатаУвольнения, Сотрудники.Организация КАК Организация ИЗ Справочник.Сотрудники КАК Сотрудники ГДЕ Сотрудники.ФизическоеЛицо = &ФизическоеЛицо"; Params = @{ "ФизическоеЛицо" = $PhysicalPerson.Ref } },
        @{ Name = "Справочник.Сотрудники.ФизическоеЛицо.ИНН = &ИНН"; Text = "ВЫБРАТЬ Сотрудники.Ссылка КАК Ссылка, Сотрудники.Наименование КАК Наименование, Сотрудники.ДатаУвольнения КАК ДатаУвольнения, Сотрудники.Организация КАК Организация ИЗ Справочник.Сотрудники КАК Сотрудники ГДЕ Сотрудники.ФизическоеЛицо.ИНН = &ИНН"; Params = @{ "ИНН" = $Inn } },
        @{ Name = "Справочник.Сотрудники.ФизЛицо = &ФизическоеЛицо"; Text = "ВЫБРАТЬ Сотрудники.Ссылка КАК Ссылка, Сотрудники.Наименование КАК Наименование, Сотрудники.ДатаУвольнения КАК ДатаУвольнения, Сотрудники.Организация КАК Организация ИЗ Справочник.Сотрудники КАК Сотрудники ГДЕ Сотрудники.ФизЛицо = &ФизическоеЛицо"; Params = @{ "ФизическоеЛицо" = $PhysicalPerson.Ref } },
        @{ Name = "Справочник.Сотрудники.Владелец = &ФизическоеЛицо"; Text = "ВЫБРАТЬ Сотрудники.Ссылка КАК Ссылка, Сотрудники.Наименование КАК Наименование, Сотрудники.ДатаУвольнения КАК ДатаУвольнения, Сотрудники.Организация КАК Организация ИЗ Справочник.Сотрудники КАК Сотрудники ГДЕ Сотрудники.Владелец = &ФизическоеЛицо"; Params = @{ "ФизическоеЛицо" = $PhysicalPerson.Ref } }
    )
    foreach ($strategy in $strategies) {
        try {
            $query = $Connection.NewObject("Запрос")
            $query.Текст = $strategy.Text
            foreach ($key in $strategy.Params.Keys) { $query.УстановитьПараметр($key, $strategy.Params[$key]) }
            $selection = $query.Выполнить().Выбрать()
            $cards = @()
            while ($selection.Следующий()) {
                $dismissal = Normalize-EmptyDate $selection.ДатаУвольнения
                $cards += @{
                    full_name = [string]$selection.Наименование
                    dismissal_date = $dismissal
                    organization = [string]$selection.Организация
                    is_active = ($null -eq $dismissal)
                }
            }
            if ($cards.Count -gt 0) {
                return @{ Cards = $cards; Strategy = $strategy.Name; Warnings = $warnings; Errors = $errors }
            }
        } catch {
            $errors += ("{0}: {1}" -f $strategy.Name, $_.Exception.Message)
        }
    }
    $warnings += "Карточки сотрудников не найдены стандартными стратегиями. Проверьте реквизиты справочника Сотрудники в вашей конфигурации 1С."
    return @{ Cards = @(); Strategy = $null; Warnings = $warnings; Errors = $errors }
}

function Check-EmployeeStatus {
    param($Payload)
    $inn = [string]$Payload.inn
    $connection = Connect-1C -Payload $Payload.connection
    $person = Find-PhysicalPersonByInn -Connection $connection -Inn $inn
    if ($null -eq $person) {
        return @{ status = "not_found"; status_label = "Не найден"; found = $false; inn = $inn; active_cards_count = 0; dismissed_cards_count = 0; message = "Физлицо по ИНН не найдено."; gateway_version = $GatewayVersion }
    }
    $lookup = Find-EmployeeCards -Connection $connection -Inn $inn -PhysicalPerson $person
    $cards = $lookup.Cards
    if ($cards.Count -eq 0) {
        return @{ status = "not_found"; status_label = "Карточки сотрудника не найдены"; found = $true; inn = $inn; full_name = $person.FullName; active_cards_count = 0; dismissed_cards_count = 0; message = "Физлицо найдено, но карточки сотрудников не найдены."; lookup_strategy_used = $lookup.Strategy; cards = @(); query_warnings = $lookup.Warnings; query_errors = $lookup.Errors; gateway_version = $GatewayVersion }
    }
    $active = @($cards | Where-Object { $_.is_active })
    $dismissed = @($cards | Where-Object { -not $_.is_active })
    if ($active.Count -gt 0) {
        $status = "working"; $label = "Работает"
    } else {
        $status = "dismissed"; $label = "Уволен"
    }
    return @{ status = $status; status_label = $label; found = $true; inn = $inn; full_name = $person.FullName; active_cards_count = $active.Count; dismissed_cards_count = $dismissed.Count; message = "Сверка выполнена."; lookup_strategy_used = $lookup.Strategy; cards = $cards; query_warnings = $lookup.Warnings; query_errors = $lookup.Errors; gateway_version = $GatewayVersion }
}

$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add($ListenPrefix)
$listener.Start()
Write-GatewayLog "WFM 1C Gateway $GatewayVersion started on $ListenPrefix"

while ($listener.IsListening) {
    $context = $listener.GetContext()
    try {
        if (-not (Assert-Token -Request $context.Request)) {
            Send-Json $context.Response @{ status = "error"; message = "Нет доступа"; gateway_version = $GatewayVersion } 401
            continue
        }
        $path = $context.Request.Url.AbsolutePath
        if ($context.Request.HttpMethod -eq "GET" -and $path -eq "/health") {
            Send-Json $context.Response @{ status = "ok"; service = "1c-gateway"; gateway_version = $GatewayVersion }
        } elseif ($context.Request.HttpMethod -eq "POST" -and $path -eq "/api/v1/1c/check-connection") {
            $body = Read-JsonBody $context.Request
            $connectionPayload = Get-ConnectionPayload -Body $body
            $connection = Connect-1C -Payload $connectionPayload
            Send-Json $context.Response @{ status = "ok"; connected = $true; service = "1c-gateway"; message = "Подключение к 1С выполнено."; gateway_version = $GatewayVersion }
        } elseif ($context.Request.HttpMethod -eq "POST" -and $path -eq "/api/v1/1c/check-employee-status") {
            $body = Read-JsonBody $context.Request
            $connectionPayload = Get-ConnectionPayload -Body $body
            $result = Check-EmployeeStatus @{ inn = $body.inn; connection = $connectionPayload }
            Send-Json $context.Response $result
        } elseif ($context.Request.HttpMethod -eq "POST" -and $path -eq "/api/v1/1c/diagnose-employee-lookup") {
            $body = Read-JsonBody $context.Request
            $connectionPayload = Get-ConnectionPayload -Body $body
            $result = Check-EmployeeStatus @{ inn = $body.inn; connection = $connectionPayload }
            $result["recommendation"] = "Если физлицо найдено, но карточки не найдены, отправьте query_errors/query_warnings разработчику Gateway и уточните реквизит связи справочника Сотрудники с физлицом."
            Send-Json $context.Response $result
        } else {
            Send-Json $context.Response @{ status = "error"; message = "Метод не найден"; gateway_version = $GatewayVersion } 404
        }
    } catch {
        Send-Json $context.Response @{ status = "error"; status_label = "Ошибка"; message = $_.Exception.Message; gateway_version = $GatewayVersion } 500
    }
}
