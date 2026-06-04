$TaskName = "WFM 1C Gateway"
$ScriptPath = "C:\WFM1CGateway\run-gateway.cmd"

if (-not (Test-Path $ScriptPath)) {
    Write-Host "Файл не найден: $ScriptPath"
    exit 1
}

$Action = New-ScheduledTaskAction -Execute $ScriptPath
$Trigger = New-ScheduledTaskTrigger -AtStartup
$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -RunLevel Highest
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Principal $Principal -Settings $Settings -Force
Start-ScheduledTask -TaskName $TaskName
Write-Host "Задача $TaskName установлена и запущена."
