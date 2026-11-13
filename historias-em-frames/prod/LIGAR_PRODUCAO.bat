@echo off
REM LIGAR_PRODUCAO.bat - Liga o produtor autonomo desta pista (destacado).
title Ligar Producao de Videos
cd /d "%~dp0"

echo ============================================
echo   LIGANDO PRODUCAO AUTONOMA DE VIDEOS
echo ============================================
echo.

REM venv da PROPRIA pista; se nao existir, cai no python do PATH
set "PY=%~dp0venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"

"%PY%" "%~dp0launch_daemon.py"

echo.
echo Producao LIGADA. Roda em segundo plano (sem janela).
echo Log: %~dp0logs\auto-producer.md
echo.
echo Esta janela fecha em 8 segundos...
timeout /t 8 >nul
