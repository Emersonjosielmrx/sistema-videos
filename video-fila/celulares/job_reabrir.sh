#!/data/data/com.termux/files/usr/bin/sh
# job_reabrir.sh — chamado pelo JobScheduler do ANDROID (termux-job-scheduler, a cada 15 min, persiste no reboot).
# 12/11 dona: "coloque os apps pra abrir quando fechar ou de x em x horas". O crond/vigia rodam DENTRO do Termux e
# morrem quando o Android fecha o Termux; este job o Android acorda mesmo com o Termux fechado: sobe crond/sshd e
# traz o Termux e o Tailscale de volta.
termux-wake-lock 2>/dev/null
pgrep -x crond >/dev/null || crond
pgrep -x sshd >/dev/null || sshd
if ! ifconfig 2>/dev/null | grep -q "inet 100\."; then
  am start --user 0 -n com.tailscale.ipn/.MainActivity >/dev/null 2>&1
fi
am start --user 0 -n com.termux/.app.TermuxActivity >/dev/null 2>&1
echo "$(date '+%d/%m %H:%M') job do Android rodou" >> ~/vigia_celular.log
