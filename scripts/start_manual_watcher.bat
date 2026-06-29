@echo off
chcp 65001 >nul
title Watcher - Testes Manuais

echo ========================================
echo   WATCHER DE TESTES MANUAIS
echo ========================================
echo.

cd /d "%~dp0"

echo Diretorio atual: %cd%
echo.
echo Monitorando pasta configurada em MANUAL_REPORT_PATH...
echo.
echo Tipos suportados:
echo   - Lista Testes All Projects
echo   - Defects All Projects
echo   - FillAutoDefects
echo.
echo Pressione Ctrl+C para parar.
echo ========================================
echo.

python watch_manual_reports.py

echo.
echo Watcher parado.
pause
