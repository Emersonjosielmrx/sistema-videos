@echo off
rem BOTÃO do dono: desliga o melhorador automático da linha PRODUTOS (a tarefa fica parada; nada é desfeito).
cd /d D:\postador-de-videos\bin
D:\veo\venv\Scripts\python.exe -m produto.melhorador --desligar
pause
