@echo off
rem Desliga o melhorador dos CORTES (as mudancas que ele ja fez ficam; pra voltar uma, ver o historico em
rem D:\recapd-ambientes\producao\bin\cortes_ajustes.json).
D:\veo\venv\Scripts\python.exe -c "import sys; sys.path.insert(0, r'D:\video-fila'); import controle; controle.mudar('melhorador_cortes', 'producao', False, 'desligado pela dona (DESLIGAR_MELHORADOR.bat)')"
schtasks /Change /TN Cortes_Melhorador /DISABLE
echo Melhorador dos Cortes DESLIGADO.
pause
