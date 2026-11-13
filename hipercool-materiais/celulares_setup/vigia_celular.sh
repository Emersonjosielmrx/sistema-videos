#!/data/data/com.termux/files/usr/bin/bash
# vigia_celular.sh — roda DENTRO do Termux de cada celular, 1 vez por minuto pelo crond (12/11, dona: "os S20 e os
# outros celulares ficam fechando os apps mesmo com a otimização de energia desligada; tem que ter um script nos celulares
# pra ficar abrindo os apps"). Loop com nohup morria junto com a sessão ssh do Termux — por isso é o crond que chama.
# Cada chamada: segura o wake-lock, sobe o sshd se caiu e, sem o IP 100.x do Tailscale, reabre o app do Tailscale.
# A cada 30 min traz o Termux pra frente (o Android mata menos app recém-usado). Log só de mudanças: ~/vigia_celular.log
# Instalação: python D:\video-fila\celulares.py vigia  (crontab "* * * * *", ~/.termux/boot/vigia e ~/.bashrc sobem o crond)
LOG=~/vigia_celular.log
termux-wake-lock 2>/dev/null
pgrep -x sshd >/dev/null || { sshd; echo "$(date '+%d/%m %H:%M') sshd subiu" >> $LOG; }
if ! ifconfig 2>/dev/null | grep -q "inet 100\."; then
  am start --user 0 -n com.tailscale.ipn/.MainActivity >/dev/null 2>&1
  echo "$(date '+%d/%m %H:%M') tailscale sem IP 100.x — reabri o app" >> $LOG
fi
if [ $(( $(date +%s) / 60 % 30 )) -eq 0 ]; then
  am start --user 0 -n com.termux/.app.TermuxActivity >/dev/null 2>&1
fi
exit 0
