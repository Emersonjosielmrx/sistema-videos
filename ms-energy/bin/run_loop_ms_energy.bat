@echo off
title MS-Energy-Loop
set PYTHONUTF8=1
set GEMINI_TTS_PROXY_ENABLED=1

REM Carrega config da LLM (mesma do Veo)
call "D:\veo\beta\configurar_llm.bat" >nul 2>&1

REM Flow defaults (fallback; a escada de resiliencia troca via contas.py)
set FLOW_SESSION=seebotsia
set FLOW_PROJ=https://labs.google/fx/pt/tools/flow
set FLOW_ASPECT=9:16
set FLOW_MODEL=Veo 3.1 - Fast
set FLOW_DURATION=8S
set FLOW_PORT=9250
set FLOW_PROFILE=chrome_gen_seebotsia

cd /d "D:\ms-energy"
REM venv do Veo (tem PIL/numpy/playwright/edge-tts). O D:\hipercool-videos\venv foi apagado.
set VENV_PY=D:\veo\venv\Scripts\python.exe

:LOOP
echo.
echo [%date% %time%] === MS Energy - Iniciando ciclo ===
"%VENV_PY%" -u bin/gerar_short_veo.py --tipo misto --lote 1
set RC=%ERRORLEVEL%

if "%RC%"=="6" (
  echo [%date% %time%] === Sem creditos. Esperando 15min... ===
  timeout /t 900 /nobreak >nul
  goto LOOP
)

echo [%date% %time%] === Ciclo terminou (rc=%RC%). Esperando 60s... ===
timeout /t 60 /nobreak >nul
goto LOOP
