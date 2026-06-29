<#
.SYNOPSIS
    Verifica a Configuracao do Ambiente para Testes Manuais
.DESCRIPTION
    Este script verifica:
    - Se o .env existe e tem a chave correta
    - Se Python esta instalado
    - Se a pasta de relatorios existe
    - Se as tabelas existem no Supabase (opcional)
.EXAMPLE
    .\verify_setup.ps1
#>

param(
    [switch]$FullCheck
)

# $ErrorActionPreference = "SilentlyContinue"  <- REMOVIDO: estava mascarando erros

# ========================================
# Configuracoes
# ========================================
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ParentDir = Split-Path -Parent $ScriptDir
$EnvFile = Join-Path $ParentDir ".env"
$EnvScriptFile = Join-Path $ScriptDir ".env"

# Debug: mostrar caminhos calculados
Write-Host "[DEBUG] Caminhos calculados:" -ForegroundColor Gray
Write-Host "         ScriptDir: $ScriptDir" -ForegroundColor Gray
Write-Host "         ParentDir: $ParentDir" -ForegroundColor Gray
Write-Host "" -ForegroundColor White

$problems = @()
$warnings = @()
$successes = @()

Write-Host "" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  VERIFICACAO DE CONFIGURACAO" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "" -ForegroundColor White

# ========================================
# 1. Verificar Pastas
# ========================================
Write-Host "[1/6] Verificando estrutura de pastas..." -ForegroundColor Yellow
Write-Host "" -ForegroundColor White

if (Test-Path $ParentDir) {
    $successes += "Pasta pai existe: $ParentDir"
    Write-Host "  [OK] Pasta pai: $ParentDir" -ForegroundColor Green
} else {
    $problems += "Pasta pai nao encontrada: $ParentDir"
    Write-Host "  [ERRO] Pasta pai nao encontrada: $ParentDir" -ForegroundColor Red
}

if (Test-Path $ScriptDir) {
    $successes += "Pasta scripts existe: $ScriptDir"
    Write-Host "  [OK] Pasta scripts: $ScriptDir" -ForegroundColor Green
} else {
    $problems += "Pasta scripts nao encontrada: $ScriptDir"
    Write-Host "  [ERRO] Pasta scripts nao encontrada: $ScriptDir" -ForegroundColor Red
}

# ========================================
# 2. Verificar Python
# ========================================
Write-Host "" -ForegroundColor White
Write-Host "[2/6] Verificando Python..." -ForegroundColor Yellow
Write-Host "" -ForegroundColor White

try {
    $pythonVersion = python --version 2>&1
    $successes += "Python instalado: $pythonVersion"
    Write-Host "  [OK] $pythonVersion" -ForegroundColor Green
    
    # Verificar pacotes
    Write-Host "  Verificando pacotes Python..." -ForegroundColor Gray
    
    $requiredPackages = @("requests", "python-dotenv", "pandas", "watchdog")
    foreach ($pkg in $requiredPackages) {
        $result = python -c "import $pkg; print('OK')" 2>&1
        if ($result -eq "OK") {
            $successes += "Pacote $pkg instalado"
            Write-Host "    [OK] $pkg" -ForegroundColor Green
        } else {
            $warnings += "Pacote $pkg nao encontrado"
            Write-Host "    [AVISO] $pkg - Instalar com: pip install $pkg" -ForegroundColor Yellow
        }
    }
    
} catch {
    $problems += "Python nao encontrado no PATH"
    Write-Host "  [ERRO] Python nao encontrado" -ForegroundColor Red
}

# ========================================
# 3. Verificar Arquivos .env
# ========================================
Write-Host "" -ForegroundColor White
Write-Host "[3/6] Verificando arquivos .env..." -ForegroundColor Yellow
Write-Host "" -ForegroundColor White

