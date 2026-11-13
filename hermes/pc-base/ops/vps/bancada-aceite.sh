#!/usr/bin/env bash
# Liga/desliga o atendimento automático de TESTE na bancada (nunca na produção).
#   bancada_aceite.sh ligar <variante>   -> HERMES_AUTO_ANSWER_ACEITAR=true, atraso 3 s, variante N
#   bancada_aceite.sh desligar           -> tira as três chaves
#   bancada_aceite.sh estado
# O HERMES_AUTO_ANSWER_SOMENTE_DE que já está no bancada.env continua limitando quem é atendido.
set -euo pipefail
F=/etc/hermes-bancada/bancada.env
CHAVES='<SEGREDO_REMOVIDO>'

estado() {
  echo "bancada: $(curl -s -m5 http://127.0.0.1:8091/api/version)"
  curl -s -m5 http://127.0.0.1:8091/saude-local | python3 -c 'import json,sys; d=json.load(sys.stdin); print({k: d.get(k) for k in ("linhas_conectadas", "chaves_de_teste")})'
  printf 'produção com chave de teste? '
  tr '\0' '\n' < "/proc/$(systemctl show -p MainPID --value hermes-call)/environ" | grep -E 'HERMES_(AUTO_ANSWER_ACEITAR|ACEITE_VARIANTE|TESTE_)' || echo "não (ok)"
  echo "limite de quem é atendido (SOMENTE_DE) no bancada.env: $(grep -c '^HERMES_AUTO_ANSWER_SOMENTE_DE=' "$F") linha(s)"
}

reiniciar() {
  systemctl restart hermes-bancada
  for _ in $(seq 1 20); do curl -s -m3 http://127.0.0.1:8091/api/version >/dev/null && break; sleep 3; done
  # espera a linha do WhatsApp reconectar
  for _ in $(seq 1 15); do
    n=$(curl -s -m3 http://127.0.0.1:8091/saude-local | python3 -c 'import json,sys; print(json.load(sys.stdin).get("linhas_conectadas", 0))' 2>/dev/null || echo 0)
    [ "$n" -ge 1 ] && break
    sleep 2
  done
}

case "${1:-estado}" in
  ligar)
    v=${2:?informe a variante (0..63)}
    [ "$(grep -c '^HERMES_AUTO_ANSWER_SOMENTE_DE=' "$F")" -ge 1 ] || { echo "PAROU: sem HERMES_AUTO_ANSWER_SOMENTE_DE no bancada.env (atenderia qualquer um)"; exit 1; }
    # conta em vez de "| grep -q": com pipefail o grep -q que acha cedo fazia o teste dar FALSO
    if [ "$(journalctl -u hermes-bancada -u hermes-call --since '-2 min' --no-pager -o cat | grep -c 'call ACTIVE' || true)" -gt 0 ]; then
      echo "PAROU: há ligação ativa agora"; exit 1
    fi
    [ -f "$F.antes-aceite-20261005" ] || cp -p "$F" "$F.antes-aceite-20261005"
    sed -i -E "/^($CHAVES)=/d" "$F"
    printf 'HERMES_AUTO_ANSWER_ACEITAR=true\nHERMES_AUTO_ANSWER_ATRASO_MS=3000\nHERMES_ACEITE_VARIANTE=%s\n' "$v" >> "$F"
    reiniciar
    estado
    ;;
  desligar)
    sed -i -E "/^($CHAVES)=/d" "$F"
    reiniciar
    estado
    ;;
  estado) estado ;;
  *) echo "uso: $0 ligar <variante> | desligar | estado"; exit 1 ;;
esac
date '+feito às %T'
