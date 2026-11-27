@echo off
REM cron_fb_continuar.bat - tarefa FacebookContinuar (03:50, 07:30, 08:50). 21/11 dona: continuar o acompanhamento do chat do
REM Facebook (claude-d0) apos os tokens acabarem. Manda "continue" no chat via sentinela (Gemini, sem Opus).
set PYTHONUTF8=1
"D:\veo\venv\Scripts\python.exe" -u "D:\postador-de-videos\bin\fb_continuar_chat.py" >> "D:\postador-de-videos\logs\fb_continuar.log" 2>&1
