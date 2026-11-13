@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d D:\manhwa-react
title ManhwaReact - aprovar videos prontos
echo ============================================================
echo  Revisar os videos prontos (react + historias) antes de postar
echo  Cada video abre no player. Responda:
echo    a = aprovar   r = rejeitar   p = pular   s = sair
echo  Os aprovados entram na agenda da rede: 1 por canal por dia,
echo  no horario de cada canal. Sobem sozinhos enquanto a
echo  POSTAGEM AUTOMATICA estiver LIGADA.
echo ============================================================
.venv\Scripts\python.exe manhwareact.py rede --aprovar
echo.
echo  Plano dos proximos 3 dias (so simulacao, nada sobe agora):
.venv\Scripts\python.exe manhwareact.py rede --simular --dias 3
pause
