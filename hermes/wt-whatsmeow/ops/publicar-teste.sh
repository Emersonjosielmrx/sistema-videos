#!/usr/bin/env bash
# ops/publicar-teste.sh — publica o commit atual (HEAD) na VPS de TESTE (209.145.60.53),
# pra ensaiar antes da produção. Rodar no Git Bash, na raiz D:\hermes\pc-base:
#   bash ops/publicar-teste.sh           compila a imagem na VPS de teste e troca o serviço
#   bash ops/publicar-teste.sh --voltar  volta o serviço pra imagem anterior (docker service rollback)
#
# A VPS de teste também hospeda OUTROS projetos: este script só mexe no serviço do Hermes.
# Site de teste: https://hermescall.inovareinteligenciaartificial.com
set -euo pipefail
cd "$(dirname "$0")/.."

HOST=hermes-staging
SVC=hermes_call_refactor_hermes-call-refactor
ssh_() { ssh -o BatchMode=yes -o ConnectTimeout=15 "$HOST" "$@"; }

if [ "${1:-}" = "--voltar" ]; then
  ssh_ "docker service rollback --quiet $SVC >/dev/null && docker service ls --filter name=$SVC --format '{{.Replicas}} {{.Image}}'"
  exit 0
fi

[ -z "$(git status --porcelain --untracked-files=no)" ] || { echo "PAROU: há alterações não commitadas."; exit 1; }
CURTO=$(git rev-parse --short=7 HEAD)
VERSAO=$(tr -d '\r\n ' < VERSION)
TAG="hermes-call:v${VERSAO}-${CURTO}"
echo "== Compilando $TAG na VPS de teste (leva ~10 min)"
git -c core.autocrlf=false archive --format=tar HEAD | ssh_ "set -e; B=/opt/hermes-build-staging; rm -rf \$B; mkdir -p \$B; tar -x -C \$B; cd \$B;
  docker build -q --build-arg APP_VERSION=v$VERSAO --build-arg APP_CHANNEL=teste -t $TAG . >/dev/null"
echo "== Trocando o serviço (backup da definição em /root na VPS)"
ssh_ "docker service inspect $SVC > /root/backup-$SVC-\$(date +%Y%m%d-%H%M%S).json
  docker service update --quiet --detach=false --no-resolve-image --image $TAG $SVC >/dev/null
  sleep 15; docker service ls --filter name=$SVC --format '{{.Replicas}} {{.Image}}'"
curl -s -m 10 https://hermescall.inovareinteligenciaartificial.com/api/version; echo
echo "Se der problema: bash ops/publicar-teste.sh --voltar"
