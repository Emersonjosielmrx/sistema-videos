@echo off
REM ============================================================
REM  Veo — ACESSO TOTAL: DESLIGAR
REM  Volte pro modo "educado": o bot NAO encosta nos seus Chromes.
REM  Use quando voltar a usar o Chrome pra coisas suas.
REM ============================================================
title Veo-ACESSO-TOTAL-DESLIGAR
set PYTHONUTF8=1
cd /d "%~dp0"
"%~dp0..\venv\Scripts\python.exe" -u acesso_total.py desligar
echo.
timeout /t 4 /nobreak >nul
