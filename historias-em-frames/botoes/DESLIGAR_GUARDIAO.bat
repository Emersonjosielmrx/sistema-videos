@echo off
title Desligar Guardiao
echo Parando o guardiao...
taskkill /F /FI "WINDOWTITLE eq Ligar Guardiao*" >nul 2>&1
for /f "tokens=2" %%p in ('tasklist /v /fo list ^| findstr /i resource_guardian') do taskkill /F /PID %%p >nul 2>&1
wmic process where "commandline like '%%resource_guardian.py%%'" delete >nul 2>&1
echo Guardiao DESLIGADO.
timeout /t 5 >nul
