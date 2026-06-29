<#
.SYNOPSIS
    Atualiza o arquivo .env com a Service Role Key correta
.DESCRIPTION
    Este script deve ser executado na VM02 para garantir que:
    - A Service Role Key esta configurada (nao a Anon Key)
    - Todas as variaveis necessarias estao definidas
.PARAMETER Force
    Se especificado, sobrescreve o .env existente sem pedir confirmacao
.EXAMPLE
    .\update_env_vm02.ps1
.EXAMPLE
    .\update_env_vm02.ps1 -Force
#>

param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"

# ========================================
# Configuracoes - EDITE AQUI SE PRECISAR
# ========================================

# Service Role Key (copiada do Supabase Dashboard)
$SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJvZHFod3ppdnNueGtmZGVuaXJ4Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3OTM2NTM0NywiZXhwIjoyMDk0OTQxMzQ3fQ.lsNs0OwNPPz9u1YuHP368QfgAeE8vzW9pVulIFKOEAU"

# URL do Supabase
$SUPABASE_URL = "https://rodqhwzivsnxkfdenirx.supabase.co"

# Caminho onde o Katalon salva os CSVs na VM02
$MANUAL_REPORT_PATH = "C:\Users\mmmorais\Downloads"

# Mapeamento de projetos
$MANUAL_PROJECT_MAP = '{"Oney Bank": "ONEY", "BNPL": "BNPL"}'

# Configuracoes para parser automatizado (Katalon XML)
$REPORT_PATH = "E:\Pipeline-Report"
$PROJECT_NAME = "BNPL"  # Mude para "ONEY" se for o projeto ONEY

# ========================================
# Fim das Configuracoes
# ========================================

Write-Host "" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ATUALIZAR .env - VM02" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "" -ForegroundColor White

# ========================================
# Determinar local do .env
# ========================================
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ParentDir = Split-Path -Parent $ScriptDir

# Prioridade: .env na raiz (recomendado)
$EnvFile = Join-Path $ParentDir ".env"

# Se a raiz nao existir, usar a pasta scripts
if (-not (Test-Path $ParentDir)) {
    $EnvFile = Join-Path $ScriptDir ".env"
    Write-Host "[AVISO] Usando .env na pasta scripts" -ForegroundColor Yellow
} else {
    Write-Host "[INFO] .env sera criado/atualizado em: $EnvFile" -ForegroundColor Gray
}

# ========================================
# Verificar se .env ja existe
# ========================================
$envExists = Test-Path $EnvFile

if ($envExists -and -not $Force) {
    Write-Host "" -ForegroundColor White
    Write-Host "[AVISO] Arquivo .env ja existe:" -ForegroundColor Yellow
    Write-Host "         $EnvFile" -ForegroundColor Gray
    Write-Host "" -ForegroundColor White
    
    $confirm = Read-Host "Deseja sobrescrever? (S/N)"
    if ($confirm -ne "S" -and $confirm -ne "s") {
        Write-Host "" -ForegroundColor White
        Write-Host "Operacao cancelada." -ForegroundColor Yellow
        Write-Host "" -ForegroundColor White
        exit 0
    }
}

# ========================================
# Criar conteudo do .env
# ========================================
$envContent = @"
# ========================================
# Credenciais do Supabase
# ========================================
# IMPORTANTE: Use a SERVICE ROLE KEY para scripts de backend
# - Ela ignora o Row-Level Security (RLS)
# - Tem todas as permissoes de leitura e escrita
#
# Onde encontrar: Supabase Dashboard → Settings → API → service_role (Reveal)

SUPABASE_URL=$SUPABASE_URL

# SERVICE ROLE KEY (use esta)
SUPABASE_KEY=$SUPABASE_KEY

# ========================================
# Parser Automatizado (Katalon XML)
# ========================================
# Para testes automatizados com XML do Katalon

REPORT_PATH=$REPORT_PATH
PROJECT_NAME=$PROJECT_NAME

# ========================================
# Testes Manuais (CSV)
# ========================================
# Caminho onde o Katalon salva os CSVs de testes manuais
# Este e o caminho da pasta Downloads do usuario que executa o Katalon na VM02

