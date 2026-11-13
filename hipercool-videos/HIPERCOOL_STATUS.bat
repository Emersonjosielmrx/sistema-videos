@echo off
REM Mostra o estado da fila do hipercool (bin/fila.py status).
title HIPERCOOL - STATUS da fila
set PYTHONUTF8=1
cd /d D:\hipercool-videos
D:\hipercool-videos\venv\Scripts\python.exe D:\hipercool-videos\bin\fila.py status
echo.
pause
