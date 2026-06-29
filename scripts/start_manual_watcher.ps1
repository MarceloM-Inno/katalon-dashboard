<#
.SYNOPSIS
    Inicia o Watcher de Testes Manuais
.DESCRIPTION
    Monitora a pasta configurada em MANUAL_REPORT_PATH para novos arquivos CSV
    e processa automaticamente usando o parse_manual_csv.py
.PARAMETER ReportPath
    (Opcional) Caminho para a pasta de relatorios. Se nao for fornecido,
    usa o valor do .env ou o padrao: C:\Users\mmmorais\Downloads
.PARAMETER NoAutoScan
    (Opcional) Se especificado, nao verifica arquivos existentes na inicializacao
.EXAMPLE
    .\start_manual_watcher.ps1
.EXAMPLE
    .\start_manual_watcher.ps1 -ReportPath "C:\Users\mmmorais\Downloads"
#>

param(
    [string]$ReportPath = "",
    [switch]$NoAutoScan
)

$ErrorActionPreference = "Stop"

# ========================================
# Configuracoes
# ========================================
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ParentDir = Split-Path -Parent $ScriptDir
$WatcherScript = Join-Path $ScriptDir "watch_manual_reports.py"
$LogFile = Join-Path $ScriptDir "watcher_manual.log"

# ========================================
# Funcao para carregar .env
# ========================================
function Get-EnvVariable {
    param([string]$Key)
    
    # Primeiro, verificar variaveis de ambiente do sistema
    $envValue = [Environment]::GetEnvironmentVariable($Key, "Process")
    if ($envValue) { return $envValue }
    
    $envValue = [Environment]::GetEnvironmentVariable($Key, "User")
    if ($envValue) { return $envValue }
    
    $envValue = [Environment]::GetEnvironmentVariable($Key, "Machine")
    if ($envValue) { return $envValue }
    
    # Depois, tentar ler do arquivo .env
    $envFile = Join-Path $ParentDir ".env"
    if (Test-Path $envFile) {
        $content = Get-Content $envFile -Raw
        $pattern = "(?m)^$Key\s*=\s*(.*?)\s*$"
        $match = [regex]::Match($content, $pattern)
        if ($match.Success) {
            return $match.Groups[1].Value.Trim()
        }
    }
    
    return $null
}

# ========================================
# Exibir Cabecalho
# ========================================
Write-Host "" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  WATCHER DE TESTES MANUAIS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "" -ForegroundColor White

# ========================================
# Verificar Arquivos
# ========================================
Write-Host "[1/4] Verificando arquivos..." -ForegroundColor Yellow

# Verificar script do watcher
if (-not (Test-Path $WatcherScript)) {
    Write-Host "  ERRO: Script nao encontrado: $WatcherScript" -ForegroundColor Red
    Write-Host "  Verifique se todos os arquivos da pasta 'scripts' foram copiados." -ForegroundColor Yellow
    exit 1
}
Write-Host "  OK: Watcher encontrado" -ForegroundColor Green

# ========================================
# Determinar Caminho da Pasta
# ========================================
Write-Host "" -ForegroundColor White
Write-Host "[2/4] Determinando pasta de monitoramento..." -ForegroundColor Yellow

$finalPath = $ReportPath

# Se nao foi fornecido por parametro, tentar outras fontes
if ([string]::IsNullOrEmpty($finalPath)) {
    $finalPath = Get-EnvVariable "MANUAL_REPORT_PATH"
}

# Se ainda nao tiver, usar padrao
if ([string]::IsNullOrEmpty($finalPath)) {
    $finalPath = "C:\Users\mmmorais\Downloads"
    Write-Host "  AVISO: Usando caminho padrao: $finalPath" -ForegroundColor Yellow
} else {
    Write-Host "  OK: Caminho definido: $finalPath" -ForegroundColor Green
}

# Verificar se a pasta existe
if (-not (Test-Path $finalPath)) {
    Write-Host "  AVISO: Pasta nao existe: $finalPath" -ForegroundColor Yellow
    Write-Host "         O watcher tentara criar as subpastas (_processed, _error, _unmatched) automaticamente." -ForegroundColor Gray
    
    $create = Read-Host "Deseja continuar mesmo assim? (S/N)"
    if ($create -ne "S" -and $create -ne "s") {
        Write-Host "Operacao cancelada." -ForegroundColor Yellow
        exit 0
    }
} else {
    Write-Host "  OK: Pasta existe" -ForegroundColor Green
}

# ========================================
# Verificar Python
# ========================================
Write-Host "" -ForegroundColor White
Write-Host "[3/4] Verificando Python..." -ForegroundColor Yellow

try {
    $pythonVersion = python --version 2>&1
    Write-Host "  OK: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ERRO: Python nao encontrado no PATH" -ForegroundColor Red
    Write-Host "  Instale o Python 3.11+ e adicione ao PATH do sistema." -ForegroundColor Yellow
    exit 1
}

# ========================================
# Iniciar Watcher
# ========================================
Write-Host "" -ForegroundColor White
Write-Host "[4/4] Preparando para iniciar..." -ForegroundColor Yellow
Write-Host "" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  INICIANDO WATCHER" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "" -ForegroundColor White
Write-Host "Monitorando: $finalPath" -ForegroundColor Gray
Write-Host "Logs: $LogFile" -ForegroundColor Gray
Write-Host "" -ForegroundColor White
Write-Host "Tipos suportados:" -ForegroundColor White
Write-Host "  - Lista Testes All Projects" -ForegroundColor Gray
Write-Host "  - Defects All Projects" -ForegroundColor Gray
Write-Host "  - FillAutoDefects" -ForegroundColor Gray
Write-Host "" -ForegroundColor White
Write-Host "Pressione Ctrl+C para parar." -ForegroundColor Yellow
Write-Host "" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "" -ForegroundColor White

try {
    # Definir variavel de ambiente para o watcher
    if (-not [string]::IsNullOrEmpty($finalPath)) {
        $env:MANUAL_REPORT_PATH = $finalPath
    }
    
    # Executar o watcher
    & python $WatcherScript
    
} catch {
    Write-Host "" -ForegroundColor White
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "  ERRO NA EXECUCAO" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "" -ForegroundColor White
    Write-Host "  Mensagem: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "" -ForegroundColor White
    
    Write-Host "  Verificacoes recomendadas:" -ForegroundColor Yellow
    Write-Host "    1. .env existe em $ParentDir ?" -ForegroundColor White
    Write-Host "    2. Service Role Key esta correta?" -ForegroundColor White
    Write-Host "    3. Pasta $finalPath existe e tem permissoes de leitura?" -ForegroundColor White
    Write-Host "" -ForegroundColor White
}

Write-Host "" -ForegroundColor White
Write-Host "Watcher finalizado." -ForegroundColor Yellow
Write-Host "" -ForegroundColor White
