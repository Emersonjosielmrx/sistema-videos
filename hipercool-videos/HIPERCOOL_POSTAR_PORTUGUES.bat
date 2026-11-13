@echo off
REM Posta agora os pendentes em PORTUGUES (bin/fila.py postar). Funciona com a fila ligada ou desligada.
title HIPERCOOL - POSTAR AGORA (so portugues)
set PATH=D:\hipercool-materiais\bin;%PATH%
set PYTHONUTF8=1
set GEMINI_TTS_PROXY_ENABLED=1
cd /d D:\hipercool-videos
echo ============================================
echo   HIPERCOOL - POSTAR AGORA (so portugues)
echo ============================================
D:\hipercool-videos\venv\Scripts\python.exe D:\hipercool-videos\bin\fila.py postar
echo.
pause
