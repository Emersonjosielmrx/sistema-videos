@echo off
REM Desliga a producao automatica do hipercool (bin/fila.py desligar). O que estiver renderizando termina.
title HIPERCOOL - DESLIGAR producao automatica
set PATH=D:\hipercool-materiais\bin;%PATH%
set PYTHONUTF8=1
cd /d D:\hipercool-videos
echo ============================================
echo   HIPERCOOL - DESLIGAR producao automatica
echo ============================================
D:\hipercool-videos\venv\Scripts\python.exe D:\hipercool-videos\bin\fila.py desligar
echo.
pause
