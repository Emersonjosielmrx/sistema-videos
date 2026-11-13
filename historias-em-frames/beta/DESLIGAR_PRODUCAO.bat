@echo off
REM DESLIGAR_PRODUCAO.bat - Para o produtor desta pista e os filhos.
title Desligar Producao de Videos
cd /d "%~dp0"

echo ============================================
echo   DESLIGANDO PRODUCAO AUTONOMA DE VIDEOS
echo ============================================
echo.

set "PY=%~dp0venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"

"%PY%" "%~dp0stop_auto_producer.py"

echo.
echo Esta janela fecha em 8 segundos...
timeout /t 8 >nul
