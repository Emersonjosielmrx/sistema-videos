@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d D:\manhwa-react
.venv\Scripts\python.exe manhwareact.py canais
start "" "D:\manhwa-react\canais"
