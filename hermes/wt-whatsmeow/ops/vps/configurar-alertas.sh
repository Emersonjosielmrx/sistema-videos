#!/usr/bin/env bash
# configurar-alertas.sh — preenche /etc/hermes-call/alertas.env (token e chat do bot do Telegram
# que recebe os avisos de operação: backup, queda do serviço, disco) e manda um aviso de teste.
# Roda NA VPS, como root, pela dona: `ssh -t hermes-prod /opt/hermes-call/ops/configurar-alertas.sh`
# (ou dois cliques em ops\LIGAR-AVISOS-TELEGRAM.bat no PC).
#
# Achado de 15/10/2026: o arquivo existia desde 03/10 com os dois valores vazios, então nenhum
# aviso chegava (o backup das VPS falhou 7 dias seguidos sem ninguém saber).
# O token não aparece na tela, não vai para o journal e fica só no arquivo (600).
set -euo pipefail
[ "$(id -u)" = 0 ] || { echo "rode como root"; exit 1; }
CONF=/etc/hermes-call/alertas.env
ALERTA=/opt/hermes-call/ops/hermes-alerta.sh

echo
echo "AVISOS DE OPERAÇÃO DO HERMES NO TELEGRAM"
echo "---------------------------------------"
echo "Pode ser o mesmo bot que o Hermes já usa. Para descobrir o chat id: mande uma mensagem"
echo "ao bot e abra https://api.telegram.org/bot<TOKEN>/getUpdates no navegador (campo chat.id)."
echo
read -rsp "Token do bot (não aparece ao digitar): " TOKEN; echo
read -rp  "Chat id que recebe os avisos: " CHAT
TOKEN=${TOKEN//[[:space:]]/}; CHAT=${CHAT//[[:space:]]/}
[ -n "$TOKEN" ] && [ -n "$CHAT" ] || { echo "token ou chat vazio: nada foi alterado"; exit 1; }

# Confere o token no Telegram sem mandar nada (a URL vai pelo stdin, não aparece em ps).
if ! printf 'url = "https://api.telegram.org/bot%s/getMe"\n' "$TOKEN" | curl -sS -m 15 -K - 2>/dev/null | grep -q '"ok":true'; then
  echo "O Telegram recusou esse token: nada foi alterado."; exit 1
fi

umask 077
[ -f "$CONF" ] && cp -a "$CONF" "$CONF.bak-$(date +%Y%m%d-%H%M)"
install -d -m 700 /etc/hermes-call
cat > "$CONF" <<EOF
# /etc/hermes-call/alertas.env — avisos de operação no Telegram (backup, queda, disco).
# Preenchido em $(date '+%d/%m/%Y %H:%M') por configurar-alertas.sh. NUNCA versionar.
ALERTA_TG_TOKEN=$TOKEN
ALERTA_TG_CHAT=$CHAT
# Repetir o MESMO aviso no máximo a cada N minutos (antirrepetição).
ALERTA_REPETIR_MIN=30
EOF
chmod 600 "$CONF"

echo
if "$ALERTA" "✅ Avisos de operação do Hermes ligados. A partir de agora: backup com falha, serviço caído e disco cheio avisam aqui." 2>&1 | grep -q 'sem /etc/hermes-call'; then
  echo "O aviso NÃO saiu (o script não leu o arquivo). Confira $CONF."; exit 1
fi
echo "AVISO DE TESTE ENVIADO. Confira no Telegram. Arquivo: $CONF (600)."
echo
echo "Opcional, para o próprio Hermes avisar quando a linha do WhatsApp cair ou for bloqueada:"
echo "  o mesmo token/chat em HERMES_MONITOR_BOT_TOKEN / HERMES_MONITOR_CHAT_ID (trancar-servico.sh faz isso)."
