@echo off
REM cron_parceiro.bat [producao ou postar ou status] - Shorts do parceiro @kaijinre (dono 16/10/2026:
REM producao + postagem, 1 por canal por dia). Tarefas: ParceiroKaijinre-Producao (02:20) e
REM ParceiroKaijinre-Postagem (23:20 e 23:50), sem janela (D:\rodar_oculto.vbs).
REM Regras e canais: config\parceiro.json; ver bin\parceiro_diario.py.
REM Python do postador (D:\veo\venv tem tzdata pros fusos); a producao chama o anime_auto com o venv daqui.
REM Um log por acao: o cmd prende o arquivo do ">>" enquanto a producao roda (horas) e a postagem nem comecaria.
setlocal
set BASE=D:\recapd-ambientes\producao
set LOG=%BASE%\logs\parceiro_%~1.log
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d %BASE%
echo [%date% %time%] ===== %~1 ===== >> "%LOG%"
"D:\veo\venv\Scripts\python.exe" bin\parceiro_diario.py %~1 >> "%LOG%" 2>&1
echo [%date% %time%] %~1 terminou (codigo %ERRORLEVEL%) >> "%LOG%"
