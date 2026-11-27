#!/bin/bash
# /opt/orcamentos-ms/instalar_vps.sh — sobe/atualiza o painel na VPS (62.171.128.241). Só toca em /opt/orcamentos-ms,
# no contêiner orcamentos-ms e no arquivo /opt/traefik-config/dynamic/orcamentos.yml. Não mexe em Hermes/Atlas/Lucrativa.
set -e
cd /opt/orcamentos-ms/servidor
mkdir -p dados
if [ "$1" = "--build" ] || ! docker image inspect orcamentos-ms:1 >/dev/null 2>&1; then
  docker compose build
fi
docker compose up -d
cp -f /opt/orcamentos-ms/traefik-orcamentos.yml /opt/traefik-config/dynamic/orcamentos.yml
for i in $(seq 1 30); do curl -fsS http://127.0.0.1:8101/saude >/dev/null 2>&1 && break; sleep 2; done
curl -fsS http://127.0.0.1:8101/saude && echo
docker ps --filter name=orcamentos-ms --format '{{.Names}} {{.Status}}'
