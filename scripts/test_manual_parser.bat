@echo off
chcp 65001 >nul
title Testar Parser - Testes Manuais

cd /d "%~dp0"

if "%~1"=="" (
    echo ========================================
    echo   TESTAR PARSER - TESTES MANUAIS
    echo ========================================
    echo.
    echo Uso: %0 "caminho\para\seu\arquivo.csv"
    echo.
    echo Exemplos:
    echo   %0 "C:\Users\mmmorais\Downloads\Lista Testes All Projects (Oney Bank) 2026-05-25T12_22_19+0100.csv"
    echo   %0 "C:\Users\mmmorais\Downloads\Defects All Projects (BNPL) 2026-05-25T14_30_00+0100.csv"
    echo.
    echo Tipos de CSV suportados:
    echo   - Lista Testes All Projects (Projeto) data.csv
    echo   - Defects All Projects (Projeto) data.csv
    echo   - FillAutoDefects (Projeto) data.csv
    echo.
    pause
    exit /b 1
)

echo ========================================
echo   TESTAR PARSER - TESTES MANUAIS
echo ========================================
echo.
echo Arquivo: %~1
echo.

if not exist "%~1" (
    echo ERRO: Arquivo nao encontrado: %~1
    echo.
    pause
    exit /b 1
)

echo Iniciando parser...
echo ========================================
echo.

python parse_manual_csv.py "%~1"

echo.
echo ========================================
echo Processamento concluido.
echo.
pause
