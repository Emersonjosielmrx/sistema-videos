#!/bin/bash
# Script de limpeza do OmniRoute na VPS 157
# Executar quando o VPS estiver acessível novamente
# Uso: bash vps157_limpeza_omniroute.sh

set -e

echo "=== Limpeza OmniRoute VPS 157 ==="
echo "Iniciando em: $(date)"
echo ""

# 1. Verificar estado atual
echo "[1/6] Verificando disco..."
df -h | grep -E "Filesystem|/dev/"
echo ""

# 2. Verificar tamanho dos call_logs
echo "[2/6] Verificando call_logs..."
if [ -d "/opt/omniroute/data/call_logs" ]; then
    du -sh /opt/omniroute/data/call_logs
    echo "Pastas de data:"
    find /opt/omniroute/data/call_logs -type d -name "2026-*" | head -20
else
    echo "Diretório call_logs não existe"
fi
echo ""

# 3. Parar container temporariamente
echo "[3/6] Parando container OmniRoute..."
docker stop antigravity-omniroute
echo "Container parado"
echo ""

# 4. Limpar call_logs antigos (manter últimos 7 dias)
echo "[4/6] Limpando call_logs antigos (mantendo últimos 7 dias)..."
if [ -d "/opt/omniroute/data/call_logs" ]; then
    ANTES=$(du -sh /opt/omniroute/data/call_logs | awk '{print $1}')
    find /opt/omniroute/data/call_logs -type d -name "2026-*" -mtime +7 -exec rm -rf {} + 2>/dev/null || true
    find /opt/omniroute/data/call_logs -type f -name "*.log" -mtime +7 -delete 2>/dev/null || true
    DEPOIS=$(du -sh /opt/omniroute/data/call_logs | awk '{print $1}')
    echo "Antes: $ANTES | Depois: $DEPOIS"
else
    echo "Diretório call_logs não existe, pulando"
fi
echo ""

# 5. Limpar registros antigos do SQLite
echo "[5/6] Limpando registros antigos do SQLite..."
if [ -f "/opt/omniroute/data/storage.sqlite" ]; then
    ANTES=$(ls -lh /opt/omniroute/data/storage.sqlite | awk '{print $5}')
    sqlite3 /opt/omniroute/data/storage.sqlite "DELETE FROM usage_history WHERE timestamp < datetime('now', '-30 days');" || true
    sqlite3 /opt/omniroute/data/storage.sqlite "VACUUM;" || true
    DEPOIS=$(ls -lh /opt/omniroute/data/storage.sqlite | awk '{print $5}')
    echo "storage.sqlite: Antes: $ANTES | Depois: $DEPOIS"
else
    echo "storage.sqlite não existe"
fi
echo ""

# 6. Reiniciar container
echo "[6/6] Reiniciando container OmniRoute..."
docker start antigravity-omniroute
sleep 3
docker ps | grep antigravity-omniroute
echo "Container reiniciado"
echo ""

# Estado final
echo "=== Estado final ==="
df -h | grep -E "Filesystem|/dev/"
echo ""
echo "Limpeza concluída em: $(date)"
