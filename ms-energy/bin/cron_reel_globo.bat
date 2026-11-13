@echo off
REM cron_reel_globo.bat - tarefa GloboSolar_Reel (09:20 / 13:20 / 20:30): Reel com o clone do dono da Globo Solar
REM (@globosolarenergiag) por HTTP com o cofre (bin\reel_globo.py). Dona 31/10.
set PYTHONUTF8=1
set LOG=D:\ms-energy\logs\reel_globo_cron.log
echo [%date% %time%] === reel globo === >> "%LOG%"
D:\veo\venv\Scripts\python.exe D:\ms-energy\bin\reel_globo.py >> "%LOG%" 2>&1
echo [%date% %time%] exit=%ERRORLEVEL% >> "%LOG%"
