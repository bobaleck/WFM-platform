# Пример-скелет Windows 1C Gateway. Не production.
# Запускать только на Windows-хосте с установленной платформой 1С и COMConnector.

$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add("http://+:8088/")
$listener.Start()

Write-Host "1C Gateway example started on http://+:8088/"

while ($listener.IsListening) {
    $context = $listener.GetContext()
    $request = $context.Request
    $response = $context.Response

    try {
        if ($request.HttpMethod -eq "GET" -and $request.Url.AbsolutePath -eq "/health") {
            $body = @{ status = "ok"; service = "1c-gateway" } | ConvertTo-Json -Depth 5
        }
        elseif ($request.HttpMethod -eq "POST" -and $request.Url.AbsolutePath -eq "/api/v1/1c/check-employee-status") {
            $reader = New-Object System.IO.StreamReader($request.InputStream)
            $payload = $reader.ReadToEnd() | ConvertFrom-Json
            $inn = [string]$payload.inn

            # Здесь должен быть production-код:
            # $connector = New-Object -ComObject "V83.COMConnector"
            # $connection = $connector.Connect("Srvr='server';Ref='base';Usr='user';Pwd='password';")
            # Далее: поиск физлица по ИНН, карточек сотрудников и дат увольнения.

            $body = @{
                status = "error"
                status_label = "Ошибка"
                found = $false
                inn = $inn
                active_cards_count = 0
                dismissed_cards_count = 0
                last_hire_date = $null
                last_dismissal_date = $null
                organization = $null
                message = "Пример Gateway не подключён к 1С"
            } | ConvertTo-Json -Depth 10
        }
        else {
            $response.StatusCode = 404
            $body = @{ status = "not_found" } | ConvertTo-Json
        }
    }
    catch {
        $response.StatusCode = 500
        $body = @{ status = "error"; message = "Ошибка Gateway" } | ConvertTo-Json
    }

    $buffer = [System.Text.Encoding]::UTF8.GetBytes($body)
    $response.ContentType = "application/json; charset=utf-8"
    $response.ContentLength64 = $buffer.Length
    $response.OutputStream.Write($buffer, 0, $buffer.Length)
    $response.OutputStream.Close()
}