MANUAL_REPORT_PATH=$MANUAL_REPORT_PATH

# Mapeamento de nomes no arquivo para projeto
# 
# Os arquivos CSV tem padrao:
#   - Lista Testes All Projects (Oney Bank) data.csv
#   - Lista Testes All Projects (BNPL) data.csv
# 
# Este JSON mapeia o nome entre parenteses para um codigo no banco:
#   - "Oney Bank" -> "ONEY"
#   - "BNPL" -> "BNPL"

MANUAL_PROJECT_MAP=$MANUAL_PROJECT_MAP

# ========================================
# Chave Antiga (Anon Key) - NAO USE
# ========================================
# Esta chave e limitada pelo RLS e nao funciona para insercao
# em tabelas sem politicas de seguranca configuradas
#
# SUPABASE_KEY=sb_publishable__UKuJOVkh4JFKLwRgEaNlg_PAYBNjOH
"@

# ========================================
# Salvar arquivo
# ========================================
Write-Host "" -ForegroundColor White
Write-Host "[INFO] Salvando .env..." -ForegroundColor Yellow

try {
    # Garantir que o diretorio existe
    $envDir = Split-Path -Parent $EnvFile
    if (-not (Test-Path $envDir)) {
        New-Item -ItemType Directory -Path $envDir -Force | Out-Null
    }
    
    # Salvar com UTF-8 sem BOM
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($EnvFile, $envContent, $utf8NoBom)
    
    Write-Host "[OK] .env salvo em: $EnvFile" -ForegroundColor Green
    
} catch {
    Write-Host "" -ForegroundColor White
    Write-Host "[ERRO] Nao foi possivel salvar o .env:" -ForegroundColor Red
    Write-Host "       $($_.Exception.Message)" -ForegroundColor White
    Write-Host "" -ForegroundColor White
    exit 1
}

# ========================================
# Verificacao
# ========================================
Write-Host "" -ForegroundColor White
Write-Host "[INFO] Verificando conteudo..." -ForegroundColor Yellow

if (Test-Path $EnvFile) {
    $content = Get-Content $EnvFile -Raw
    
    if ($content -match "SUPABASE_KEY\s*=\s*eyJ") {
        Write-Host "[OK] Service Role Key detectada (comeca com eyJ...)" -ForegroundColor Green
    } else {
        Write-Host "[AVISO] Nao foi possivel verificar a chave" -ForegroundColor Yellow
    }
    
    if ($content -match "MANUAL_REPORT_PATH") {
        Write-Host "[OK] MANUAL_REPORT_PATH definido" -ForegroundColor Green
    }
    
    if ($content -match "MANUAL_PROJECT_MAP") {
        Write-Host "[OK] MANUAL_PROJECT_MAP definido" -ForegroundColor Green
    }
}

# ========================================
# Resumo
# ========================================
Write-Host "" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  CONFIGURACAO CONCLUIDA!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "" -ForegroundColor White

Write-Host "Arquivo criado/atualizado:" -ForegroundColor White
Write-Host "  $EnvFile" -ForegroundColor Gray
Write-Host "" -ForegroundColor White

Write-Host "Configuracoes:" -ForegroundColor White
Write-Host "  SUPABASE_URL: $SUPABASE_URL" -ForegroundColor Gray
Write-Host "  MANUAL_REPORT_PATH: $MANUAL_REPORT_PATH" -ForegroundColor Gray
Write-Host "  PROJECT_NAME: $PROJECT_NAME" -ForegroundColor Gray
Write-Host "" -ForegroundColor White

Write-Host "Proximos passos:" -ForegroundColor Yellow
Write-Host "  1. Reinicie o PowerShell/terminal para limpar cache" -ForegroundColor White
Write-Host "  2. Teste o parser: .\test_manual_parser.ps1 `"caminho\para\arquivo.csv`"" -ForegroundColor Gray
Write-Host "  3. Instale o watcher: .\install_manual_watcher.ps1 (como Admin)" -ForegroundColor Gray
Write-Host "" -ForegroundColor White

if (-not $Force) {
    Write-Host "Pressione Enter para sair..." -ForegroundColor Gray
    Read-Host | Out-Null
}
