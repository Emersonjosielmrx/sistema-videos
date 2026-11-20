@echo off
REM cron_facebook_criar.bat - tarefa FacebookCriarPaginas (09:40 13:40 16:40 19:40 22:40). 20/11/2026 dona: 1 Pagina por TikTok,
REM procedimento completo (arte, criar, foto, capa, config, 1o Reel). Fila: config\fb_fila_paginas.json. Ritmo e trava no script.
set PYTHONUTF8=1
set LOG=D:\postador-de-videos\logs\facebook_criar_cron.log
set PY=D:\hipercool-videos\venv\Scripts\python.exe
echo [%date% %time%] === criar Pagina === >> "%LOG%"
"%PY%" -u "D:\postador-de-videos\bin\fb_criar_fila.py" >> "%LOG%" 2>&1
echo [%date% %time%] exit=%ERRORLEVEL% >> "%LOG%"
