@echo off
REM Posta 1 video pendente no Instagram agora (Feed + Stories) — o proximo da fila (os novos vem primeiro).
REM 22/10: antes postava TODOS em sequencia; rajada de posts + legenda repetida = sinal de spam pro Instagram.
title MS Energy - Postar 1 video AGORA
set PYTHONUTF8=1
set PY=D:\hipercool-videos\venv\Scripts\python.exe
set SCRIPT=D:\postador-de-videos\bin\postar_ms_energy.py

echo ============================================
echo   MS ENERGY - POSTANDO 1 VIDEO NO INSTAGRAM
echo ============================================
echo.

"%PY%" "%SCRIPT%" --so insta --um

echo.
echo ============================================
echo   FINALIZADO
echo ============================================
echo.
pause
