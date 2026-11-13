@echo off
REM Abre o Chrome do perfil dedicado de um canal para logar UMA vez (o postador pelo navegador usa essa sessao).
REM Depois de logar, abra studio.youtube.com nesse mesmo Chrome para conferir o canal e feche a janela.
cd /d D:\postador-de-videos
set PYTHONUTF8=1
echo Canais sem login: manhwareact animescomia cenareact cartuchoreact forjareact mundoquenaoexiste
echo                   historiasemframes fiodameada assistiainvestimentos inovaremanhwabr inovare_ind inovare_eng inovare_thai
set /p SLUG=Qual canal (slug)?
D:\manhwa-react\.venv\Scripts\python.exe bin\youtube_web_poster.py --logar %SLUG%
pause
