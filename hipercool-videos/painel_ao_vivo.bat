@echo off
title Painel Dashboard Hipercool Avançado
chcp 65001 >nul
cls

echo ====================================================
echo    INICIANDO DASHBOARD ESTACAO DE CONTROLE
echo ====================================================

set PYTHONUTF8=1
"D:\hipercool-videos\venv\Scripts\python.exe" "D:\hipercool-inferior-fix\painel_dashboard.py"
pause
