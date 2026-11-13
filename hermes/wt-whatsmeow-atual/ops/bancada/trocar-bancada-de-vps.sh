#!/usr/bin/env bash
# ops/bancada/trocar-bancada-de-vps.sh — muda a BANCADA de máquina. Roda NO PC (que entra nas duas).
#
#   A bancada existe instalada nas duas VPS, mas só pode estar LIGADA numa: é a mesma linha
#   (8288) e o WhatsApp só aceita um aparelho com aquela identidade. Ligar as duas ao mesmo
#   tempo, ou ligar uma com o banco velho da outra, estraga a sessão da linha.
#   Por isso a troca é sempre: PARA a de origem -> COPIA os dois bancos e as gravações -> LIGA a
#   de destino. Não é só "systemctl start".
#
#   trocar-bancada-de-vps.sh estado          onde ela está ligada e com qual versão
#   trocar-bancada-de-vps.sh para-producao   209  -> produção (62.171…)
#   trocar-bancada-de-vps.sh para-209        produção -> teste (209)
#
# Não mexe no Hermes de produção nem em senha alguma. Os bancos passam pelo PC em trânsito
# (ssh | ssh), sem arquivo no PC.
set -euo pipefail

PROD=hermes-prod
T209=hermes-staging
SID=<SEGREDO_REMOVIDO>
BANCOS="bancada_main bancada_$SID"
SSH="ssh -o BatchMode=yes -o ConnectTimeout=20"

die() { echo "PAROU: $*" >&2; exit 1; }
log() { echo "[$(date '+%H:%M:%S')] $*"; }

ativa()  { $SSH "$1" 'systemctl is-active hermes-bancada 2>/dev/null || true' | head -1; }
versao() { $SSH "$1" 'curl -s -m3 http://127.0.0.1:8091/api/version | grep -o "\"build\":\"[^\"]*\"" || echo "(sem resposta)"'; }
binario() { $SSH "$1" 'sha256sum /opt/hermes-bancada/hermes-call 2>/dev/null | cut -c1-12'; }

estado() {
  for h in $PROD $T209; do
    echo "$h: serviço $(ativa $h) | responde $(versao $h) | programa $(binario $h)"
  done
}

# psql/pg_dump/pg_restore de cada lado: na produção é o Postgres da máquina; na 209 é o contêiner da bancada.
dump_de() { # host banco
  case "$1" in
    $PROD) $SSH "$1" "cd /; sudo -u postgres pg_dump -Fc $2" ;;
    $T209) $SSH "$1" "docker exec hermes-bancada-pg pg_dump -U postgres -Fc $2" ;;
  esac
}
restaura_em() { # host banco   (lê o dump da entrada)
  case "$1" in
    $T209) $SSH "$1" "docker exec -i hermes-bancada-pg pg_restore -U postgres --no-owner --no-acl --clean --if-exists -d $2 2>&1 | grep -vE 'does not exist, skipping' | tail -3" ;;
    $PROD)
      # Na produção os bancos da bancada são do usuário do Hermes (não superusuário): o dump vai para um
      # arquivo temporário, a extensão "vector" (que já existe lá) fica de fora da lista, e tudo é
      # recriado em nome do dono do banco.
      $SSH "$1" "set -e; cd /; umask 077; f=\$(mktemp /var/tmp/bancada-XXXXXX.dump); trap 'rm -f \$f \$f.lista' EXIT; cat > \$f; chown postgres \$f;
        dono=\$(sudo -u postgres psql -Atc \"select pg_get_userbyid(datdba) from pg_database where datname='$2'\");
        [ -n \"\$dono\" ] || { echo 'banco $2 não existe na produção'; exit 1; };
        sudo -u postgres pg_restore -l \$f | grep -vE ' (EXTENSION|COMMENT - EXTENSION) ' > \$f.lista; chown postgres \$f.lista;
        sudo -u postgres pg_restore --no-owner --no-acl --role=\"\$dono\" --clean --if-exists -L \$f.lista -d $2 \$f 2>&1 | grep -vE 'does not exist, skipping' | tail -3" ;;
  esac
}
tabelas() { # host banco
  case "$1" in
    $PROD) $SSH "$1" "cd /; sudo -u postgres psql -d $2 -Atc \"select count(*) from information_schema.tables where table_schema='public'\"" ;;
    $T209) $SSH "$1" "docker exec hermes-bancada-pg psql -U postgres -d $2 -Atc \"select count(*) from information_schema.tables where table_schema='public'\"" ;;
  esac
}

trocar() { # origem destino
  local de=$1 para=$2
  [ "$(ativa $de)" = active ] || die "a bancada não está ligada em $de (veja: $0 estado)"
  [ "$(ativa $para)" != active ] || die "a bancada já está ligada em $para: as duas ligadas estragam a sessão da linha"
  local a b; a=$(binario $de); b=$(binario $para)
  [ "$a" = "$b" ] || die "o programa da bancada é diferente nas duas máquinas ($a x $b): iguale a versão antes de trocar"
  if [ "$($SSH $de "journalctl -u hermes-bancada --since '-2 min' --no-pager -o cat | grep -c 'call ACTIVE' || true")" -gt 0 ]; then
    die "houve ligação na bancada nos últimos 2 min; espere acabar"
  fi

  log "parando a bancada em $de"
  $SSH $de 'systemctl disable --now hermes-bancada >/dev/null 2>&1; systemctl is-active hermes-bancada || true' | head -1
  sleep 5
  for db in $BANCOS; do
    log "copiando $db: $de -> $para"
    set -o pipefail
    dump_de $de $db | restaura_em $para $db || die "a cópia de $db falhou. A bancada ficou PARADA nas duas; para voltar: ssh $de systemctl enable --now hermes-bancada"
    local n1 n2; n1=$(tabelas $de $db); n2=$(tabelas $para $db)
    [ "$n1" = "$n2" ] || die "$db: $n1 tabelas na origem e $n2 no destino. Bancada PARADA nas duas; para voltar: ssh $de systemctl enable --now hermes-bancada"
    sleep 6   # o ssh das VPS limita conexões seguidas
  done
  log "copiando as gravações"
  $SSH $de 'tar -C /var/lib/hermes-bancada -cz recordings 2>/dev/null' | $SSH $para 'mkdir -p /var/lib/hermes-bancada && tar -C /var/lib/hermes-bancada -xz' || log "aviso: as gravações não foram copiadas (a bancada funciona sem elas)"
  sleep 6
  log "ligando a bancada em $para"
  $SSH $para 'systemctl enable --now hermes-bancada >/dev/null 2>&1; for i in $(seq 1 30); do curl -s -m2 http://127.0.0.1:8091/api/version | grep -q build && break; sleep 2; done; sleep 20;
    echo "responde: $(curl -s -m3 http://127.0.0.1:8091/api/version)";
    echo "linha: $(journalctl -u hermes-bancada --since "-2 min" --no-pager -o cat | grep -cE "sessions restored|fila offline entregue") sinal(is) de conexão"'
  log "feito. Estado:"
  estado
}

case "${1:-}" in
  estado) estado ;;
  para-producao) trocar $T209 $PROD ;;
  para-209) trocar $PROD $T209 ;;
  *) echo "uso: $0 estado | para-producao | para-209"; exit 1 ;;
esac