# Verificar .env na raiz
if (Test-Path $EnvFile) {
    $successes += ".env encontrado na raiz: $EnvFile"
    Write-Host "  [OK] .env na raiz: $EnvFile" -ForegroundColor Green
    
    # Ler e analisar o conteudo
    $envContent = Get-Content $EnvFile -Raw
    
    # Verificar SUPABASE_URL
    if ($envContent -match "SUPABASE_URL\s*=\s*https://") {
        $successes += "SUPABASE_URL definida corretamente"
        Write-Host "    [OK] SUPABASE_URL" -ForegroundColor Green
    } else {
        $problems += "SUPABASE_URL nao encontrada ou invalida"
        Write-Host "    [ERRO] SUPABASE_URL nao encontrada" -ForegroundColor Red
    }
    
    # Verificar SUPABASE_KEY - Service Role Key comeca com eyJ
    if ($envContent -match "SUPABASE_KEY\s*=\s*eyJ") {
        $successes += "SUPABASE_KEY parece ser Service Role (comeca com eyJ)"
        Write-Host "    [OK] SUPABASE_KEY (Service Role detectada)" -ForegroundColor Green
    } elseif ($envContent -match "SUPABASE_KEY\s*=\s*sb_publishable") {
        $problems += "SUPABASE_KEY e Anon Key (sb_publishable__). Nao funciona para insercao."
        Write-Host "    [ERRO] SUPABASE_KEY e Anon Key (use Service Role)" -ForegroundColor Red
    } else {
        $warnings += "Nao foi possivel determinar o tipo de SUPABASE_KEY"
        Write-Host "    [AVISO] Tipo de chave indeterminado" -ForegroundColor Yellow
    }
    
    # Verificar MANUAL_REPORT_PATH
    if ($envContent -match "MANUAL_REPORT_PATH") {
        $successes += "MANUAL_REPORT_PATH definido"
        Write-Host "    [OK] MANUAL_REPORT_PATH" -ForegroundColor Green
    } else {
        $warnings += "MANUAL_REPORT_PATH nao definido (usara padrao)"
        Write-Host "    [AVISO] MANUAL_REPORT_PATH nao definido" -ForegroundColor Yellow
    }
    
    # Verificar MANUAL_PROJECT_MAP
    if ($envContent -match "MANUAL_PROJECT_MAP") {
        $successes += "MANUAL_PROJECT_MAP definido"
        Write-Host "    [OK] MANUAL_PROJECT_MAP" -ForegroundColor Green
    } else {
        $warnings += "MANUAL_PROJECT_MAP nao definido (usara padrao)"
        Write-Host "    [AVISO] MANUAL_PROJECT_MAP nao definido" -ForegroundColor Yellow
    }
    
} else {
    $warnings += ".env nao encontrado na raiz: $EnvFile"
    Write-Host "  [AVISO] .env na raiz nao encontrado: $EnvFile" -ForegroundColor Yellow
}

# Verificar .env na pasta scripts (pode conflitar)
if (Test-Path $EnvScriptFile) {
    $warnings += ".env encontrado na pasta scripts (pode sobrescrever o da raiz)"
    Write-Host "" -ForegroundColor White
    Write-Host "  [AVISO] .env na pasta scripts detectado:" -ForegroundColor Yellow
    Write-Host "           $EnvScriptFile" -ForegroundColor Gray
    Write-Host "           Este .env pode sobrescrever as configuracoes do da raiz." -ForegroundColor Gray
    Write-Host "           Recomendacao: Exclua ou renomeie este arquivo." -ForegroundColor Gray
}

# ========================================
# 4. Verificar Scripts Principais
# ========================================
Write-Host "" -ForegroundColor White
Write-Host "[4/6] Verificando scripts principais..." -ForegroundColor Yellow
Write-Host "" -ForegroundColor White

$scripts = @(
    @{Name = "parse_manual_csv.py"; Path = Join-Path $ScriptDir "parse_manual_csv.py" },
    @{Name = "watch_manual_reports.py"; Path = Join-Path $ScriptDir "watch_manual_reports.py" },
    @{Name = "db.py"; Path = Join-Path $ParentDir "db.py" },
    @{Name = "config.py"; Path = Join-Path $ParentDir "config.py" }
)

foreach ($script in $scripts) {
    if (Test-Path $script.Path) {
        $successes += "Script encontrado: $($script.Name)"
        Write-Host "  [OK] $($script.Name)" -ForegroundColor Green
    } else {
        $problems += "Script nao encontrado: $($script.Name)"
        Write-Host "  [ERRO] $($script.Name) nao encontrado em $($script.Path)" -ForegroundColor Red
    }
}

