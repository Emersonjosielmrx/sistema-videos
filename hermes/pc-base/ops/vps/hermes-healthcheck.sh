#!/usr/bin/env bash
# hermes-healthcheck.sh — checagem a cada 5 min (timer hermes-healthcheck.timer). Roda NA
# VPS de produção. Instalado em /opt/hermes-call/ops/ por ops/vps/instalar-operacao.sh.
#
#   1. o servidor responde em http://127.0.0.1:8080/api/version? (tenta de novo após 30 s
#      antes de avisar — não dispara durante a troca de versão do ops/publicar.sh)
#   2. disco: algum sistema de arquivos importante acima de DISCO_LIMITE_PCT (85%)?
#
# Avisa no Telegram (hermes-alerta.sh) com ANTIRREPETIÇÃO: o mesmo problema só é
# avisado de novo depois de ALERTA_REPETIR_MIN (60 min); quando volta ao normal, manda
# um "✅ voltou" uma vez. Nunca reinicia nada sozinho.
set -euo pipefail

APP=/opt/hermes-call
ALERTA=${ALERTA:-$APP/ops/hermes-alerta.sh}
URL=${HEALTH_URL:-http://127.0.0.1:8080/api/version}
DISCO_LIMITE_PCT=${DISCO_LIMITE_PCT:-85}
# shellcheck disable=SC1091
[ -r /etc/hermes-call/alertas.env ] && . /etc/hermes-call/alertas.env

responde() { curl -s -m 10 "$URL" 2>/dev/null | grep -q '"version"'; }

# ---------- 1. servidor ----------
if responde; then
  "$ALERTA" --resolvido servidor-fora "✅ Hermes voltou a responder ($URL)."
else
  sleep "${HEALTH_RETRY_SEC:-30}"
  if responde; then
    "$ALERTA" --resolvido servidor-fora "✅ Hermes voltou a responder ($URL)."
  else
    estado=$(systemctl is-active hermes-call 2>/dev/null || true)
    "$ALERTA" --chave servidor-fora "🔴 HERMES FORA DO AR
$URL não respondeu (2 tentativas, 30 s de intervalo).
systemd: hermes-call = ${estado:-desconhecido}
Ver: journalctl -u hermes-call -n 80 · bash ops/status.sh"
  fi
fi

# ---------- 2. disco ----------
# Sistemas de arquivos onde moram o app, o banco, os backups e as gravações.
for alvo in / /opt /var/lib/postgresql /var/backups /var/lib/hermes-call; do
  [ -e "$alvo" ] || continue
  read -r fs pct mnt < <(df -P "$alvo" | awk 'NR==2{gsub("%","",$5); print $1, $5, $6}')
  chave="disco-$(echo "$mnt" | tr '/' '_')"
  if [ "$pct" -ge "$DISCO_LIMITE_PCT" ]; then
    "$ALERTA" --chave "$chave" "🟠 DISCO QUASE CHEIO na VPS do Hermes
$mnt ($fs) em ${pct}% (limite ${DISCO_LIMITE_PCT}%).
Maiores: journalctl --disk-usage · du -sh /var/backups/hermes-call /var/lib/hermes-call/recordings /opt/hermes-call/releases"
  else
    "$ALERTA" --resolvido "$chave" "✅ Disco $mnt voltou para ${pct}%."
  fi
done
exit 0
