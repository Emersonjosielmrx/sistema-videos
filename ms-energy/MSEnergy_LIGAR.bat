@echo off
REM ============================================================
REM  MS Energy — GERAR 2 SHORTS AGORA (fora do horario)
REM  A geracao diaria e automatica (controlador central, ~00:01). Este botao roda a MESMA geracao uma vez:
REM  2 shorts (1 com foto real do Instagram + 1 com consultor), com a trava de qualidade.
REM  22/10: antes ligava o loop infinito run_loop_ms_energy.bat (gastava credito sem parar) e apagava a pausa
REM  geral do Veo (PAUSE_SYSTEM).
REM ============================================================
title MS-Energy-GERAR
cd /d "D:\ms-energy"
echo Gerando 2 shorts do MS Energy (leva uns 15 a 30 minutos). Acompanhe em D:\ms-energy\logs\gerar_diario.log
call "D:\ms-energy\bin\cron_gerar_ms_energy.bat" 2
echo.
echo Terminou. Shorts aprovados: D:\ms-energy\videos\shorts_veo  ^|  reprovados: D:\ms-energy\videos\_revisar
timeout /t 15 >nul
