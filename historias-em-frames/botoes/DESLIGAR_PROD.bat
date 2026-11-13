@echo off
title Desligar PROD
echo Desligando a pista PROD...
"D:\historias-em-frames\prod\venv\Scripts\python.exe" "D:\historias-em-frames\guardian\pista_control.py" prod off
timeout /t 5 >nul
