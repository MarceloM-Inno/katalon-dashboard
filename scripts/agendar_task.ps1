$taskName = "KatalonSync_BNPL"
$projectRoot = "E:\git\katalon-dashboard"
$venvPython = "$projectRoot\.venv\Scripts\python.exe"
$scriptPath = "$projectRoot\scripts\parse_and_send.py"

$action = New-ScheduledTaskAction -Execute $venvPython -Argument "`"$scriptPath`"" -WorkingDirectory "$projectRoot"
$triggers = @(
    (New-ScheduledTaskTrigger -Daily -At 06:00),
    (New-ScheduledTaskTrigger -Daily -At 18:00)
)
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit ([TimeSpan]::FromHours(2))
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $triggers -Settings $settings -Principal $principal -Force

Write-Host "Tarefa '$taskName' criada com sucesso!"
Write-Host "Executa diariamente as 06:00 e 18:00."
Write-Host ""
Write-Host "Para testar manualmente:"
Write-Host "  $venvPython `"$scriptPath`""
