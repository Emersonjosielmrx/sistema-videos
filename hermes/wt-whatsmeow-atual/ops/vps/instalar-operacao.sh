#!/usr/bin/env bash
# instalar-operacao.sh — instala/atualiza NA VPS de produção o backup diário, os alertas
# (queda e disco) e o limite do journal. Idempotente: pode rodar de novo a qualquer hora.
# NÃO reinicia o hermes-call e NÃO mexe nos segredos (10-segredos.conf).
#
# Do PC (Git Bash, raiz do repositório):
#   scp -r ops/vps hermes-prod:/tmp/hermes-ops
#   ssh hermes-prod 'bash /tmp/hermes-ops/instalar-operacao.sh && rm -rf /tmp/hermes-ops'
#
# Depois, preencher /etc/hermes-call/alertas.env (e, se quiser cópia fora, backup.env).
set -euo pipefail
[ "$(id -u)" = 0 ] || { echo "rode como root"; exit 1; }
AQUI=$(cd "$(dirname "$0")" && pwd)
OPS=/opt/hermes-call/ops
log() { echo "[$(date '+%F %T')] $*"; }

log "scripts → $OPS"
install -d -m 755 "$OPS"
for f in hermes-alerta.sh hermes-backup.sh hermes-healthcheck.sh hermes-falhou.sh configurar-alertas.sh trancar-servico.sh fechar-ssh-senha.sh; do
  install -m 755 "$AQUI/$f" "$OPS/$f"
done

log "pastas de estado/backup/gravações"
install -d -m 700 /etc/hermes-call /var/backups/hermes-call
install -d -m 750 /var/lib/hermes-call /var/lib/hermes-call/recordings /var/lib/hermes-call/alertas

for f in alertas.env backup.env; do
  if [ ! -e "/etc/hermes-call/$f" ]; then
    install -m 600 "$AQUI/exemplos/$f.exemplo" "/etc/hermes-call/$f"
    log "criado /etc/hermes-call/$f (MODELO vazio — preencha)"
  else
    chmod 600 "/etc/hermes-call/$f"
    log "/etc/hermes-call/$f já existe (mantido)"
  fi
done

log "units systemd"
for u in hermes-backup.service hermes-backup.timer hermes-healthcheck.service hermes-healthcheck.timer 'hermes-call-falhou@.service'; do
  install -m 644 "$AQUI/systemd/$u" "/etc/systemd/system/$u"
done
install -d -m 755 /etc/systemd/system/hermes-call.service.d
install -m 644 "$AQUI/systemd/hermes-call.service.d/20-alerta-falha.conf" /etc/systemd/system/hermes-call.service.d/20-alerta-falha.conf
install -d -m 755 /etc/systemd/journald.conf.d
install -m 644 "$AQUI/systemd/journald.conf.d/50-hermes-tamanho.conf" /etc/systemd/journald.conf.d/50-hermes-tamanho.conf

systemctl daemon-reload
systemctl enable --now hermes-backup.timer hermes-healthcheck.timer
# O journald NÃO é reiniciado aqui (a VPS é compartilhada; não mexemos no log dos outros
# serviços sem decisão da dona). O teto de 2 GB vale no próximo reinício do journald/VPS.

log "pronto. Conferir:"
systemctl list-timers 'hermes-*' --no-pager || true
systemctl show hermes-call -p OnFailure --value || true
journalctl --disk-usage || true
echo
echo "Próximos passos:"
echo "  1. Preencher /etc/hermes-call/alertas.env (ALERTA_TG_TOKEN / ALERTA_TG_CHAT) e testar:"
echo "       $OPS/hermes-alerta.sh 'teste de aviso do Hermes'"
echo "  2. (Recomendado) RCLONE_REMOTE em /etc/hermes-call/backup.env"
echo "  3. Rodar um backup agora e ver o resultado:"
echo "       systemctl start hermes-backup.service; journalctl -u hermes-backup -n 30 --no-pager"
echo "  4. Journal: teto de 2 GB instalado, mas só vale no próximo reinício do journald/VPS"
echo "     (para aplicar já, se a dona quiser: systemctl restart systemd-journald)."
