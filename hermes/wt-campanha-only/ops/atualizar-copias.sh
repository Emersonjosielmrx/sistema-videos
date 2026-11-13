#!/usr/bin/env bash
# ops/atualizar-copias.sh — depois de publicar, deixa TODAS as cópias na mesma versão. Roda NO PC.
#
#   Decisão da dona (07/10/2026): Hermes e bancada existem nas duas VPS e usa-se uma de cada
#   vez. Para comparar as máquinas as cópias têm de estar no mesmo programa. Este script leva
#   a versão (padrão: a que está NO AR na produção) para:
#     1. a bancada da produção   (/opt/hermes-bancada em hermes-prod)
#     2. a bancada da 209        (/opt/hermes-bancada em hermes-staging)
#     3. o Hermes RESERVA da 209 (/opt/hermes-call-reserva em hermes-staging; fica DESLIGADO)
#   Bancada que estiver ligada é reiniciada na versão nova; a que estiver parada continua parada.
#   Não liga nada que estava desligado, não copia banco nem segredo.
#
#   atualizar-copias.sh            usa a versão que está no ar
#   atualizar-copias.sh <ID>       usa /opt/hermes-call/releases/<ID> da produção
set -euo pipefail
PROD=hermes-prod
T209=hermes-staging
SSH="ssh -o BatchMode=yes -o ConnectTimeout=20"
die() { echo "PAROU: $*" >&2; exit 1; }
log() { echo "[$(date '+%H:%M:%S')] $*"; }

ID=${1:-$($SSH $PROD 'cat /opt/hermes-call/releases/ATUAL')}
R=/opt/hermes-call/releases/$ID
$SSH $PROD "[ -x $R/hermes-call ] && [ -d $R/dist ]" || die "a versão $ID não existe em $R na produção"
SOMA=$($SSH $PROD "sha256sum $R/hermes-call | cut -c1-16")
log "versão $ID (programa $SOMA)"
sleep 4

log "1/3 bancada da produção"
$SSH $PROD "set -e; B=/opt/hermes-bancada; a=\$(systemctl is-active hermes-bancada || true)
  cp -a $R/hermes-call \$B/hermes-call.novo && mv -f \$B/hermes-call.novo \$B/hermes-call
  rm -rf \$B/dist.novo && cp -a $R/dist \$B/dist.novo && rm -rf \$B/dist && mv \$B/dist.novo \$B/dist
  echo '$ID' > \$B/VERSAO
  if [ \"\$a\" = active ]; then systemctl restart hermes-bancada; echo '   ligada: reiniciada na versão nova'; else echo '   parada: arquivos trocados, continua parada'; fi"
sleep 6

copia_para_209() { # pasta de destino
  $SSH $PROD "tar -C $R -cz hermes-call dist" | $SSH $T209 "set -e; D=$1; mkdir -p \$D/lib \$D/novo; tar -C \$D/novo -xz
    mv -f \$D/novo/hermes-call \$D/hermes-call; rm -rf \$D/dist; mv \$D/novo/dist \$D/dist; rmdir \$D/novo; echo '$ID' > \$D/VERSAO
    [ \"\$(sha256sum \$D/hermes-call | cut -c1-16)\" = '$SOMA' ] || { echo 'programa chegou diferente'; exit 1; }"
}

log "2/3 bancada da 209"
copia_para_209 /opt/hermes-bancada
sleep 6
$SSH $T209 'if [ "$(systemctl is-active hermes-bancada || true)" = active ]; then systemctl restart hermes-bancada; for i in $(seq 1 30); do curl -s -m2 http://127.0.0.1:8091/api/version | grep -q build && break; sleep 2; done; echo "   ligada: reiniciada, responde $(curl -s -m3 http://127.0.0.1:8091/api/version)"; else echo "   parada: arquivos trocados, continua parada"; fi'
sleep 6

log "3/3 Hermes reserva da 209 (desligado)"
copia_para_209 /opt/hermes-call-reserva
sleep 6
$SSH $PROD "cat /usr/local/lib/libopus_mlow.so" | $SSH $T209 'cat > /opt/hermes-call-reserva/lib/libopus_mlow.so.novo && mv -f /opt/hermes-call-reserva/lib/libopus_mlow.so.novo /opt/hermes-call-reserva/lib/libopus_mlow.so
  cat > /opt/hermes-call-reserva/LEIA-ME.txt <<EOF
Hermes Call RESERVA (copia do programa que esta no ar na producao). DESLIGADO.
Mantido por ops/atualizar-copias.sh. Aqui so ha o programa e o painel: nao ha banco, linha
do WhatsApp nem segredo. Ligar isto como producao e uma MUDANCA DE MAQUINA (banco, gravacoes,
as linhas, o dominio e os segredos): ver docs/PLANO_DUAS_VPS.md no repositorio. Nao ligue a mao.
EOF
  echo "   programa $(sha256sum /opt/hermes-call-reserva/hermes-call | cut -c1-16), $(cat /opt/hermes-call-reserva/VERSAO); bibliotecas que faltam: $(LD_LIBRARY_PATH=/opt/hermes-call-reserva/lib ldd /opt/hermes-call-reserva/hermes-call | grep -c "not found")"'
log "feito."
