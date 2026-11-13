@echo off
REM cron_carrossel_advance.bat - tarefa AdvanceSolar_Carrossel (todo dia 11:23): gera e posta 1 carrossel no Instagram
REM @advance_novoestrela (Advance Solar, Castanhal-PA) por HTTP com o cofre (bin\carrossel_advance.py). Dona 29/10.
set PYTHONUTF8=1
set LOG=D:\ms-energy\logs\carrossel_advance.log
echo [%date% %time%] === carrossel advance === >> "%LOG%"
D:\veo\venv\Scripts\python.exe D:\ms-energy\bin\carrossel_advance.py >> "%LOG%" 2>&1
echo [%date% %time%] exit=%ERRORLEVEL% >> "%LOG%"
