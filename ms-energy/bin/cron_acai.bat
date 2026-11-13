@echo off
rem 05/11 dona: posta o próximo item da fila do açaí (paleta C, carrossel ou reel de arquivado)
cd /d D:\ms-energy\bin
"D:\veo\venv\Scripts\python.exe" -X utf8 acai_fila_proximo.py >> D:\ms-energy\logs\acai_cron.log 2>&1
