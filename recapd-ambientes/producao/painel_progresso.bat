@echo off
title Painel Progresso - Hipercool
chcp 65001 >nul
set PYTHONUTF8=1
D:\recapd-ambientes\producao\venv\Scripts\python.exe "%~dp0bin\painel-progresso.py"
pause
