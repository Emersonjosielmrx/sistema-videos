@echo off
rem Liga o trabalhador da Ponte PC <-> n8n sem janela (pythonw). Para desligar: DESLIGAR_PONTE.bat
cd /d "%~dp0"
start "" pythonw "%~dp0trabalhador.py"
echo Ponte ligada. Log: %~dp0logs\trabalhador.log
