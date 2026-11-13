@echo off
title Desligar BETA
echo Desligando a pista BETA...
"D:\historias-em-frames\prod\venv\Scripts\python.exe" "D:\historias-em-frames\guardian\pista_control.py" beta off
timeout /t 5 >nul
