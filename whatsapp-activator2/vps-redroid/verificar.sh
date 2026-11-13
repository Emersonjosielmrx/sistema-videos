#!/usr/bin/env bash
# Confere se o Android/WhatsApp da VPS esta de pe. So le e tira um print; nao toca na tela
# e nao apaga nada. Pode rodar com a conta ja ativada.
set -u
cd /opt/vps-redroid 2>/dev/null || { echo "ERRO: /opt/vps-redroid nao existe"; exit 1; }
ADB="adb -s 127.0.0.1:5555"
adb connect 127.0.0.1:5555 >/dev/null 2>&1

echo "===== 1. Contêiner (espera: Up ...)"
docker ps --filter name=redroid --format '{{.Names}} | {{.Status}} | {{.Image}}'

echo
echo "===== 2. Android ligado (espera: 1)"
$ADB shell getprop sys.boot_completed

echo
echo "===== 3. WhatsApp instalado (espera: package:...)"
$ADB shell pm path com.whatsapp
$ADB shell dumpsys package com.whatsapp | grep -m1 versionName

echo
echo "===== 4. WhatsApp rodando e em que tela"
echo "pid: $($ADB shell pidof com.whatsapp)"
$ADB shell dumpsys window | grep -i mCurrentFocus

echo
echo "===== 5. Print da tela -> /opt/vps-redroid/tela-final.png"
echo "      (traga com: scp hermes-bloqueio:/opt/vps-redroid/tela-final.png .)"
$ADB exec-out screencap -p > /opt/vps-redroid/tela-final.png
ls -l /opt/vps-redroid/tela-final.png

echo
echo "===== 6. Manutenção automática (2x por semana)"
systemctl list-timers redroid-manter-vivo.timer --no-pager | head -3
echo "log:"; cat /opt/vps-redroid/manter-vivo.log 2>/dev/null || echo "(vazio)"

echo
echo "===== 7. Recursos"
free -h | head -2
docker stats --no-stream --format '{{.Name}} | CPU {{.CPUPerc}} | MEM {{.MemUsage}}' redroid
df -h / | tail -1

echo
echo "===== 8. Kernel e binder (kernel SEM 'cloud'; binders em 666)"
uname -r
stat -c '%n %a' /dev/binder /dev/hwbinder /dev/vndbinder

echo
echo "===== 9. A conta (nunca apagar depois de ativada)"
du -sh /opt/vps-redroid/android-data 2>/dev/null
