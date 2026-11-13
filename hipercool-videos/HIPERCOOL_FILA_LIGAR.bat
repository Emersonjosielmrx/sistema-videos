@echo off
REM Liga a producao automatica do hipercool (bin/fila.py ligar): tarefa HipercoolFila a cada 20 min.
title HIPERCOOL - LIGAR producao automatica
set PATH=D:\hipercool-materiais\bin;%PATH%
set PYTHONUTF8=1
set GEMINI_TTS_PROXY_ENABLED=1
cd /d D:\hipercool-videos
echo ============================================
echo   HIPERCOOL - LIGAR producao automatica
echo ============================================
D:\hipercool-videos\venv\Scripts\python.exe D:\hipercool-videos\bin\fila.py ligar
echo.
pause
