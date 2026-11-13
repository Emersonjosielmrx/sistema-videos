#!/usr/bin/env bash
# ops/vps/listar-consumo-recursos.sh — lista TODOS os processos por CPU e RAM

set -euo pipefail

listar_recursos() {
  local HOST=$1
  local NOME=$2
  
  echo "=========================================="
  echo "VPS: $NOME"
  echo "=========================================="
  echo
  
  # TOP 50 por CPU
  echo "--- TOP 50 PROCESSOS POR CPU ---"
  ssh "$HOST" "ps aux --sort=-%cpu | head -51 | tail -50 | awk '{printf \"%-8s %5s %5s %s\n\", \$1, \$3\"%\", \$4\"%\", \$11}'" 2>&1
  echo
  
  # TOP 50 por RAM
  echo "--- TOP 50 PROCESSOS POR RAM ---"
  ssh "$HOST" "ps aux --sort=-%mem | head -51 | tail -50 | awk '{printf \"%-8s %5s %5s %s\n\", \$1, \$3\"%\", \$4\"%\", \$11}'" 2>&1
  echo
  
  # Serviços systemd com status
  echo "--- SERVIÇOS SYSTEMD (todos) ---"
  ssh "$HOST" "systemctl list-units --type=service --all --no-pager --no-legend | awk '{print \$1, \$3, \$4}' | grep -v 'systemd-\|user@\|getty@' | sort" 2>&1 | head -100
  echo
  
  # Docker containers com stats
  echo "--- DOCKER CONTAINERS (uso de recursos) ---"
  if ssh "$HOST" "command -v docker >/dev/null 2>&1"; then
    ssh "$HOST" "docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}' 2>/dev/null | head -60" 2>&1 || echo "Erro ao obter stats"
  else
    echo "(Docker não disponível)"
  fi
  echo
  echo
}

DESTINO=_temp_audio
mkdir -p "$DESTINO"

echo "=== CONSUMO DE RECURSOS NAS 3 VPS ==="
echo "Horário: $(date '+%Y-%m-%d %H:%M:%S')"
echo

listar_recursos hermes-prod "Produção (62.171.128.241)" | tee "$DESTINO/recursos-producao.txt"
listar_recursos hermes-staging "Staging (209.145.60.53)" | tee "$DESTINO/recursos-staging.txt"
listar_recursos hermes-bloqueio "Bloqueio (157.173.207.22)" | tee "$DESTINO/recursos-bloqueio.txt"

echo "=========================================="
echo "Arquivos salvos:"
echo "  $DESTINO/recursos-producao.txt"
echo "  $DESTINO/recursos-staging.txt"
echo "  $DESTINO/recursos-bloqueio.txt"
