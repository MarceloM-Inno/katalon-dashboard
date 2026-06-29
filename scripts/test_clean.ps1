<#
.SYNOPSIS
    Testa o Parser com Cache Limpo
.DESCRIPTION
    Este script:
    1. Limpa variaveis de ambiente do PowerShell (SUPABASE_*)
    2. Carrega o .env da raiz
    3. Executa o parse_manual_csv.py
    - Usar este script para garantir que a Service Role Key seja usada
.PARAMETER CsvPath
    Caminho completo para o arquivo CSV
.EXAMPLE
    .\test_clean.ps1 "C:\Users\mmmorais\Downloads\Lista Testes All Projects (Oney Bank) 2026-05-25T09_13_22+0100.csv"
#>

param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$CsvPath
)

$ErrorActionPreference = "Stop"

Write-Host "" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  TESTE COM CACHE LIMPO" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "" -ForegroundColor White

# ========================================
# Configuracoes
# ========================================
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ParentDir = Split-Path -Parent $ScriptDir
$EnvFile = Join-Path $ParentDir ".env"
$ParserScript = Join-Path $ScriptDir "parse_manual_csv.py"

# ========================================
# 1. Limpar Cache de Variaveis de Ambiente
# ========================================
Write-Host "[1/4] Limpando cache de variaveis..." -ForegroundColor Yellow

# Limpar variaveis da sessao atual
$varsToClear = @("SUPABASE_URL", "SUPABASE_KEY", "MANUAL_REPORT_PATH", "MANUAL_PROJECT_MAP")

foreach ($var in $varsToClear) {
    if (Test-Path "env:$var") {
        Remove-Item "env:$var" -Force
        Write-Host "  [OK] Limpado: env:$var" -ForegroundColor Green
    } else {
        Write-Host "  [OK] Nao existia: env:$var" -ForegroundColor Gray
    }
}

# ========================================
# 2. Verificar .env
# ========================================
Write-Host "" -ForegroundColor White
Write-Host "[2/4] Verificando arquivo .env..." -ForegroundColor Yellow

if (-not (Test-Path $EnvFile)) {
    Write-Host "  [ERRO] .env nao encontrado em: $EnvFile" -ForegroundColor Red
    exit 1
}

Write-Host "  [OK] .env encontrado: $EnvFile" -ForegroundColor Green

# Ler e verificar a chave
$envContent = Get-Content $EnvFile -Raw

# Procurar SUPABASE_KEY nao comentada
$keyMatch = [regex]::Match($envContent, '(?m)^SUPABASE_KEY\s*=\s*(\S+)')
if ($keyMatch.Success) {
    $foundKey = $keyMatch.Groups[1].Value
    Write-Host "" -ForegroundColor White
    Write-Host "  Chave encontrada (primeiros 20 caracteres):" -ForegroundColor Gray
    Write-Host "  $($foundKey.Substring(0, [Math]::Min(20, $foundKey.Length)))..." -ForegroundColor Gray
    
    if ($foundKey.StartsWith("eyJ")) {
        Write-Host "  [OK] Parece ser Service Role Key (comeca com eyJ...)" -ForegroundColor Green
    } elseif ($foundKey.StartsWith("sb_publishable")) {
        Write-Host "  [ERRO] Chave e Anon Key (sb_publishable__). Nao funciona para insercao!" -ForegroundColor Red
        Write-Host "" -ForegroundColor White
        Write-Host "  Solucao:" -ForegroundColor Yellow
        Write-Host "    1. Acesse o Supabase Dashboard" -ForegroundColor White
        Write-Host "    2. Settings -> API -> Revele a chave 'service_role'" -ForegroundColor White
        Write-Host "    3. Atualize o .env com a Service Role Key" -ForegroundColor White
        exit 1
    } else {
        Write-Host "  [AVISO] Formato de chave desconhecido" -ForegroundColor Yellow
    }
} else {
    Write-Host "  [ERRO] Nao foi possivel encontrar SUPABASE_KEY no .env" -ForegroundColor Red
    exit 1
}

# ========================================
# 3. Verificar Scripts
# ========================================
Write-Host "" -ForegroundColor White
Write-Host "[3/4] Verificando scripts..." -ForegroundColor Yellow

if (-not (Test-Path $ParserScript)) {
    Write-Host "  [ERRO] Script nao encontrado: $ParserScript" -ForegroundColor Red
    exit 1
}
Write-Host "  [OK] Parser encontrado" -ForegroundColor Green

if (-not (Test-Path $CsvPath)) {
    Write-Host "  [ERRO] CSV nao encontrado: $CsvPath" -ForegroundColor Red
    exit 1
}
Write-Host "  [OK] CSV encontrado" -ForegroundColor Green

# ========================================
# 4. Executar Teste
# ========================================
Write-Host "" -ForegroundColor White
Write-Host "[4/4] Executando teste..." -ForegroundColor Yellow
Write-Host "" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SAIDA DO PARSER" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "" -ForegroundColor White

try {
    # Mudar para o diretorio do parser para garantir que o .env seja carregado corretamente
    Push-Location $ScriptDir
    
    # Executar o parser
    & python $ParserScript $CsvPath
    
    $exitCode = $LASTEXITCODE
    
    Write-Host "" -ForegroundColor White
    Write-Host "========================================" -ForegroundColor Cyan
    
    if ($exitCode -eq 0) {
        Write-Host "  SUCESSO!" -ForegroundColor Green
    } else {
        Write-Host "  Codigo de saida: $exitCode" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "" -ForegroundColor White
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "  ERRO NA EXECUCAO" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "" -ForegroundColor White
    Write-Host "  $($_.Exception.Message)" -ForegroundColor Red
} finally {
    Pop-Location
}

Write-Host "" -ForegroundColor White
