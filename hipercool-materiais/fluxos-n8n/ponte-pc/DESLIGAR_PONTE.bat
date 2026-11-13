@echo off
rem Desliga SÓ o trabalhador da ponte (procura pelo nome do script; não mexe em outros pythonw).
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name like 'python%%'\" | Where-Object { $_.CommandLine -like '*fluxos-n8n*trabalhador.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force; 'parado: ' + $_.ProcessId }"
