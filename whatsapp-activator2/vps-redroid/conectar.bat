@echo off
setlocal
rem ===== ajuste aqui =====
rem apelido do ~/.ssh/config deste PC (hermes-bloqueio, hermes-staging...) ou root@IP
set VPS=hermes-bloqueio
set PORTA_VPS=5555
rem porta no PC (15555 para nao brigar com o emulador do Windows, que usa a 5555)
set PORTA_PC=15555
rem =======================
cd /d "%~dp0"

if "%VPS%"=="ESCOLHA_A_VPS" (
  echo Abra este arquivo no Bloco de Notas e troque ESCOLHA_A_VPS pelo apelido da VPS, ex.: hermes-bloqueio
  pause & exit /b 1
)
if not exist "scrcpy\scrcpy.exe" (
  echo Falta o scrcpy. Baixe "scrcpy-win64-....zip" em https://github.com/Genymobile/scrcpy/releases
  echo e extraia o conteudo numa pasta "scrcpy" ao lado deste arquivo.
  pause & exit /b 1
)
where ssh >nul 2>&1 || (
  echo O Windows nao tem o cliente SSH. Configuracoes ^> Aplicativos ^> Recursos opcionais ^> Cliente OpenSSH.
  pause & exit /b 1
)

echo Abrindo o tunel para a VPS numa janela separada. Se ela pedir senha, a chave SSH nao esta
echo configurada neste PC: feche e avise. Nao digite senha.
start "tunel-whatsapp-vps" ssh -N -o BatchMode=yes -o ServerAliveInterval=30 -o ExitOnForwardFailure=yes -L %PORTA_PC%:127.0.0.1:%PORTA_VPS% %VPS%
echo Esperando o tunel abrir (ate 60 s)...
set /a tentativas=0
:espera_tunel
netstat -an | find ":%PORTA_PC% " | find "LISTENING" >nul
if not errorlevel 1 goto tunel_pronto
set /a tentativas+=1
if %tentativas% geq 60 (
  echo O tunel nao abriu em 60 s. Veja a mensagem na janela "tunel-whatsapp-vps" e mande.
  pause
  exit /b 1
)
timeout /t 1 /nobreak >nul
goto espera_tunel
:tunel_pronto
echo Tunel aberto.

rem Liga o Android se estiver desligado (o agendamento pode te-lo desligado).
ssh -o BatchMode=yes %VPS% "cd /opt/vps-redroid 2>/dev/null && bash -c '. ./comum.sh; docker compose up -d' >/dev/null 2>&1; true"

scrcpy\adb.exe connect 127.0.0.1:%PORTA_PC%
scrcpy\scrcpy.exe -s 127.0.0.1:%PORTA_PC% --no-audio --max-size=1024 --video-bit-rate=2M --window-title="WhatsApp na VPS"
scrcpy\adb.exe disconnect 127.0.0.1:%PORTA_PC% >nul 2>&1

taskkill /fi "WINDOWTITLE eq tunel-whatsapp-vps*" /f >nul 2>&1
echo Tunel fechado. Pode fechar esta janela.
pause
