@echo off
REM Revisa (abre no player) tudo que a rede pode postar: react + historias. a=aprova r=rejeita p=pula s=sai
set PYTHONUTF8=1
D:\manhwa-react\.venv\Scripts\python.exe D:\manhwa-react\manhwareact.py rede --aprovar
D:\manhwa-react\.venv\Scripts\python.exe D:\manhwa-react\manhwareact.py rede --simular
pause
