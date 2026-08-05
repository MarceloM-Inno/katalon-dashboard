<#
.SYNOPSIS
    Instala o Watcher de Reports (tempo real) como Tarefa Agendada
.DESCRIPTION
    Cria uma tarefa no Windows Task Scheduler que:
    - Executa automaticamente na inicialização do sistema
    - Monitora E:\Pipeline-Report para novos JUnit_Report.xml
    - Envia os resultados para a dashboard imediatamente
    - Roda como conta SYSTEM para rodar em background
    - Reinicia automaticamente em caso de falha
#>

$ErrorActionPreference = "Stop"

# ========================================
# Configurações
# ========================================
$taskName = "KatalonRealtimeWatcher"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir
$venvPython = Join-Path $ProjectDir ".venv\Scripts\python.exe"
$watcherScript = Join-Path $ScriptDir "watch_reports.py"

# Verificar se o script existe
if (-not (Test-Path $watcherScript)) {
    Write-Host "ERRO: Script não encontrado: $watcherScript" -ForegroundColor Red
    exit 1
}

# Verificar Python do venv
if (-not (Test-Path $venvPython)) {
    Write-Host "ERRO: Python do venv não encontrado: $venvPython" -ForegroundColor Red
    exit 1
}

# ========================================
# Verificar privilégios de Administrador
# ========================================
$currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
$adminRole = [Security.Principal.WindowsBuiltInRole]::Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] $currentUser).IsInRole($adminRole)

if (-not $isAdmin) {
    Write-Host "ERRO: Este script precisa ser executado como Administrador." -ForegroundColor Red
    Write-Host ""
    Write-Host "Para executar como Administrador:" -ForegroundColor Yellow
    Write-Host "  1. Clique com o botão direito no PowerShell" -ForegroundColor White
    Write-Host "  2. Selecione 'Executar como Administrador'" -ForegroundColor White
    Write-Host "  3. Navegue até a pasta e execute novamente:" -ForegroundColor White
    Write-Host "     .\install_watcher.ps1" -ForegroundColor Cyan
    exit 1
}

# ========================================
# Exibir informações
# ========================================
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  INSTALAR WATCHER - REPORTS KATALON" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Configurações:" -ForegroundColor White
Write-Host "  Nome da Tarefa: $taskName" -ForegroundColor Gray
Write-Host "  Script: $watcherScript" -ForegroundColor Gray
Write-Host "  Diretório de Trabalho: $ScriptDir" -ForegroundColor Gray
Write-Host ""

# ========================================
# Remover tarefa existente se houver
# ========================================
try {
    $existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($existingTask) {
        Write-Host "Removendo tarefa existente: $taskName" -ForegroundColor Gray
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    }
} catch {
    # Tarefa não existe, continuar
}

# ========================================
# Criar tarefa agendada
# ========================================
$action = New-ScheduledTaskAction `
    -Execute $venvPython `
    -Argument "`"$watcherScript`"" `
    -WorkingDirectory $ScriptDir

$trigger = New-ScheduledTaskTrigger -AtStartup

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -DontStopOnIdleEnd `
    -RestartInterval (New-TimeSpan -Minutes 5) `
    -RestartCount 3 `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -MultipleInstances IgnoreNew

$principal = New-ScheduledTaskPrincipal `
    -UserId "SYSTEM" `
    -LogonType ServiceAccount `
    -RunLevel Highest

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Force | Out-Null

Write-Host "OK: Tarefa criada com sucesso!" -ForegroundColor Green

# ========================================
# Iniciar a tarefa agora
# ========================================
try {
    Start-ScheduledTask -TaskName $taskName
    Write-Host "OK: Tarefa iniciada!" -ForegroundColor Green
} catch {
    Write-Host "AVISO: Não foi possível iniciar a tarefa automaticamente." -ForegroundColor Yellow
    Write-Host "Você pode iniciar manualmente no Task Scheduler ou reiniciar o computador." -ForegroundColor Gray
}

# ========================================
# Resumo
# ========================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  INSTALAÇÃO CONCLUÍDA!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "A tarefa '$taskName' foi criada e iniciada." -ForegroundColor White
Write-Host ""
Write-Host "O que a tarefa faz:" -ForegroundColor Yellow
Write-Host "  - Inicia automaticamente quando o computador ligar" -ForegroundColor White
Write-Host "  - Monitora E:\Pipeline-Report em tempo real" -ForegroundColor White
Write-Host "  - Envia novos JUnit_Report.xml para a dashboard na hora" -ForegroundColor White
Write-Host "  - Reinicia sozinha em caso de falha (a cada 5 min, até 3 vezes)" -ForegroundColor White
Write-Host ""
Write-Host "Para gerenciar a tarefa:" -ForegroundColor Yellow
Write-Host "  - Abrir Task Scheduler: taskschd.msc" -ForegroundColor White
Write-Host "  - Navegar até: Biblioteca do Agendador de Tarefas" -ForegroundColor White
Write-Host "  - Localizar a tarefa: $taskName" -ForegroundColor White
Write-Host ""
Write-Host "Logs:" -ForegroundColor Yellow
Write-Host "  - Watcher: $ScriptDir\watcher.log" -ForegroundColor Gray
Write-Host "  - Parse: $ScriptDir\sync.log" -ForegroundColor Gray
Write-Host ""

try {
    $taskStatus = Get-ScheduledTask -TaskName $taskName | Select-Object TaskName, State, LastRunTime
    Write-Host "Status atual da tarefa:" -ForegroundColor White
    $taskStatus | Format-Table -AutoSize | Out-Host
} catch {
    Write-Host "Não foi possível obter o status da tarefa." -ForegroundColor Gray
}
