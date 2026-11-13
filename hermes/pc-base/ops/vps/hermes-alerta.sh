#!/usr/bin/env bash
# hermes-alerta.sh — manda um aviso no Telegram da dona/admin. Roda NA VPS
# (instalado em /opt/hermes-call/ops/hermes-alerta.sh por ops/vps/instalar-operacao.sh).
#
#   hermes-alerta.sh "texto do aviso"
#   hermes-alerta.sh --chave disco "texto"   # antirrepetição: a mesma chave só repete
#                                            # depois de ALERTA_REPETIR_MIN (padrão 60) min
#   hermes-alerta.sh --resolvido disco "texto"  # avisa "voltou ao normal" só se a chave
#                                               # estava em alerta, e limpa a chave
#
# Config (fora do git, chmod 600): /etc/hermes-call/alertas.env
#   ALERTA_TG_TOKEN=<token do bot de avisos>     (pode ser o mesmo do HERMES_MONITOR_BOT_TOKEN)
#   ALERTA_TG_CHAT=<chat_id que recebe>          (pode ser o mesmo do HERMES_MONITOR_CHAT_ID)
#   ALERTA_REPETIR_MIN=60                        (opcional)
# Sem config: só escreve no journal (não falha quem chamou).
set -euo pipefail

CONF=${ALERTA_CONF:-/etc/hermes-call/alertas.env}
ESTADO=${ALERTA_ESTADO_DIR:-/var/lib/hermes-call/alertas}
# shellcheck disable=SC1090
[ -r "$CONF" ] && . "$CONF"
REPETIR_MIN=${ALERTA_REPETIR_MIN:-60}

CHAVE=""; MODO=alerta
case "${1:-}" in
  --chave)     CHAVE=$2; shift 2 ;;
  --resolvido) CHAVE=$2; MODO=resolvido; shift 2 ;;
esac
TEXTO="${*:-aviso sem texto}"

# Nunca manda segredo pro Telegram (mesmas regras do redact.go do servidor).
mascara() {
  sed -E \
    -e 's/bot[0-9]+:[A-Za-z0-9_-]{20,}/bot<redacted>/g' \
    -e 's/\b[0-9]{6,12}:[A-Za-z0-9_-]{30,}/<redacted>/g' \
    -e 's/([?&](key|apiKey|api_key|token|access_token|password|secret)=)[^&[:space:]"]+/\1<redacted>/Ig' \
    -e 's/\b(sk-|sk_|gsk_|dckr_pat_|ghp_)[A-Za-z0-9_-]{10,}/\1<redacted>/g' \
    -e 's/\bAIza[0-9A-Za-z_-]{30,}/AIza<redacted>/g' \
    -e 's/([Bb]earer[[:space:]]+)[A-Za-z0-9._~+\/=-]{8,}/\1<redacted>/g' \
    -e 's#(postgres(ql)?://[^:/@[:space:]]+:)[^@[:space:]]+@#\1<redacted>@#g'
}

if [ -n "$CHAVE" ]; then
  mkdir -p "$ESTADO"
  F="$ESTADO/$(echo "$CHAVE" | tr -c 'A-Za-z0-9_.-' '_')"
  if [ "$MODO" = resolvido ]; then
    [ -f "$F" ] || exit 0          # não estava em alerta: nada a dizer
    rm -f "$F"
  else
    if [ -f "$F" ] && [ $(( $(date +%s) - $(stat -c %Y "$F") )) -lt $(( REPETIR_MIN * 60 )) ]; then
      exit 0                       # já avisou há pouco
    fi
    touch "$F"
  fi
fi

MSG="$(printf '%s\n🖥️ %s · %s' "$TEXTO" "$(hostname)" "$(date '+%d/%m %H:%M')" | mascara | head -c 3800)"
echo "[hermes-alerta] $MSG"
if [ -z "${ALERTA_TG_TOKEN:-}" ] || [ -z "${ALERTA_TG_CHAT:-}" ]; then
  echo "[hermes-alerta] sem $CONF (ALERTA_TG_TOKEN/ALERTA_TG_CHAT): aviso só no journal" >&2
  exit 0
fi
# O token vai na URL do Telegram; a URL é passada ao curl pelo stdin (-K -), não na
# linha de comando — assim não aparece em `ps`/journal de outros usuários da VPS.
printf 'url = "https://api.telegram.org/bot%s/sendMessage"\n' "$ALERTA_TG_TOKEN" \
  | curl -sS -m 15 -o /dev/null -K - \
      --data-urlencode "chat_id=$ALERTA_TG_CHAT" \
      --data-urlencode "text=$MSG" \
      --data-urlencode "disable_web_page_preview=true" 2>/dev/null \
  || echo "[hermes-alerta] falha ao enviar pro Telegram" >&2
exit 0
