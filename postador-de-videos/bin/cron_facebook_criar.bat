@echo off
REM cron_facebook_criar.bat - tarefa FacebookCriarPaginas (de hora em hora 07:45-23:45 + madrugada). 20/11 dona: "crie o maximo
REM de paginas, mantenha o trabalho, deixe tudo postado". --todas = 1 processo por conta LIVRE em paralelo (cada uma no seu IP;
REM ritmo/intervalo/limite por conta e trava anti-bloqueio no fb_criar_fila). Fila: config\fb_fila_paginas.json.
set PYTHONUTF8=1
set LOG=D:\postador-de-videos\logs\facebook_criar_cron.log
set PY=D:\hipercool-videos\venv\Scripts\python.exe
echo [%date% %time%] === criar Paginas (todas as contas livres) === >> "%LOG%"
"%PY%" -u "D:\postador-de-videos\bin\fb_criar_fila.py" --todas >> "%LOG%" 2>&1
echo [%date% %time%] exit=%ERRORLEVEL% >> "%LOG%"
