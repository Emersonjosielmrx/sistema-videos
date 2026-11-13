@echo off
title Ligar TESTE
echo Ligando a pista TESTE...
"D:\historias-em-frames\prod\venv\Scripts\python.exe" "D:\historias-em-frames\guardian\pista_control.py" teste on
timeout /t 5 >nul
