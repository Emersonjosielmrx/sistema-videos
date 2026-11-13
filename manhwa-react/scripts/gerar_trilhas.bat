@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d D:\manhwa-react
title ManhwaReact - gerando trilhas originais (MusicGen, demora)
.venv\Scripts\python.exe manhwareact.py musica --por-mood 4 --dur 30
pause
