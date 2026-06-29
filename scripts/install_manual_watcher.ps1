<#
.SYNOPSIS
    Instala o Watcher de Testes Manuais como Tarefa Agendada
.DESCRIPTION
    Cria uma tarefa no Windows Task Scheduler que:
    - Executa automaticamente na inicialização do sistema
    - Monitora a pasta de CSVs de testes manuais
    - Roda como conta SYSTEM para rodar em background
#>

$ErrorActionPreference = "Stop"

# ========================================
# Configurações
# ========================================
$taskName = "KatalonManualTestsWatcher"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ParentDir = Split-Path -Parent $ScriptDir

# Script a ser executado
$watcherScript = Join-Path $ScriptDir "watch_manual_reports.py"

# Verificar se o script existe
if (-not (Test-Path $watcherScript)) {
    Write-Host "ERRO: Script não encontrado: $watcherScript" -ForegroundColor Red
    Write-Host "Verifique se todos os arquivos da pasta 'scripts' foram copiados." -ForegroundColor Yellow
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
    Write-Host "" -ForegroundColor White
    Write-Host "Para executar como Administrador:" -ForegroundColor Yellow
    Write-Host "  1. Clique com o botão direito no PowerShell" -ForegroundColor White
    Write-Host "  2. Selecione 'Executar como Administrador'" -ForegroundColor White
    Write-Host "  3. Navegue até a pasta e execute novamente:" -ForegroundColor White
    Write-Host "     .\install_manual_watcher.ps1" -ForegroundColor Cyan
    exit 1
}

# ========================================
# Exibir informações
# ========================================
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  INSTALAR WATCHER - TESTES MANUAIS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Configurações:" -ForegroundColor White
Write-Host "  Nome da Tarefa: $taskName" -ForegroundColor Gray
Write-Host "  Script: $watcherScript" -ForegroundColor Gray
Write-Host "  Diretório de Trabalho: $ScriptDir" -ForegroundColor Gray
Write-Host ""

# ========================================
# Verificar Python
# ========================================
Write-Host "[1/3] Verificando Python..." -ForegroundColor Yellow

try {
    $pythonCmd = Get-Command python -ErrorAction Stop
    $pythonExe = $pythonCmd.Source
    Write-Host "  OK: Python encontrado em: $pythonExe" -ForegroundColor Green
} catch {
    Write-Host "  ERRO: Python não encontrado no PATH do sistema" -ForegroundColor Red
    Write-Host "  O watcher instalado como SYSTEM pode não encontrar o Python." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Para resolver:" -ForegroundColor White
    Write-Host "  1. Instale Python para todos os usuários (Install for all users)" -ForegroundColor White
    Write-Host "  2. Ou adicione o Python ao PATH do sistema (não apenas do usuário)" -ForegroundColor White
    Write-Host ""
    
    $confirm = Read-Host "Deseja continuar mesmo assim? (S/N)"
    if ($confirm -ne "S" -and $confirm -ne "s") {
        Write-Host "Instalação cancelada." -ForegroundColor Yellow
        exit 0
    }
    
    $pythonExe = "python"
}

# ========================================
# Criar tarefa agendada
# ========================================
Write-Host ""
Write-Host "[2/3] Criando tarefa agendada..." -ForegroundColor Yellow

# Remover tarefa existente se houver
try {
    $existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($existingTask) {
        Write-Host "  Removendo tarefa existente: $taskName" -ForegroundColor Gray
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    }
} catch {
    # Tarefa não existe, continuar
}

# Criar ação: executar o script
# O watcher é um script que roda continuamente, então não precisa de argumentos complexos
$action = New-ScheduledTaskAction `
    -Execute $pythonExe `
    -Argument "`"$watcherScript`"" `
    -WorkingDirectory $ScriptDir

# Criar trigger: executar na inicialização do sistema
$trigger = New-ScheduledTaskTrigger -AtStartup

# Configurações:
# - Permitir início se o computador estiver na bateria
# - Não parar se mudar para bateria
# - Iniciar quando possível se perder o horário
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -DontStopOnIdleEnd `
    -RestartInterval (New-TimeSpan -Minutes 5) `
    -RestartCount 3

# Principal: rodar como SYSTEM (serviço) com privilégios elevados
$principal = New-ScheduledTaskPrincipal `
    -UserId "SYSTEM" `
    -LogonType ServiceAccount `
    -RunLevel Highest

# Registrar a tarefa
Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Force | Out-Null

Write-Host "  OK: Tarefa criada com sucesso!" -ForegroundColor Green

# ========================================
# Iniciar a tarefa agora
# ========================================
Write-Host ""
Write-Host "[3/3] Iniciando o watcher..." -ForegroundColor Yellow

try {
    Start-ScheduledTask -TaskName $taskName
    Write-Host "  OK: Tarefa iniciada!" -ForegroundColor Green
} catch {
    Write-Host "  AVISO: Não foi possível iniciar a tarefa automaticamente." -ForegroundColor Yellow
    Write-Host "  Você pode iniciar manualmente no Task Scheduler ou reiniciar o computador." -ForegroundColor Gray
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
Write-Host "  - Monitora a pasta configurada em MANUAL_REPORT_PATH" -ForegroundColor White
Write-Host "  - Processa novos CSVs automaticamente" -ForegroundColor White
Write-Host "  - Move arquivos processados para subpastas (_processed, _error, _unmatched)" -ForegroundColor White
Write-Host ""
Write-Host "Para gerenciar a tarefa:" -ForegroundColor Yellow
Write-Host "  - Abrir Task Scheduler: taskschd.msc" -ForegroundColor White
Write-Host "  - Navegar até: Biblioteca do Agendador de Tarefas" -ForegroundColor White
Write-Host "  - Localizar a tarefa: $taskName" -ForegroundColor White
Write-Host ""
Write-Host "Logs:" -ForegroundColor Yellow
Write-Host "  - Watcher: $ScriptDir\watcher_manual.log" -ForegroundColor Gray
Write-Host "  - Estado: $ScriptDir\manual_processed_state.json" -ForegroundColor Gray
Write-Host ""

# Exibir status da tarefa
try {
    $taskStatus = Get-ScheduledTask -TaskName $taskName | Select-Object TaskName, State, LastRunTime
    Write-Host "Status atual da tarefa:" -ForegroundColor White
    $taskStatus | Format-Table -AutoSize | Out-Host
} catch {
    Write-Host "Não foi possível obter o status da tarefa." -ForegroundColor Gray
}
