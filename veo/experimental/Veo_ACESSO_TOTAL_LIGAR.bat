@echo off
REM ============================================================
REM  Veo — ACESSO TOTAL: LIGAR
REM  Ligue quando NAO estiver usando o Chrome pra nada seu.
REM  O bot fecha os Chromes ociosos e deixa aberto SO os que ele usa.
REM  (tambem derruba Chromes velhos travados do bot pra respawnar limpos)
REM ============================================================
title Veo-ACESSO-TOTAL-LIGAR
set PYTHONUTF8=1
cd /d "%~dp0"
"%~dp0..\venv\Scripts\python.exe" -u acesso_total.py ligar
echo.
timeout /t 4 /nobreak >nul
