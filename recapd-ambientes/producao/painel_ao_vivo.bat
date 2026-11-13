@echo off
title Painel Ao Vivo - Hipercool
chcp 65001 >nul
cls

echo ====================================================
echo    MONITORADOR DE RENDERIZACAO (TEMPO REAL)
echo ====================================================
echo Aguardando o log mais recente...
echo.

:: Pega o ultimo arquivo .log alterado (incluindo pasta raiz e logs/) e da um "tail" nele
powershell -Command "$latest = Get-ChildItem -Path .\, .\logs\ -Filter *.log | Sort-Object LastWriteTime -Descending | Select-Object -First 1; Write-Host '>>> Acompanhando log:' $latest.FullName; Get-Content $latest.FullName -Tail 20 -Wait"
