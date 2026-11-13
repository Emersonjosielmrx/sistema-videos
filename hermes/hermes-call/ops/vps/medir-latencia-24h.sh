#!/usr/bin/env bash
# ops/vps/medir-latencia-24h.sh — mede pausas da VPS por 24 horas
#
# O que faz:
#   A cada minuto, acorda e anota quanto tempo passou desde a última medição.
#   Se passou muito mais que 1 minuto, é porque a máquina física pausou o processo.
#
# Como usar:
#   1. Copiar para cada VPS: scp ops/vps/medir-latencia-24h.sh usuario@vps:/tmp/
#   2. Rodar em cada uma (em background): ssh usuario@vps "nohup bash /tmp/medir-latencia-24h.sh produção > /tmp/latencia-24h.log 2>&1 &"
#   3. Amanhã, baixar os logs: scp usuario@vps:/tmp/latencia-24h.log latencia-prod-24h.log
#
# Argumento: nome da VPS (ex: "produção", "teste", "chatwoot") — vai no log

set -euo pipefail

NOME="${1:-vps}"
DURACAO=$((24 * 60))  # 24 horas em minutos
INTERVALO=60          # 1 minuto em segundos

echo "=== Medição de latência: $NOME ==="
echo "Início: $(date '+%Y-%m-%d %H:%M:%S')"
echo "Duração: ${DURACAO} minutos (24 horas)"
echo "Intervalo: ${INTERVALO}s (1 minuto)"
echo

ultima=$(date +%s)
total_atrasos=0
pior_atraso=0
medicoes=0

for i in $(seq 1 "$DURACAO"); do
  sleep "$INTERVALO"

  agora=$(date +%s)
  decorrido=$((agora - ultima))
  atraso=$((decorrido - INTERVALO))

  if [ $atraso -gt 0 ]; then
    total_atrasos=$((total_atrasos + atraso))
    [ $atraso -gt $pior_atraso ] && pior_atraso=$atraso
    echo "$(date '+%Y-%m-%d %H:%M:%S') | minuto $i/$DURACAO | atraso: ${atraso}s (decorrido: ${decorrido}s)"
  fi

  ultima=$agora
  medicoes=$i
done

echo
echo "=== Resumo: $NOME ==="
echo "Término: $(date '+%Y-%m-%d %H:%M:%S')"
echo "Medições: $medicoes"
echo "Total de atrasos: ${total_atrasos}s"
echo "Pior atraso: ${pior_atraso}s"
echo "Média de atraso por medição: $(awk "BEGIN {printf \"%.2f\", $total_atrasos / $medicoes}")s"
