@echo off
title Ligar Guardiao de Recurso
echo Ligando o guardiao (monitora RAM/CPU e gerencia beta/teste)...
start "" /min "D:\historias-em-frames\prod\venv\Scripts\python.exe" "D:\historias-em-frames\guardian\resource_guardian.py"
echo Guardiao LIGADO (roda em segundo plano).
timeout /t 5 >nul
