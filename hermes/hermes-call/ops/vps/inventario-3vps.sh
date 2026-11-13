#!/usr/bin/env bash
# ops/vps/inventario-3vps.sh — inventário completo do que roda nas 3 VPS
#
# O que faz:
#   - Lista processos, containers Docker, serviços systemd em cada VPS
#   - Mostra uso de CPU, memória e disco
#   - Identifica serviços que competem por recursos

set -euo pipefail
cd "$(dirname "$0")/../.."

PRODUCAO=hermes-prod
STAGING=hermes-staging
BLOQUEIO=hermes-bloqueio
DESTINO=_temp_audio

mkdir -p "$DESTINO"

echo "=== Inventário das 3 VPS ==="
echo "Horário: $(date '+%Y-%m-%d %H:%M:%S')"
echo

inventariar_vps() {
  local HOST=$1
  local NOME=$2
  local IP=$3

  echo "=========================================="
  echo "VPS: $NOME ($IP)"
  echo "Host SSH: $HOST"
  echo "=========================================="
  echo

  # Recursos da máquina
  echo "--- RECURSOS ---"
  ssh "$HOST" 'echo "CPU: $(nproc) cores"; free -h | head -2; df -h / | tail -1'
  echo

  # Serviços systemd
  echo "--- SERVIÇOS SYSTEMD (ativos) ---"
  ssh "$HOST" "systemctl list-units --type=service --state=running --no-pager --no-legend | awk '{print \$1}' | grep -v 'systemd-\|user@\|getty@' | sort"
  echo

  # Containers Docker
  echo "--- CONTAINERS DOCKER ---"
  if ssh "$HOST" "command -v docker >/dev/null 2>&1"; then
    ssh "$HOST" "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}' 2>/dev/null || echo 'Docker não acessível'"
  else
    echo "(Docker não instalado)"
  fi
  echo

  # Docker Swarm services
  echo "--- DOCKER SWARM SERVICES ---"
  if ssh "$HOST" "docker info 2>/dev/null | grep -q 'Swarm: active'"; then
    ssh "$HOST" "docker service ls --format 'table {{.Name}}\t{{.Replicas}}\t{{.Image}}' 2>/dev/null || echo 'Swarm sem serviços'"
  else
    echo "(Swarm não ativo)"
  fi
  echo

  # Top 10 processos por CPU
  echo "--- TOP 10 PROCESSOS (CPU) ---"
  ssh "$HOST" "ps aux --sort=-%cpu | head -11 | tail -10 | awk '{printf \"%-6s %-5s %-5s %s\n\", \$1, \$3, \$4, \$11}'"
  echo

  # Top 10 processos por memória
  echo "--- TOP 10 PROCESSOS (MEMÓRIA) ---"
  ssh "$HOST" "ps aux --sort=-%mem | head -11 | tail -10 | awk '{printf \"%-6s %-5s %-5s %s\n\", \$1, \$3, \$4, \$11}'"
  echo

  # Uptime e load average
  echo "--- UPTIME E LOAD ---"
  ssh "$HOST" "uptime"
  echo
  echo
}

# Inventaria cada VPS
inventariar_vps "$PRODUCAO" "Produção" "62.171.128.241" | tee "$DESTINO/inventario-producao.txt"
inventariar_vps "$STAGING" "Staging" "209.145.60.53" | tee "$DESTINO/inventario-staging.txt"
inventariar_vps "$BLOQUEIO" "Bloqueio" "157.173.207.22" | tee "$DESTINO/inventario-bloqueio.txt"

echo "=========================================="
echo "RESUMO"
echo "=========================================="
echo
echo "Arquivos salvos em $DESTINO/:"
echo "  - inventario-producao.txt"
echo "  - inventario-staging.txt"
echo "  - inventario-bloqueio.txt"
echo
echo "Resumo dos principais serviços:"
echo
echo "[Produção - 62.171.128.241]"
grep -E "hermes-call|hermes-bancada|atlas|lucrativa" "$DESTINO/inventario-producao.txt" | head -10 || echo "  (processar manualmente)"
echo
echo "[Staging - 209.145.60.53]"
grep -E "n8n|hermes" "$DESTINO/inventario-staging.txt" | head -10 || echo "  (processar manualmente)"
echo
echo "[Bloqueio - 157.173.207.22]"
grep -E "chatwoot|n8n|omniroute" "$DESTINO/inventario-bloqueio.txt" | head -10 || echo "  (processar manualmente)"
