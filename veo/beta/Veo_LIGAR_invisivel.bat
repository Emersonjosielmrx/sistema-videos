@echo off
REM ============================================================
REM  Veo — LIGAR (INVISIVEL / ECONOMICO)
REM  Chrome roda escondido (headless). Consome MENOS RAM/CPU.
REM  Este e o modo recomendado pra producao (inclusive de madrugada).
REM  Download e por rede, entao gera video normal mesmo invisivel.
REM  Um pop-up no canto avisa quando cada video sai.
REM ============================================================
title Veo-LIGAR-invisivel
set PYTHONUTF8=1
set FLOW_HEADLESS=1
cd /d "%~dp0"

REM tira pausa manual, se houver, pra poder ligar
if exist logs\PAUSE_SYSTEM del /q logs\PAUSE_SYSTEM

call "%~dp0run_cron_loop_3contas.bat"
