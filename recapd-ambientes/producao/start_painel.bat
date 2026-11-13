@echo off
title Painel Dashboard Hipercool
chcp 65001 >nul
cls

echo ====================================================
echo    INICIANDO DASHBOARD DE RENDERIZACAO
echo ====================================================

"D:\recapd-ambientes\producao\venv\Scripts\python.exe" "D:\hipercool-inferior-fix\painel_dashboard.py"
pause
