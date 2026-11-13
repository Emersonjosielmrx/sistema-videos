@echo off
rem Melhorador automático da linha PRODUTOS (produto\melhorador.py). Só faz algo se config\melhorador_produtos.json "ligado".
cd /d D:\postador-de-videos\bin
D:\veo\venv\Scripts\python.exe -u -m produto.melhorador --ciclo >> D:\video-fila\linhas\PRODUTOS\melhorador_tarefa.log 2>&1
