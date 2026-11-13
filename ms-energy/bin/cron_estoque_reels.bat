@echo off
REM cron_estoque_reels.bat - tarefa Solares_Estoque (de 2 em 2 h): gera com antecedencia Reels da Advance e da Globo
REM ate ter 2 prontos de cada (bin\estoque_reels.py). Dona 31/10.
set PYTHONUTF8=1
set LOG=D:\ms-energy\logs\estoque_reels.log
D:\veo\venv\Scripts\python.exe D:\ms-energy\bin\estoque_reels.py >> "%LOG%" 2>&1
