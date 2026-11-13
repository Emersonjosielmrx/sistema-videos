@echo off
title Ligar BETA
echo Ligando a pista BETA...
"D:\historias-em-frames\prod\venv\Scripts\python.exe" "D:\historias-em-frames\guardian\pista_control.py" beta on
timeout /t 5 >nul
