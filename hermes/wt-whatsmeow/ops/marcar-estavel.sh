#!/usr/bin/env bash
# ops/marcar-estavel.sh — a versão que está NO AR vira a ESTÁVEL (a volta segura).
# Rode só depois de validar a versão nova (ligação de teste, painel, Telegram).
# A estável anterior continua guardada e protegida da limpeza.
set -euo pipefail
HOST=hermes-prod
REL=/opt/hermes-call/releases
ssh_() { ssh -o BatchMode=yes -o ConnectTimeout=15 "$HOST" "$@"; }
NO_AR=$(ssh_ "cat $REL/ATUAL")
ANTES=$(ssh_ "cat $REL/ESTAVEL 2>/dev/null || echo nenhuma")
ssh_ "$REL/hermes-release.sh marcar-estavel '$NO_AR'"
echo "== Versão estável agora: $NO_AR   (antes: $ANTES, continua guardada)"
