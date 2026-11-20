@echo off
REM cron_facebook_paginas.bat - tarefa FacebookPaginas (de hora em hora, 08:20 a 23:20). 20/11/2026 dona: "criar o maximo de Paginas,
REM postagem em todas, sistemas dos outros (escada, inteligencia) funcionando".
REM As 2 contas rodam EM PARALELO, cada uma no Chrome e na saida dela (fb_contas confere o proxy):
REM   msenergypara = casa; emersonjosiel02 = Webshare rnprmtfo-58. Nunca as duas pela mesma saida.
REM --horario: posta so nas Paginas atrasadas pelo relogio (teto da escada espalhado 08-21 h) + 1 no horario nobre 21-22 h.
set PYTHONUTF8=1
set LOG=D:\postador-de-videos\logs\facebook_paginas.log
set PY=D:\hipercool-videos\venv\Scripts\python.exe
echo [%date% %time%] === Reels nas Paginas (rodada da hora) === >> "%LOG%"
start "" /b "%PY%" -u "D:\postador-de-videos\bin\postar_facebook_paginas.py" --horario --conta msenergypara >> "D:\postador-de-videos\logs\facebook_paginas_msenergypara.log" 2>&1
"%PY%" -u "D:\postador-de-videos\bin\postar_facebook_paginas.py" --horario --conta emersonjosiel02 >> "%LOG%" 2>&1
echo [%date% %time%] exit=%ERRORLEVEL% >> "%LOG%"
echo. >> "%LOG%"
