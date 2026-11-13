@echo off
rem Liga o melhorador dos CORTES (dona: "so liga no meu sinal"). Ele continua em modo SOMBRA ate voce mudar
rem "sombra": false em D:\recapd-ambientes\producao\bin\cortes_melhorador.json.
D:\veo\venv\Scripts\python.exe -c "import sys; sys.path.insert(0, r'D:\video-fila'); import controle; controle.mudar('melhorador_cortes', 'producao', True, 'ligado pela dona (LIGAR_MELHORADOR.bat)')"
schtasks /Change /TN Cortes_Melhorador /ENABLE
echo Melhorador dos Cortes LIGADO.
pause