# ========================================
# 5. Verificar Pasta de Relatorios
# ========================================
Write-Host "" -ForegroundColor White
Write-Host "[5/6] Verificando pasta de relatorios..." -ForegroundColor Yellow
Write-Host "" -ForegroundColor White

# Tentar extrair do .env ou usar padrao
$reportPath = "C:\Users\mmmorais\Downloads"

if (Test-Path $EnvFile) {
    $envContent = Get-Content $EnvFile -Raw
    if ($envContent -match "MANUAL_REPORT_PATH\s*=\s*(.+?)\s*$") {
        $reportPath = $matches[1].Trim()
    }
}

Write-Host "  Caminho esperado: $reportPath" -ForegroundColor Gray

if (Test-Path $reportPath) {
    $successes += "Pasta de relatorios existe: $reportPath"
    Write-Host "  [OK] Pasta existe: $reportPath" -ForegroundColor Green
    
    # Verificar se ha arquivos CSV
    $csvFiles = Get-ChildItem -Path $reportPath -Filter "*.csv" -File -ErrorAction SilentlyContinue
    if ($csvFiles) {
        $successes += "Encontrados $($csvFiles.Count) arquivos CSV"
        Write-Host "  [OK] $($csvFiles.Count) arquivo(s) CSV encontrado(s)" -ForegroundColor Green
        
        # Listar alguns exemplos
        $exampleCsvs = $csvFiles | Select-Object -First 3
        foreach ($csv in $exampleCsvs) {
            Write-Host "       - $($csv.Name)" -ForegroundColor Gray
        }
    } else {
        $warnings += "Nenhum arquivo CSV encontrado em $reportPath"
        Write-Host "  [AVISO] Nenhum CSV encontrado (normal se for a primeira configuracao)" -ForegroundColor Yellow
    }
    
} else {
    $warnings += "Pasta de relatorios nao existe: $reportPath"
    Write-Host "  [AVISO] Pasta nao existe: $reportPath" -ForegroundColor Yellow
    Write-Host "           O watcher tentara criar subpastas automaticamente." -ForegroundColor Gray
}

# ========================================
# 6. Resumo Final
# ========================================
Write-Host "" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  RESUMO DA VERIFICACAO" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "" -ForegroundColor White

if ($successes.Count -gt 0) {
    Write-Host "[SUCESSOS] $($successes.Count) itens OK:" -ForegroundColor Green
    foreach ($s in $successes) {
        Write-Host "  - $s" -ForegroundColor White
    }
    Write-Host "" -ForegroundColor White
}

if ($warnings.Count -gt 0) {
    Write-Host "[AVISOS] $($warnings.Count) itens:" -ForegroundColor Yellow
    foreach ($w in $warnings) {
        Write-Host "  - $w" -ForegroundColor White
    }
    Write-Host "" -ForegroundColor White
}

if ($problems.Count -gt 0) {
    Write-Host "[PROBLEMAS] $($problems.Count) itens criticos:" -ForegroundColor Red
    foreach ($p in $problems) {
        Write-Host "  - $p" -ForegroundColor White
    }
    Write-Host "" -ForegroundColor White
}

# ========================================
# Conclusao
# ========================================
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "" -ForegroundColor White

if ($problems.Count -eq 0) {
    Write-Host "CONFIGURACAO PARECE OK!" -ForegroundColor Green
    Write-Host "" -ForegroundColor White
    Write-Host "Proximos passos:" -ForegroundColor White
    Write-Host "  1. Teste o parser: .\test_manual_parser.ps1 `"caminho\para\arquivo.csv`"" -ForegroundColor Gray
    Write-Host "  2. Instale o watcher: .\install_manual_watcher.ps1 (como Admin)" -ForegroundColor Gray
} else {
    Write-Host "ALGUNS PROBLEMAS FORAM ENCONTRADOS" -ForegroundColor Red
    Write-Host "" -ForegroundColor White
    Write-Host "Corrija os problemas acima e execute novamente." -ForegroundColor White
}

Write-Host "" -ForegroundColor White
