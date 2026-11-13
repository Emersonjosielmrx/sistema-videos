@echo off
cd /d D:\veo\beta
set PYTHONUTF8=1
set LLM_MODEL=gemini-flash-lite-latest
set LLM_TIMEOUT=30
set FLOW_HEADLESS=0
set FLOW_PROXY=
set FLOW_PIN_SESSION=filmescomia
set FLOW_SESSION=filmescomia
set FLOW_PORT=9280
set FLOW_PROFILE=chrome_gen_filmescomia
set FLOW_ASPECT=9:16
set FLOW_MODEL=Veo 3.1 - Fast
set FLOW_DURATION=8S
title Veo-filmescomia-BETA
:LOOP
echo [%date% %time%] === [filmescomia-BETA] ciclo ===
D:\veo\venv\Scripts\python.exe -u cron_gerar_video_llm.py
set RC=%ERRORLEVEL%
if "%RC%"=="6" (
  echo [%date% %time%] filmescomia SEM CREDITO. Encerrando loop.
  goto FIM
)
echo [%date% %time%] ciclo rc=%RC%. Esperando 20s...
timeout /t 20 /nobreak >nul
goto LOOP
:FIM
echo [%date% %time%] filmescomia-BETA finalizada.