#!/usr/bin/env bash
# Liga o Android (se estiver desligado), abre o WhatsApp por alguns minutos para o
# WhatsApp Web não ser desconectado, e desliga de novo se estava desligado.
# Roda sozinho pelo agendamento; também pode ser rodado à mão:  sudo bash manter-vivo.sh
set -euo pipefail
. "$(dirname "$0")/comum.sh"
cd "$KIT_DIR"
MINUTOS="${MINUTOS:-5}"

estava=$(docker inspect -f '{{.State.Running}}' redroid 2>/dev/null || echo false)
docker compose up -d
espera_android 300 || die "o Android não ligou"
abre_whatsapp || die "não consegui abrir o WhatsApp"
ok "WhatsApp aberto; esperando ${MINUTOS} min para ele sincronizar"
sleep "${MINUTOS}m"
if [ "$estava" != true ]; then
  docker compose stop
  ok "Android desligado de novo (estava desligado antes)"
fi
echo "$(date -Is) ok" >> "$KIT_DIR/manter-vivo.log"
