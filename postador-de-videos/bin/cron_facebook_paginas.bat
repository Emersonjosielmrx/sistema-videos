@echo off
REM cron_facebook_paginas.bat - tarefa FacebookPaginas (de hora em hora 08:20-23:20). 21/11: roda TODAS as contas que tem
REM Paginas ativas, em paralelo, cada uma no Chrome e na saida dela (fb_contas confere o proxy). Antes so rodava a
REM emersonjosiel02 e as Paginas da mundosolar1995 nunca recebiam Reel. MS Energy nao passa aqui (postar_ms_energy).
REM --horario: posta so nas Paginas atrasadas pelo relogio + 1 no horario nobre 21-22 h. Trava por conta (lock) no script.
set PYTHONUTF8=1
set LOG=D:\postador-de-videos\logs\facebook_paginas.log
set PY=D:\hipercool-videos\venv\Scripts\python.exe
echo [%date% %time%] === Reels nas Paginas (rodada da hora) === >> "%LOG%"
"%PY%" -u "D:\postador-de-videos\bin\fb_rodada_todas.py" >> "%LOG%" 2>&1
echo [%date% %time%] exit=%ERRORLEVEL% >> "%LOG%"
echo. >> "%LOG%"
