@echo off
REM Liga a POSTAGEM automatica do hipercool (bin/fila.py ligar-postagem): tarefa HipercoolPostagem a cada 20 min.
REM Independente da producao: uma pode estar ligada e a outra desligada.
title HIPERCOOL - LIGAR postagem automatica
set PATH=D:\hipercool-materiais\bin;%PATH%
set PYTHONUTF8=1
set GEMINI_TTS_PROXY_ENABLED=1
cd /d D:\hipercool-videos
echo ============================================
echo   HIPERCOOL - LIGAR postagem automatica
echo ============================================
D:\hipercool-videos\venv\Scripts\python.exe D:\hipercool-videos\bin\fila.py ligar-postagem
echo.
pause
