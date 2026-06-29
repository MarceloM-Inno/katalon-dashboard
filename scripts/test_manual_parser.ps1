<#
.SYNOPSIS
    Testa o Parser de Testes Manuais
.DESCRIPTION
    Executa o parse_manual_csv.py com tratamento para nomes de arquivos complexos
    (com espacos, parenteses, caracteres especiais)
.PARAMETER CsvPath
    Caminho completo para o arquivo CSV a ser processado
.EXAMPLE
    .\test_manual_parser.ps1 "C:\Users\mmmorais\Downloads\Lista Testes All Projects (Oney Bank) 2026-05-25T09_13_22+0100.csv"
#>

param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$CsvPath
)

$ErrorActionPreference = "Stop"

# ========================================
# Configuracoes
# ========================================
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ParentDir = Split-Path -Parent $ScriptDir
$ParserScript = Join-Path $ScriptDir "parse_manual_csv.py"

# ========================================
# Exibir Informacoes
# ========================================
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  TESTAR PARSER - TESTES MANUAIS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ========================================
# Verificar Arquivos
# ========================================
Write-Host "[1/4] Verificando arquivos..." -ForegroundColor Yellow

# Verificar script do parser
if (-not (Test-Path $ParserScript)) {
    Write-Host "  ERRO: Script nao encontrado: $ParserScript" -ForegroundColor Red
    Write-Host "  Verifique se todos os arquivos da pasta 'scripts' foram copiados." -ForegroundColor Yellow
    exit 1
}
Write-Host "  OK: Parser encontrado" -ForegroundColor Green

# Verificar arquivo CSV
if (-not (Test-Path $CsvPath)) {
    Write-Host "  ERRO: Arquivo CSV nao encontrado: $CsvPath" -ForegroundColor Red
    
    # Tentar encontrar na pasta padrao
    $defaultPath = "C:\Users\mmmorais\Downloads"
    if (Test-Path $defaultPath) {
        $csvFiles = Get-ChildItem -Path $defaultPath -Filter "*.csv" -File | 
                    Where-Object { $_.Name -like "*Lista Testes*" -or $_.Name -like "*Defects*" -or $_.Name -like "*FillAutoDefects*" }
        
        if ($csvFiles) {
            Write-Host "" -ForegroundColor White
            Write-Host "  Arquivos CSV encontrados em $defaultPath :" -ForegroundColor Yellow
            foreach ($csv in $csvFiles) {
                Write-Host "    - $($csv.Name)" -ForegroundColor Gray
            }
            Write-Host "" -ForegroundColor White
            Write-Host "  Exemplo de uso:" -ForegroundColor White
            Write-Host "    .\test_manual_parser.ps1 `"$defaultPath\$($csvFiles[0].Name)`"" -ForegroundColor Cyan
        }
    }
    exit 1
}
Write-Host "  OK: CSV encontrado" -ForegroundColor Green
Write-Host "" -ForegroundColor White
Write-Host "  Arquivo: $CsvPath" -ForegroundColor Gray
Write-Host "" -ForegroundColor White

# ========================================
# Verificar Python
# ========================================
Write-Host "[2/4] Verificando Python..." -ForegroundColor Yellow

try {
    $pythonVersion = python --version 2>&1
    Write-Host "  OK: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ERRO: Python nao encontrado no PATH" -ForegroundColor Red
    Write-Host "  Instale o Python 3.11+ e adicione ao PATH do sistema." -ForegroundColor Yellow
    exit 1
}

# ========================================
# Verificar .env
# ========================================
Write-Host "" -ForegroundColor White
Write-Host "[3/4] Verificando configuracoes..." -ForegroundColor Yellow

$envFile = Join-Path $ParentDir ".env"
if (Test-Path $envFile) {
    Write-Host "  OK: .env encontrado em $ParentDir" -ForegroundColor Green
    
    # Ler e verificar se a chave parece ser Service Role
    $envContent = Get-Content $envFile -Raw
    if ($envContent -match "SUPABASE_KEY\s*=\s*eyJ") {
        Write-Host "  OK: Service Role Key detectada (comeca com eyJ...)" -ForegroundColor Green
    } else {
        Write-Host "  AVISO: Chave pode ser Anon Key (verifique se comeca com eyJ...)" -ForegroundColor Yellow
        Write-Host "         Service Role Keys comecam com 'eyJ' (formato JWT)" -ForegroundColor Gray
    }
} else {
    Write-Host "  AVISO: .env nao encontrado em $ParentDir" -ForegroundColor Yellow
    Write-Host "         O script tentara usar variaveis de ambiente do sistema." -ForegroundColor Gray
}

# ========================================
# Executar Parser
# ========================================
Write-Host "" -ForegroundColor White
Write-Host "[4/4] Executando parser..." -ForegroundColor Yellow
Write-Host "" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SAIDA DO PARSER" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "" -ForegroundColor White

try {
    # Executar o parser com o caminho do CSV
    # Usando & para garantir que argumentos com espacos sejam passados corretamente
    & python $ParserScript $CsvPath
    
    $exitCode = $LASTEXITCODE
    
    Write-Host "" -ForegroundColor White
    Write-Host "========================================" -ForegroundColor Cyan
    
    if ($exitCode -eq 0) {
        Write-Host "  PARSER CONCLUIDO COM SUCESSO!" -ForegroundColor Green
    } else {
        Write-Host "  PARSER FINALIZADO COM CODIGO: $exitCode" -ForegroundColor Yellow
    }
    Write-Host "========================================" -ForegroundColor Cyan
    
} catch {
    Write-Host "" -ForegroundColor White
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "  ERRO NA EXECUCAO" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "" -ForegroundColor White
    Write-Host "  Mensagem: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "" -ForegroundColor White
    
    # Sugestoes de solucao
    Write-Host "  Possiveis solucoes:" -ForegroundColor Yellow
    Write-Host "    1. Reinicie o PowerShell/terminal para limpar cache" -ForegroundColor White
    Write-Host "    2. Verifique se a Service Role Key esta correta no .env" -ForegroundColor White
    Write-Host "    3. Verifique se as tabelas 'manual_*' existem no Supabase" -ForegroundColor White
    Write-Host "    4. Verifique se o Row-Level Security (RLS) esta configurado" -ForegroundColor White
    Write-Host "" -ForegroundColor White
}

Write-Host "" -ForegroundColor White
