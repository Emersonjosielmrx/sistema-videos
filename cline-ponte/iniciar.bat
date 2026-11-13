@echo off
rem Liga a cline-ponte (sem janela pela tarefa ClinePonte via D:\rodar_oculto.vbs).
rem Se ja estiver rodando, a porta 20160 esta ocupada e este sai sozinho.
cd /d D:\cline-ponte
"C:\Program Files\nodejs\node.exe" ponte.mjs
