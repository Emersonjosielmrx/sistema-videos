@echo off
REM ============================================================
REM  Veo — LIGAR (VISIVEL)
REM  Modo que a dona VE o Chrome. Consome mais RAM/CPU.
REM  Bom pra acompanhar/depurar. Pra producao normal use o invisivel.
REM ============================================================
title Veo-LIGAR-visivel
set PYTHONUTF8=1
set FLOW_HEADLESS=0
cd /d "%~dp0"

REM tira pausa manual, se houver, pra poder ligar
if exist logs\PAUSE_SYSTEM del /q logs\PAUSE_SYSTEM

call "%~dp0run_cron_loop_3contas.bat"
