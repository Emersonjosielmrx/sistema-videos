@echo off
REM ============================================================
REM  Veo — START DIARIO (agendado 07:00 via Task Scheduler)
REM  Inicia a producao todo dia as 7h. A priorizacao free-first
REM  (contas 55/dia primeiro, depois as PRO grandes) ja esta no
REM  escolher_sessao do cron_gerar_video_llm.py.
REM
REM  Idempotente: se o loop ja estiver rodando, o novo start apenas
REM  garante que a pausa foi removida (nao duplica geracao porque o
REM  proprio cron usa lock por porta/sessao).
REM ============================================================
title Veo-START-DIARIO-7H
set PYTHONUTF8=1
set FLOW_HEADLESS=1
cd /d "%~dp0"

REM remove pausa manual, se houver, pra poder ligar
if exist logs\PAUSE_SYSTEM del /q logs\PAUSE_SYSTEM

call "%~dp0run_cron_loop_3contas.bat"
