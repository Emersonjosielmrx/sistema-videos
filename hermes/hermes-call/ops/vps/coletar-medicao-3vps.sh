#!/usr/bin/env bash
# ops/vps/coletar-medicao-3vps.sh — baixa logs das 3 VPS e gera resumo
#
# Roda depois de 24h da iniciar-medicao-3vps.sh (2026-10-07 após 21h)

set -euo pipefail
cd "$(dirname "$0")/../.."

PRODUCAO=hermes-prod
STAGING=hermes-staging
BLOQUEIO=hermes-bloqueio
DESTINO=_temp_audio

mkdir -p "$DESTINO"

echo "=== Coletando logs das 3 VPS ==="
echo "Horário: $(date '+%Y-%m-%d %H:%M:%S')"
echo

# Baixa os logs
for HOST in "$PRODUCAO" "$STAGING" "$BLOQUEIO"; do
  case "$HOST" in
    "$PRODUCAO") NOME="producao" ;;
    "$STAGING") NOME="staging" ;;
    "$BLOQUEIO") NOME="bloqueio" ;;
  esac

  echo "Baixando de $HOST..."
  if scp -q "$HOST:/tmp/latencia-24h.log" "$DESTINO/latencia-${NOME}-24h.log" 2>/dev/null; then
    LINHAS=$(wc -l < "$DESTINO/latencia-${NOME}-24h.log")
    echo "  ✓ $LINHAS linhas salvas em $DESTINO/latencia-${NOME}-24h.log"
  else
    echo "  ✗ ERRO: não consegui baixar de $HOST"
  fi
done

echo
echo "=== Resumo das 3 VPS ==="
echo

for NOME in producao staging bloqueio; do
  LOG="$DESTINO/latencia-${NOME}-24h.log"

  if [ ! -f "$LOG" ]; then
    echo "[$NOME] LOG NÃO ENCONTRADO"
    continue
  fi

  echo "[$NOME]"
  grep "^===" "$LOG" | head -1 | sed 's/^=== /  /'
  grep "Término:" "$LOG" || echo "  (ainda rodando)"
  grep "Total de atrasos:" "$LOG" || echo "  (sem resumo ainda)"
  grep "Pior atraso:" "$LOG" || true
  grep "Média de atraso" "$LOG" || true
  echo
done

echo "=== Análise ==="
echo
echo "Arquivos salvos em $DESTINO/"
echo "  - latencia-producao-24h.log"
echo "  - latencia-staging-24h.log"
echo "  - latencia-bloqueio-24h.log"
echo
echo "Para ver os piores momentos de cada VPS:"
echo "  grep 'atraso:' $DESTINO/latencia-producao-24h.log | sort -t: -k4 -n | tail -20"
echo "  grep 'atraso:' $DESTINO/latencia-staging-24h.log | sort -t: -k4 -n | tail -20"
echo "  grep 'atraso:' $DESTINO/latencia-bloqueio-24h.log | sort -t: -k4 -n | tail -20"
