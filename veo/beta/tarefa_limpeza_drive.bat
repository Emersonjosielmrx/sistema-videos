@echo off
rem Tarefa Veo_Limpeza_Drive (26/10: roda pelo D:\rodar_oculto.vbs, sem janela). Mesmo comando de antes.
cd /d D:\veo\beta
set PYTHONUTF8=1
D:\veo\venv\Scripts\python.exe D:\veo\beta\cron_limpeza_drive.py >> D:\veo\beta\logs\cron_limpeza_drive.log 2>&1
