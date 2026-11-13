@echo off
title CronVeoLLM-Loop-3contas
set PYTHONUTF8=1

REM Carrega config da LLM
call "%~dp0configurar_llm.bat" >nul 2>&1

REM O rodizio REAL de contas vem de contas.py (via escolher_sessao no codigo).
REM Os set FLOW_* abaixo sao so um fallback inofensivo pro 1o ciclo.
set FLOW_SESSION=seebotsia
set FLOW_PROJ=https://labs.google/fx/pt/tools/flow
set FLOW_ASPECT=9:16
set FLOW_MODEL=Veo 3.1 - Fast
set FLOW_DURATION=8S
set FLOW_PORT=9250
set FLOW_PROFILE=chrome_gen_seebotsia
REM INDEPENDENTE: pasta do proprio .bat + venv da raiz D:\veo\venv
cd /d "%~dp0"
set VENV_PY=%~dp0..\venv\Scripts\python.exe

:LOOP
echo.
echo [%date% %time%] === Iniciando ciclo ===
"%VENV_PY%" -u cron_gerar_video_llm.py
set RC=%ERRORLEVEL%

REM exit 6 = todas as contas sem credito. Nao adianta martelar de 30s em 30s
REM ate a meia-noite; espera 15min (o credito so renova no reset diario BR).
if "%RC%"=="6" (
  echo [%date% %time%] === Sem creditos em nenhuma conta. Esperando 15min... ===
  timeout /t 900 /nobreak >nul
  goto LOOP
)

echo [%date% %time%] === Ciclo terminou (rc=%RC%). Esperando 30s... ===
timeout /t 30 /nobreak >nul
goto LOOP
