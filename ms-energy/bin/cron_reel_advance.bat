@echo off
REM cron_reel_advance.bat - tarefa AdvanceSolar_Reel: gera 1 Reel com o CLONE do Luiz (Veo) e posta no Instagram
REM @advance_novoestrela por HTTP (bin\reel_advance.py). Dona 30/10: "cade os videos de avatar?".
set PYTHONUTF8=1
set LOG=D:\ms-energy\logs\reel_advance_cron.log
echo [%date% %time%] === reel advance === >> "%LOG%"
D:\veo\venv\Scripts\python.exe D:\ms-energy\bin\reel_advance.py >> "%LOG%" 2>&1
echo [%date% %time%] exit=%ERRORLEVEL% >> "%LOG%"
