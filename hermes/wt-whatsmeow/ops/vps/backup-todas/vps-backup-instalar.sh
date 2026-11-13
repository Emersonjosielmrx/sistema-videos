#!/usr/bin/env bash
# vps-backup-instalar.sh — roda NA VPS QUE VAI SER GUARDADA (teste 209, a 157), pela DONA. Recebe pela
# entrada a chave PÚBLICA de backup da produção e:
#   1. instala o exportador em /usr/local/sbin/vps-backup-exportar;
#   2. autoriza essa chave a rodar SÓ o exportador, e só vindo do endereço da produção
#      (comando forçado, sem terminal, sem túnel). A chave não serve para entrar na máquina.
# Não instala programa nenhum, não agenda nada e não manda nada para fora: quem busca é a produção.
#
# No PowerShell do PC (um por VPS):
#   ssh hermes-prod "/opt/hermes-call/ops/backup-vps.sh chave-publica" | ssh hermes-staging "bash /root/vps-backup-instalar.sh"
#   ssh hermes-prod "/opt/hermes-call/ops/backup-vps.sh chave-publica" | ssh hermes-bloqueio "bash /root/vps-backup-instalar.sh"
# Para desfazer:  bash /root/vps-backup-instalar.sh remover
set -euo pipefail

ORIGEM=${ORIGEM:-62.171.128.241}          # endereço da produção: só ela pode usar a chave
FONTE=/root/vps-backup-exportar
DEST=/usr/local/sbin/vps-backup-exportar
AK=/root/.ssh/authorized_keys
MARCA=backup-da-producao

die() { echo "PAROU: $*" >&2; exit 1; }
[ "$(id -u)" = 0 ] || die "rode como root"

tirar_chave() { [ -f "$AK" ] && sed -i "/ $MARCA\$/d" "$AK"; return 0; }

if [ "${1:-}" = "remover" ]; then
  tirar_chave; rm -f "$DEST"
  echo "removido: a chave de backup não entra mais e o exportador foi apagado."
  exit 0
fi

PUB=$(tr -d '\r' | grep -m1 -E '^ssh-ed25519 AAAA[A-Za-z0-9+/=]{40,}' || true)
[ -n "$PUB" ] || die "não recebi a chave pública da produção (rode o comando inteiro, com o | no meio)."
TIPO=$(echo "$PUB" | awk '{print $1}'); CORPO=$(echo "$PUB" | awk '{print $2}')
[ -f "$FONTE" ] || die "falta $FONTE (o agente copia esse arquivo antes)."
bash -n "$FONTE" || die "o exportador está com erro de sintaxe."

install -m 700 "$FONTE" "$DEST"
mkdir -p /root/.ssh; chmod 700 /root/.ssh; touch "$AK"; chmod 600 "$AK"
cp -p "$AK" "$AK.antes-do-backup-$(date +%Y%m%d-%H%M%S)"
tirar_chave
printf 'command="%s",from="%s",no-port-forwarding,no-agent-forwarding,no-X11-forwarding,no-pty %s %s %s\n' \
  "$DEST" "$ORIGEM" "$TIPO" "$CORPO" "$MARCA" >> "$AK"

echo "== $(hostname): exportador instalado e chave de backup autorizada (só para o exportador, só vinda de $ORIGEM)"
echo "   chaves no authorized_keys: $(grep -cvE '^\s*(#|$)' "$AK") (a de backup é a que termina em $MARCA)"
echo "   o que vai ser guardado daqui:"
"$DEST" lista 2>/dev/null | awk '{c[$1]++; if ($1=="semanal") mb+=$3} END {printf "      todo dia: %d item(ns) (bancos, n8n, definições) | no domingo: %d item(ns), ~%d MB | de fora por tamanho: %d\n", c["diario"], c["semanal"], mb, c["grande"]}'
