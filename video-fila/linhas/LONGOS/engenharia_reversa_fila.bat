@echo off
cd /d D:\recapd-ambientes\producao
"D:\recapd-ambientes\producao\venv\Scripts\python.exe" -u D:\video-fila\linhas\LONGOS\engenharia_reversa.py fila >> "D:\video-fila\linhas\LONGOS\referencias\engenharia.log" 2>&1
