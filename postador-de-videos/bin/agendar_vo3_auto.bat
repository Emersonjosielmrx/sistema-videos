@echo off
REM Agendador automatico VO3 — roda 1x/dia, agenda pro dia corrente
REM Chamado pelo schtasks "AgendadorVO3"
REM 16/10 (dono; AB-01 de D:\veo\docs\PLANO_MELHORIAS_VEO.md): DESARMADO. Tarefa desabilitada e agendar_vo3.py em
REM bin\_legado\ (agendava o pos_final COM o slide de WhatsApp, publico na hora). O Veo vai ao ar limpo pela rede.
echo [%date% %time%] AgendadorVO3 desarmado (16/10) - nada feito >> D:\postador-de-videos\logs\agendar_auto.log
exit /b 0

set PYTHONUTF8=1

REM Botao DESLIGAR do desktop (manhwareact.py rede --desligar): nao agenda nada
if exist D:\postador-de-videos\config\POSTAGEM_DESLIGADA.json (
    echo [%date% %time%] POSTAGEM AUTOMATICA DESLIGADA pelo botao - pulado >> D:\postador-de-videos\logs\agendar_auto.log
    exit /b 0
)

REM Calcula a data de hoje (YYYY-MM-DD)
for /f "tokens=*" %%d in ('powershell -Command "(Get-Date).ToString('yyyy-MM-dd')"') do set DIA=%%d

echo [%date% %time%] Agendando VO3 para %DIA% >> D:\postador-de-videos\logs\agendar_auto.log

D:\veo\venv\Scripts\python.exe D:\postador-de-videos\bin\agendar_vo3.py --dia %DIA% > D:\postador-de-videos\logs\agendar_vo3_%DIA%.log 2>&1

echo [%date% %time%] Fim (exit code %ERRORLEVEL%) >> D:\postador-de-videos\logs\agendar_auto.log
