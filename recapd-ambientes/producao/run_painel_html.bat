@echo off
set PYTHONUTF8=1
cd /d D:\hipercool-inferior-fix
echo Iniciando Painel HTML...
start http://localhost:8080
"D:\recapd-ambientes\producao\venv\Scripts\python.exe" painel_html.py
pause
