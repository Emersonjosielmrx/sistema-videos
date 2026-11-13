@echo off
REM ============================================================
REM  VEO — PAINEL (raiz D:\veo)
REM  Liga o SUPERVISOR, que gerencia os 3 ambientes conforme o
REM  recurso da maquina (prod > beta > experimental):
REM   - com folga: roda os ativos
REM   - apertado : mantem so a live (beta hoje), pausa o resto
REM   - critico  : pausa tudo, 1 teste na experimental, religa a live
REM ============================================================
title VEO-PAINEL-supervisor
set PYTHONUTF8=1
cd /d "%~dp0"

echo.
echo  === VEO — estado atual ===
"%~dp0venv\Scripts\python.exe" -u supervisor.py status
echo.
echo  Iniciando supervisor (Ctrl+C nesta janela para parar)...
echo.
"%~dp0venv\Scripts\python.exe" -u supervisor.py --loop
