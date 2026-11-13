@echo off
REM cron_vigia_pastas.bat - tarefa EmpresasPastas_Vigia (a cada 30 min): avisa no Telegram quando o cliente coloca
REM arquivos em entrada/ ou fotos_base/ da pasta do Drive (bin\vigia_pasta_empresas.py). Dona 31/10.
set PYTHONUTF8=1
set LOG=D:\ms-energy\logs\vigia_pastas.log
D:\veo\venv\Scripts\python.exe D:\ms-energy\bin\vigia_pasta_empresas.py >> "%LOG%" 2>&1
