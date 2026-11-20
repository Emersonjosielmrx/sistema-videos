@echo off
REM cron_facebook_vigia.bat - tarefa FacebookVigia (a cada 15 min). 20/11/2026 dona: acompanhar cada acao e resolver em tempo real.
set PYTHONUTF8=1
"D:\hipercool-videos\venv\Scripts\python.exe" -u "D:\postador-de-videos\bin\fb_vigia.py" >> "D:\postador-de-videos\logs\fb_vigia_cron.log" 2>&1
