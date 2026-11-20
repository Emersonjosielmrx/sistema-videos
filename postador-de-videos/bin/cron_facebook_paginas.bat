@echo off
REM cron_facebook_paginas.bat — tarefa FacebookPaginas (12:20, 18:20, 21:10). 20/11/2026 dona: "comece as postagens".
REM 1 Reel em cada Página de config\facebook_paginas.json (por_dia = 3), pela saída fixa da conta (fb_contas).
set PYTHONUTF8=1
set LOG=D:\postador-de-videos\logs\facebook_paginas.log
set PY=D:\hipercool-videos\venv\Scripts\python.exe
echo [%date% %time%] === Reels nas Paginas === >> "%LOG%"
"%PY%" -u "D:\postador-de-videos\bin\postar_facebook_paginas.py" --intervalo 240 >> "%LOG%" 2>&1
echo [%date% %time%] exit=%ERRORLEVEL% >> "%LOG%"
echo. >> "%LOG%"
