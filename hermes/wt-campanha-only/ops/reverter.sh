#!/usr/bin/env bash
# ops/reverter.sh — volta a produção para a versão anterior (ou para uma específica).
#   bash ops/reverter.sh            volta para a versão que estava antes da atual
#   bash ops/reverter.sh <ID>       volta para uma versão da lista (bash ops/status.sh mostra os IDs)
# Só troca o programa e o painel. O banco NÃO é revertido (senão perderia os dados novos);
# se precisar, cada versão tem banco.dump com o backup feito antes de sair dela.
set -euo pipefail
HOST=hermes-prod
REL=/opt/hermes-call/releases
ssh_() { ssh -o BatchMode=yes -o ConnectTimeout=15 "$HOST" "$@"; }

ALVO=${1:-}
if [ -z "$ALVO" ]; then
  # anterior = versão de onde veio a última troca bem-sucedida
  ALVO=$(ssh_ "grep ' OK\$' $REL/HISTORICO | tail -1 | awk '{print \$3}'")
  [ -n "$ALVO" ] || { echo "não há versão anterior registrada"; exit 1; }
fi
echo "== No ar: $(ssh_ "cat $REL/ATUAL")  ->  voltando para: $ALVO"
# "ativar <ID> volta" = VOLTA: confere só /api/version e nunca recoloca sozinha a versão de
# onde saiu (o script da VPS até a v0.7.0 ignora o "volta" e faz o ativar dele, que também só
# confere /api/version).
ssh_ "$REL/hermes-release.sh ativar '$ALVO' volta"
echo "== Pronto. Conferir: https://hermescall.opus-sem-limites.com.br/api/version"
echo "   IMPORTANTE: recarregue o painel (Ctrl+F5) em TODAS as abas abertas — o painel novo carregado"
echo "   no navegador apagaria configurações ao salvar no servidor antigo."
