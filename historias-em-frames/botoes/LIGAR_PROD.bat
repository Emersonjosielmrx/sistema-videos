@echo off
title Ligar PROD
echo Ligando a pista PROD...
"D:\historias-em-frames\prod\venv\Scripts\python.exe" "D:\historias-em-frames\guardian\pista_control.py" prod on
timeout /t 5 >nul
