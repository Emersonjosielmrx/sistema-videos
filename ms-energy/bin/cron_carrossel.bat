@echo off
REM cron_carrossel.bat - tarefa MSEnergy_Carrossel (terca, quinta e sabado 12:37): gera e posta 1 carrossel educativo
REM no Instagram @msenergycap (bin\carrossel_ms.py). Nao gasta credito do Veo.
set PYTHONUTF8=1
set LOG=D:\ms-energy\logs\carrossel.log
echo [%date% %time%] === carrossel === >> "%LOG%"
D:\veo\venv\Scripts\python.exe D:\ms-energy\bin\carrossel_ms.py >> "%LOG%" 2>&1
echo [%date% %time%] exit=%ERRORLEVEL% >> "%LOG%"
