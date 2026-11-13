@echo off
REM HIPERCOOL_DESLIGAR.bat — Para produção autônoma de vídeos
title HIPERCOOL — Desligar Produção
set PATH=D:\hipercool-materiais\bin;%PATH%
cd /d D:\hipercool-videos
echo ============================================
echo   HIPERCOOL — DESLIGAR PRODUCAO
echo ============================================
D:\hipercool-videos\venv\Scripts\python.exe D:\hipercool-videos\stop_auto_producer.py
echo.
echo Producao PARADA.
echo Esta janela fecha em 8s...
timeout /t 8 >nul
