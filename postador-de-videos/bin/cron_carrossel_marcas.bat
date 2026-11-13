@echo off
rem 24/10 (dono): carrossel com a cor de cada Instagram (bin\carrossel_marca.py), 1 por conta por dia
rem 25/10: saida em arquivo PROPRIO (o script escreve no carrossel_marca.log; o mesmo arquivo nos dois = PermissionError)
cd /d D:\postador-de-videos\bin
set PYTHONIOENCODING=utf-8
echo [%date% %time%] inicio >> D:\postador-de-videos\logs\carrossel_marca_tarefa.log
D:\hipercool-videos\venv\Scripts\python.exe -u carrossel_marca.py --todas >> D:\postador-de-videos\logs\carrossel_marca_tarefa.log 2>&1
echo [%date% %time%] fim (exit %errorlevel%) >> D:\postador-de-videos\logs\carrossel_marca_tarefa.log
