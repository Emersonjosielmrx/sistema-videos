#!/usr/bin/env bash
# hermes-falhou.sh <unit> — chamado pelo hermes-call-falhou@.service (OnFailure= do
# hermes-call.service). Manda aviso no Telegram com o estado e as últimas linhas do log
# (o hermes-alerta.sh mascara segredos). Antirrepetição: 1 aviso a cada 60 min por unit.
set -euo pipefail
UNIT=${1:-hermes-call.service}
ESTADO=$(systemctl is-active "$UNIT" 2>/dev/null || true)
ULTIMAS=$(journalctl -u "$UNIT" -n 8 --no-pager -o cat 2>/dev/null | cut -c1-200 || true)
exec /opt/hermes-call/ops/hermes-alerta.sh --chave "falhou-$UNIT" "🔴 O serviço $UNIT FALHOU na VPS (estado: ${ESTADO:-desconhecido}).
O systemd vai tentar subir de novo se houver Restart=; confira em 1-2 min.
Últimas linhas:
$ULTIMAS"
