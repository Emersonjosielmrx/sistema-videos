@echo off
rem Desliga o melhorador automatico do Claude Code Video (o que ja mudou fica; o experimento aberto para de ser julgado)
cd /d D:\claude-code-video
"D:\veo\venv\Scripts\python.exe" melhorador.py desligar
echo.
echo Melhorador DESLIGADO.
pause
