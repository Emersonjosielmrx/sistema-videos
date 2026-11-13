@echo off
REM cron_carrossel_globo.bat - tarefa GloboSolar_Carrossel (10:50 e 17:40): gera e posta 1 carrossel no Instagram
REM @globosolarenergiag (Globo Solar, Concordia do Para) por HTTP com o cofre (bin\carrossel_globo.py). Dona 31/10.
set PYTHONUTF8=1
set LOG=D:\ms-energy\logs\carrossel_globo.log
echo [%date% %time%] === carrossel globo === >> "%LOG%"
D:\veo\venv\Scripts\python.exe D:\ms-energy\bin\carrossel_globo.py >> "%LOG%" 2>&1
echo [%date% %time%] exit=%ERRORLEVEL% >> "%LOG%"
