@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d D:\manhwa-react
if "%~1"=="" (
  echo Uso: processar.bat "caminho\video.mp4" [opcoes]
  exit /b 1
)
.venv\Scripts\python.exe manhwareact.py process %*
