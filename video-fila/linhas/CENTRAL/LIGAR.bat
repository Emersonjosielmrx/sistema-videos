@echo off
rem BOTAO: liga o melhorador central. Sem argumento = SOMBRA (decide, nao aplica). "LIGAR.bat aplicar" = as 4 linhas aplicam.
cd /d D:\video-fila
if /i "%1"=="aplicar" ("C:\Users\Haylla\AppData\Local\Programs\Python\Python313\python.exe" melhorador_central.py ligar --aplicar) else ("C:\Users\Haylla\AppData\Local\Programs\Python\Python313\python.exe" melhorador_central.py ligar)
"C:\Users\Haylla\AppData\Local\Programs\Python\Python313\python.exe" melhorador_central.py status
pause
