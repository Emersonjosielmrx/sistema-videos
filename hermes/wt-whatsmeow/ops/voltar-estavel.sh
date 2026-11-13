#!/usr/bin/env bash
# ops/voltar-estavel.sh — VOLTA SEGURA: coloca no ar a versão marcada como ESTÁVEL
# (a última que comprovadamente funcionava). Pode rodar quantas vezes quiser: se a
# estável já está no ar, não faz nada. O banco não é revertido (mudanças são aditivas).
# É uma VOLTA: a VPS confere só se o serviço responde (/api/version) e nunca recoloca
# sozinha a versão de onde saiu (ops/vps/hermes-release.sh cmd_voltar).
set -euo pipefail
HOST=hermes-prod
REL=/opt/hermes-call/releases
ssh_() { ssh -o BatchMode=yes -o ConnectTimeout=15 "$HOST" "$@"; }
echo "== No ar: $(ssh_ "cat $REL/ATUAL")   Estável: $(ssh_ "cat $REL/ESTAVEL 2>/dev/null || echo nenhuma")"
ssh_ "$REL/hermes-release.sh voltar-estavel"
echo "== Pronto. No ar agora: $(ssh_ "cat $REL/ATUAL")"
echo "   Conferir: https://hermescall.opus-sem-limites.com.br/api/version"
echo "   IMPORTANTE: recarregue o painel (Ctrl+F5) em TODAS as abas abertas — o painel novo carregado"
echo "   no navegador apagaria configurações ao salvar no servidor antigo."
