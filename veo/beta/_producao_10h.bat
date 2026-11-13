@echo off
REM ============================================================
REM  PRODUCAO AUTONOMA - loop unico, bot rotaciona as contas
REM  sozinho (escolher_sessao pula EXHAUSTED/cooldown).
REM  Roda ate zerar creditos de todas as contas ou ser parado.
REM ============================================================
cd /d D:\veo\beta
set PYTHONUTF8=1
REM FIX 2026-07-27: cron_gerar_video_llm.validar_video() chama ffprobe sem path.
REM Sem isto no PATH, devolvia [WinError 2] e o pipeline travava em loop vazio.
set PATH=D:\hipercool-materiais\bin;%PATH%
set LLM_MODEL=gemini-flash-lite-latest
set LLM_TIMEOUT=30
set FLOW_HEADLESS=0
set FLOW_PROXY=
set FLOW_ASPECT=9:16
set FLOW_MODEL=Veo 3.1 - Fast
set FLOW_DURATION=8S
title Veo-PRODUCAO-BETA
:LOOP
echo [%date% %time%] === ciclo producao ===
D:\veo\venv\Scripts\python.exe -u cron_gerar_video_llm.py >> logs\producao_10h.log 2>&1
set RC=%ERRORLEVEL%
echo [%date% %time%] ciclo rc=%RC%
if "%RC%"=="6" (
  echo [%date% %time%] TODAS as contas sem credito. Esperando 30min para renovacao...
  timeout /t 1800 /nobreak >nul
  goto LOOP
)
timeout /t 20 /nobreak >nul
goto LOOP
