param(
    [Parameter(Mandatory=$true)][string]$Inn
)

$BaseUrl = "http://127.0.0.1:8088"
$body = @{ inn = $Inn } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "$BaseUrl/api/v1/1c/diagnose-employee-lookup" -ContentType "application/json" -Body $body | ConvertTo-Json -Depth 20
