$taskName = "KatalonSync_BNPL"
$projectRoot = "E:\Victor\Dashboard\katalon-dashboard"
$scriptPath = "$projectRoot\scripts\parse_and_send.py"
$pythonExe = "python"

$action = New-ScheduledTaskAction -Execute $pythonExe -Argument "`"$scriptPath`"" -WorkingDirectory "$projectRoot\scripts"
$trigger = New-ScheduledTaskTrigger -Daily -At 06:00
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force

Write-Host "Tarefa '$taskName' criada com sucesso!"
Write-Host "Executa diariamente as 06:00."
Write-Host ""
Write-Host "Para testar manualmente:"
Write-Host "  python `"$scriptPath`""
