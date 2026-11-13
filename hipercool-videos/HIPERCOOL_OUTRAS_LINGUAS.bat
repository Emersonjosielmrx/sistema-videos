@echo off
REM Renderiza agora os pendentes nas OUTRAS LINGUAS (bin/fila.py idiomas). Quem posta e a postagem automatica
REM (HIPERCOOL_POSTAGEM_LIGAR.bat), no horario de pico de cada pais.
title HIPERCOOL - RENDERIZAR pendentes nas outras linguas
set PATH=D:\hipercool-materiais\bin;%PATH%
set PYTHONUTF8=1
set GEMINI_TTS_PROXY_ENABLED=1
cd /d D:\hipercool-videos
echo ============================================
echo   HIPERCOOL - pendentes nas outras linguas
echo ============================================
D:\hipercool-videos\venv\Scripts\python.exe D:\hipercool-videos\bin\fila.py idiomas
echo.
pause
