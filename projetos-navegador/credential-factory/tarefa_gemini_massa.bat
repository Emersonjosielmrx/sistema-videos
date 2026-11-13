@echo off
rem Tarefa GeminiChavesRetentativa (26/10: roda pelo D:\rodar_oculto.vbs, sem janela). Mesmo comando de antes.
cd /d D:\projetos-navegador\credential-factory
set PYTHONUNBUFFERED=1
python -I "D:\projetos-navegador\credential-factory\gemini_chaves.py" criar_massa --vivas > "D:\projetos-navegador\credential-factory\gemini_massa_saida.txt" 2>&1
