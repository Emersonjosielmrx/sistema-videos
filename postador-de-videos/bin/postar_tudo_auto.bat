@echo off
REM PostadorDeVideos - roda 1x/dia, posta tudo que esta pronto
REM Chamado pelo schtasks "PostadorDeVideos"
REM Fluxo: 1) postar_tudo_hoje 2) postar_pos_final 3) TikTok CDP

set PYTHONUTF8=1

REM Botao DESLIGAR do desktop (manhwareact.py rede --desligar): pula o ciclo inteiro - nada sobe nem abre navegador
if exist D:\postador-de-videos\config\POSTAGEM_DESLIGADA.json (
    echo [%date% %time%] POSTAGEM AUTOMATICA DESLIGADA pelo botao - ciclo pulado >> D:\postador-de-videos\logs\postar_auto.log
    exit /b 0
)

echo [%date% %time%] === INICIO CICLO COMPLETO === >> D:\postador-de-videos\logs\postar_auto.log

REM --- Etapa 1: recap de ANIME (anime_publish grava postar.json categoria=animes; so sai com pronto=true) ---
REM 16/10 (dono; AB-01 de D:\veo\docs\PLANO_MELHORIAS_VEO.md): o Veo saiu daqui - vai ao ar limpo pela rede (etapa 2b).
REM A antiga etapa 2 (postar_pos_final: VO3 pos_final COM o slide de WhatsApp) saiu; script em bin\_legado\.
echo [%date% %time%] Inicio postar_tudo_hoje (animes) >> D:\postador-de-videos\logs\postar_auto.log
D:\veo\venv\Scripts\python.exe D:\postador-de-videos\bin\postar_tudo_hoje.py --so animes > D:\postador-de-videos\logs\postar_tudo_%date:~6,4%%date:~3,2%%date:~0,2%.log 2>&1
echo [%date% %time%] Fim postar_tudo_hoje (exit %ERRORLEVEL%) >> D:\postador-de-videos\logs\postar_auto.log

REM --- Etapa 2a: DESLIGADA 19/10 — limpar_veo agora e feita pelo controlador geral (D:\video-fila\controlador.py) ---
REM echo [%date% %time%] Inicio limpar_veo >> D:\postador-de-videos\logs\postar_auto.log
REM D:\manhwa-react\.venv\Scripts\python.exe D:\postador-de-videos\bin\limpar_veo.py --drive --max 40 > D:\postador-de-videos\logs\limpar_veo_%date:~6,4%%date:~3,2%%date:~0,2%.log 2>&1
REM echo [%date% %time%] Fim limpar_veo (exit %ERRORLEVEL%) >> D:\postador-de-videos\logs\postar_auto.log

REM --- Etapa 2b: REDE de canais (manhwareact.py rede): 1 video/dia por canal ativo (config
ede_canais.json), agente por canal, melhor horario ---
echo [%date% %time%] Inicio manhwa-react publicar >> D:\postador-de-videos\logs\postar_auto.log
D:\manhwa-react\.venv\Scripts\python.exe D:\manhwa-react\manhwareact.py rede > D:\postador-de-videos\logs\manhwa_react_%date:~6,4%%date:~3,2%%date:~0,2%.log 2>&1
echo [%date% %time%] Fim manhwa-react publicar (exit %ERRORLEVEL%) >> D:\postador-de-videos\logs\postar_auto.log

REM --- Etapa 3: TikTok CDP (o script abre o Chrome de cada conta so na hora do post e fecha; 15/10) ---
echo [%date% %time%] Inicio TikTok >> D:\postador-de-videos\logs\postar_auto.log
REM 16/10 (BX-09): com prazo - em 15/10 o TikTok travou e Instagram/limpar_usados/resumo nao rodaram
REM 18/10: 90 -> 150 min (16 contas x 1 a 3 por dia); o script para sozinho aos 135 para mandar o resumo/aviso
D:\veo\venv\Scripts\python.exe D:\postador-de-videos\bin\etapa.py 150 D:\postador-de-videos\logs\tiktok_%date:~6,4%%date:~3,2%%date:~0,2%.log -- D:\veo\venv\Scripts\python.exe D:\postador-de-videos\bin\postar_tiktok_auto.py --ate-min 135
echo [%date% %time%] Fim TikTok (exit %ERRORLEVEL%) >> D:\postador-de-videos\logs\postar_auto.log

REM --- Etapa 3b: Instagram - reaproveita como Reel o que ja saiu em outra rede (catalogo, config\reuso_plataformas.json) ---
echo [%date% %time%] Inicio Instagram >> D:\postador-de-videos\logs\postar_auto.log
REM 01/11: 60 -> 150 min (33 contas x ~3-4 min; com 60/90 as ultimas da lista nunca postavam)
D:\veo\venv\Scripts\python.exe D:\postador-de-videos\bin\etapa.py 150 D:\postador-de-videos\logs\instagram_%date:~6,4%%date:~3,2%%date:~0,2%.log -- D:\veo\venv\Scripts\python.exe D:\postador-de-videos\bin\postar_insta_auto.py
echo [%date% %time%] Fim Instagram (exit %ERRORLEVEL%) >> D:\postador-de-videos\logs\postar_auto.log

REM --- Etapa 4: Mover usados (postado em YT + TikTok) pra _usados ---
echo [%date% %time%] Inicio limpar_usados >> D:\postador-de-videos\logs\postar_auto.log
D:\veo\venv\Scripts\python.exe D:\postador-de-videos\bin\limpar_usados.py >> D:\postador-de-videos\logs\postar_auto.log 2>&1
echo [%date% %time%] Fim limpar_usados (exit %ERRORLEVEL%) >> D:\postador-de-videos\logs\postar_auto.log

REM --- Etapa 5: contas Google do Veo ainda logadas? (BX-07, 16/10; sem gerar nada; deslogada -> cooldown + Telegram) ---
D:\veo\venv\Scripts\python.exe D:\postador-de-videos\bin\etapa.py 15 D:\postador-de-videos\logs\postar_auto.log -- D:\veo\venv\Scripts\python.exe D:\veo\beta\sonda_contas_veo.py

REM --- Resumo: cota usada por canal, bloqueios e parada geral ---
D:\veo\venv\Scripts\python.exe D:\postador-de-videos\bin\politica.py >> D:\postador-de-videos\logs\postar_auto.log 2>&1

echo [%date% %time%] === FIM CICLO COMPLETO === >> D:\postador-de-videos\logs\postar_auto.log
