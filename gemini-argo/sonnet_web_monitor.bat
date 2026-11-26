@echo off
rem Tarefa SonnetWebMonitor (1 h): o caminho "D:\sonnet web" tem espaço e o schtasks engasga; este .bat resolve.
"D:\veo\venv\Scripts\pythonw.exe" -X utf8 "D:\sonnet web\monitor_sonnet_web.py"
