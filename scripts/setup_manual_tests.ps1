<#
.SYNOPSIS
    Script de setup para Testes Manuais na VM02
.DESCRIPTION
    Configura o ambiente para processar CSVs de testes manuais:
    - Cria arquivo .env com credenciais
    - Instala dependências Python
    - Configura caminhos padrão
#>

param(
    [string]$ReportPath = "C:\Users\mmmorais\Downloads",
    [string]$ProjectName = "BNPL"
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SETUP - TESTES MANUAIS (VM02)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ========================================
# Verificar Python
# ========================================
Write-Host "[1/4] Verificando Python..." -ForegroundColor Yellow

try {
    $pythonVersion = python --version 2>&1
    Write-Host "  OK: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ERRO: Python não encontrado no PATH" -ForegroundColor Red
    Write-Host "  Instale o Python 3.11+ e adicione ao PATH" -ForegroundColor Red
    exit 1
}

# ========================================
# Determinar diretórios
# ========================================
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ParentDir = Split-Path -Parent $ScriptDir

Write-Host ""
Write-Host "[INFO] Diretório do script: $ScriptDir" -ForegroundColor Gray
Write-Host "[INFO] Diretório pai: $ParentDir" -ForegroundColor Gray

# ========================================
# Criar arquivo .env
# ========================================
Write-Host ""
Write-Host "[2/4] Criando arquivo .env..." -ForegroundColor Yellow

$envContent = @"
# ========================================
# Credenciais do Supabase
# ========================================
SUPABASE_URL=https://rodqhwzivsnxkfdenirx.supabase.co
SUPABASE_KEY=sb_publishable__UKuJOVkh4JFKLwRgEaNlg_PAYBNjOH

# ========================================
# Parser Automatizado (Katalon XML)
# ========================================
REPORT_PATH=E:\Pipeline-Report
PROJECT_NAME=$ProjectName

# ========================================
# Testes Manuais (CSV)
# ========================================
# Caminho onde o Katalon salva os CSVs
MANUAL_REPORT_PATH=$ReportPath

# Mapeamento de nomes no arquivo para projeto
# Formato: {"Nome no Arquivo": "Código no Banco"}
MANUAL_PROJECT_MAP={"Oney Bank": "ONEY", "BNPL": "BNPL"}
"@

# Criar .env na pasta scripts (para facilitar)
$envScriptPath = Join-Path $ScriptDir ".env"
$envContent | Out-File -FilePath $envScriptPath -Encoding utf8
Write-Host "  OK: Criado $envScriptPath" -ForegroundColor Green

# Também criar no diretório pai (se existir) para compatibilidade
if (Test-Path $ParentDir) {
    $envParentPath = Join-Path $ParentDir ".env"
    if (-not (Test-Path $envParentPath)) {
        $envContent | Out-File -FilePath $envParentPath -Encoding utf8
        Write-Host "  OK: Criado $envParentPath" -ForegroundColor Green
    } else {
        Write-Host "  AVISO: .env já existe em $ParentDir (não sobrescrito)" -ForegroundColor Yellow
    }
}

# ========================================
# Instalar dependências
# ========================================
Write-Host ""
Write-Host "[3/4] Instalando dependências Python..." -ForegroundColor Yellow

$requirementsPath = Join-Path $ScriptDir "requirements.txt"

if (Test-Path $requirementsPath) {
    Write-Host "  Instalando de: $requirementsPath" -ForegroundColor Gray
    
    try {
        python -m pip install --upgrade pip 2>&1 | Out-Null
        python -m pip install -r $requirementsPath 2>&1
        Write-Host "  OK: Dependências instaladas" -ForegroundColor Green
    } catch {
        Write-Host "  AVISO: Erro ao instalar algumas dependências" -ForegroundColor Yellow
        Write-Host "  Tentando instalar pacotes essenciais individualmente..." -ForegroundColor Gray
        
        $packages = @("requests", "python-dotenv", "pandas", "watchdog")
        foreach ($pkg in $packages) {
            try {
                python -m pip install $pkg 2>&1 | Out-Null
                Write-Host "    OK: $pkg" -ForegroundColor Green
            } catch {
                Write-Host "    ERRO: $pkg" -ForegroundColor Red
            }
        }
    }
} else {
    Write-Host "  AVISO: requirements.txt não encontrado em $ScriptDir" -ForegroundColor Yellow
    Write-Host "  Instalando pacotes essenciais..." -ForegroundColor Gray
    
    $packages = @("requests", "python-dotenv", "pandas", "watchdog")
    foreach ($pkg in $packages) {
        try {
            python -m pip install $pkg 2>&1 | Out-Null
            Write-Host "    OK: $pkg" -ForegroundColor Green
        } catch {
            Write-Host "    ERRO: $pkg" -ForegroundColor Red
        }
    }
}

# ========================================
# Verificar pasta de relatórios
# ========================================
Write-Host ""
Write-Host "[4/4] Verificando pasta de relatórios..." -ForegroundColor Yellow

if (Test-Path $ReportPath) {
    Write-Host "  OK: Pasta existe: $ReportPath" -ForegroundColor Green
} else {
    Write-Host "  AVISO: Pasta não encontrada: $ReportPath" -ForegroundColor Yellow
    Write-Host "  O watcher criará as subpastas (_processed, _error, _unmatched) automaticamente" -ForegroundColor Gray
}

# ========================================
# Resumo
# ========================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SETUP CONCLUÍDO!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Configurações atuais:" -ForegroundColor White
Write-Host "  MANUAL_REPORT_PATH: $ReportPath" -ForegroundColor Gray
Write-Host "  PROJECT_NAME: $ProjectName" -ForegroundColor Gray
Write-Host "  SUPABASE_URL: https://rodqhwzivsnxkfdenirx.supabase.co" -ForegroundColor Gray
Write-Host ""
Write-Host "Próximos passos:" -ForegroundColor Yellow
Write-Host "  1. Teste o parser: .\test_manual_parser.bat `"C:\caminho\para\seu\arquivo.csv`"" -ForegroundColor White
Write-Host "  2. Instale o watcher: .\install_manual_watcher.ps1 (como Administrador)" -ForegroundColor White
Write-Host ""
Write-Host "Arquivos criados/atualizados:" -ForegroundColor Gray
Write-Host "  - $envScriptPath" -ForegroundColor Gray
if (Test-Path $envParentPath) {
    Write-Host "  - $envParentPath" -ForegroundColor Gray
}
Write-Host ""
