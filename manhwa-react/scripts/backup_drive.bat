@echo off
REM Manda para o Google Drive o que ja foi postado ou rejeitado e libera o disco (tarefa BackupDriveVideos, 1x/dia)
set PYTHONUTF8=1
D:\manhwa-react\.venv\Scripts\python.exe -u D:\manhwa-react\scripts\backup_drive.py >> D:\manhwa-react\logs\backup_drive.log 2>&1
