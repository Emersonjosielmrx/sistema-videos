@echo off
title Desligar TESTE
echo Desligando a pista TESTE...
"D:\historias-em-frames\prod\venv\Scripts\python.exe" "D:\historias-em-frames\guardian\pista_control.py" teste off
timeout /t 5 >nul
