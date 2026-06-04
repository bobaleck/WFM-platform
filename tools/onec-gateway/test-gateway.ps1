$BaseUrl = "http://127.0.0.1:8088"

Write-Host "Проверка health..."
Invoke-RestMethod -Method Get -Uri "$BaseUrl/health"

Write-Host "Проверка подключения к 1С. Пароль берётся из переменных окружения Gateway или вводится пользователем вручную в WFM."
$body = @{
    infobase_type = $env:WFM_1C_INFOBASE_TYPE
    server = $env:WFM_1C_SERVER
    database = $env:WFM_1C_DATABASE
    file_base_path = $env:WFM_1C_FILE_BASE_PATH
    username = $env:WFM_1C_USERNAME
    password = $env:WFM_1C_PASSWORD
} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "$BaseUrl/api/v1/1c/check-connection" -ContentType "application/json" -Body $body
