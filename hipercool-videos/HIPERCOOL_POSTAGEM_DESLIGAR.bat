@echo off
REM Desliga a POSTAGEM automatica do hipercool (bin/fila.py desligar-postagem). A producao continua.
title HIPERCOOL - DESLIGAR postagem automatica
set PATH=D:\hipercool-materiais\bin;%PATH%
set PYTHONUTF8=1
cd /d D:\hipercool-videos
echo ============================================
echo   HIPERCOOL - DESLIGAR postagem automatica
echo ============================================
D:\hipercool-videos\venv\Scripts\python.exe D:\hipercool-videos\bin\fila.py desligar-postagem
echo.
pause
