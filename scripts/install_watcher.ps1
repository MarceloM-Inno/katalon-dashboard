$taskName = "KatalonDashboardWatcher"
$scriptPath = "E:\Victor\Dashboard\katalon-dashboard\scripts\watch_reports.py"
$venvPython = "E:\Victor\Dashboard\katalon-dashboard\.venv\Scripts\python.exe"
$workDir = "E:\Victor\Dashboard\katalon-dashboard"

$action = New-ScheduledTaskAction -Execute $venvPython -Argument "scripts\watch_reports.py" -WorkingDirectory $workDir
$trigger = New-ScheduledTaskTrigger -AtStartup
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force

Write-Host "Tarefa '$taskName' criada com sucesso!"
Write-Host "Inicia automaticamente ao ligar o computador."
Get-ScheduledTask -TaskName $taskName | Format-List TaskName, State, Actions
