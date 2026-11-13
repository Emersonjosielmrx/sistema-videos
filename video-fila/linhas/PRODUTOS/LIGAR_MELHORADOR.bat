@echo off
rem BOTÃO do dono: liga o melhorador automático da linha PRODUTOS no modo ENSAIO (só propõe e anota no DECISOES.md).
rem Para ele APLICAR sozinho (com backup e desfaz se a nota cair): LIGAR_MELHORADOR.bat aplicar
cd /d D:\postador-de-videos\bin
if /i "%1"=="aplicar" (
  D:\veo\venv\Scripts\python.exe -m produto.melhorador --ligar --aplicar
) else (
  D:\veo\venv\Scripts\python.exe -m produto.melhorador --ligar
)
pause
