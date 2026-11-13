@echo off
cd /d D:\recap_central_casa
"D:\recap_central_casa\venv\Scripts\python.exe" -X utf8 vps_central.py %* >> central.log 2>&1
