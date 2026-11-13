#!/usr/bin/env bash
# ops/vps/iniciar-medicao-3vps.sh — inicia medição de 24h nas 3 VPS
#
# Roda o medir-latencia-24h.sh nas três VPS em paralelo.
# Amanhã (2026-10-07 às 21h), baixa os logs e gera o resumo.

set -euo pipefail
cd "$(dirname "$0")/../.."

PRODUCAO=hermes-prod
STAGING=hermes-staging
BLOQUEIO=hermes-bloqueio

echo "=== Iniciando medição de 24h nas 3 VPS ==="
echo "Horário: $(date '+%Y-%m-%d %H:%M:%S')"
echo

# Envia o script para cada VPS
for HOST in "$PRODUCAO" "$STAGING" "$BLOQUEIO"; do
  echo "Enviando script para $HOST..."
  scp -q ops/vps/medir-latencia-24h.sh "$HOST:/tmp/" || {
    echo "ERRO: não consegui enviar para $HOST"
    continue
  }
done

echo
echo "=== Iniciando medições (background) ==="

# Produção (62.171.128.241 - hermes-prod)
echo "Iniciando em $PRODUCAO (produção - Hermes, bancada, Atlas, Lucrativa)..."
ssh "$PRODUCAO" "nohup bash /tmp/medir-latencia-24h.sh produção > /tmp/latencia-24h.log 2>&1 &"
echo "  PID: $(ssh "$PRODUCAO" "pgrep -f 'medir-latencia-24h.sh produção' | head -1")"

# Staging (209.145.60.53 - hermes-staging)
echo "Iniciando em $STAGING (staging - n8n, ~48 serviços)..."
ssh "$STAGING" "nohup bash /tmp/medir-latencia-24h.sh staging > /tmp/latencia-24h.log 2>&1 &"
echo "  PID: $(ssh "$STAGING" "pgrep -f 'medir-latencia-24h.sh staging' | head -1")"

# Bloqueio (157.173.207.22 - hermes-bloqueio)
echo "Iniciando em $BLOQUEIO (bloqueio - Chatwoot, n8n, OmniRoute)..."
ssh "$BLOQUEIO" "nohup bash /tmp/medir-latencia-24h.sh bloqueio > /tmp/latencia-24h.log 2>&1 &"
echo "  PID: $(ssh "$BLOQUEIO" "pgrep -f 'medir-latencia-24h.sh bloqueio' | head -1")"

echo
echo "=== Medições iniciadas ==="
echo "Duração: 24 horas (até 2026-10-07 às 21h)"
echo
echo "Para conferir o progresso:"
echo "  ssh $PRODUCAO 'tail -20 /tmp/latencia-24h.log'"
echo "  ssh $STAGING 'tail -20 /tmp/latencia-24h.log'"
echo "  ssh $BLOQUEIO 'tail -20 /tmp/latencia-24h.log'"
echo
echo "Amanhã, para baixar os resultados:"
echo "  bash ops/vps/coletar-medicao-3vps.sh"
