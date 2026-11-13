#!/usr/bin/env bash
# configurar-asaas.sh — liga a COBRANÇA (Asaas) na produção. Roda NA VPS, pela DONA, num terminal:
#
#     ssh -t hermes-prod /opt/hermes-call/ops/configurar-asaas.sh
#
# Por que é a dona que roda: a chave do Asaas movimenta dinheiro. O agente não digita nem guarda
# chave de pagamento; a chave é colada aqui (não aparece na tela) e vai direto para um arquivo que
# só o root lê (/etc/hermes-call/asaas.env). Nada de chave no chat, no git ou no histórico.
#
# O que faz:
#   1. pede a chave (escondida) e confere no Asaas com uma consulta de leitura (lista 1 cliente);
#   2. cria (ou mantém) o token do webhook: a senha que o Asaas manda junto com cada aviso de pagamento;
#   3. grava /etc/hermes-call/asaas.env (modo 600) e o drop-in 30-asaas.conf do hermes-call;
#   4. garante que a BANCADA fique SEM cobrança (ela copia o ambiente da produção);
#   5. reinicia a produção (~10 s) e confere que a cobrança ligou;
#   6. mostra o endereço e o token para colar no painel do Asaas.
# Para desligar a cobrança:  configurar-asaas.sh desligar
set -euo pipefail

ENVF=/etc/hermes-call/asaas.env
DROP=/etc/systemd/system/hermes-call.service.d/30-asaas.conf
BANC=/etc/hermes-bancada/bancada.env
SITE=${HERMES_SITE:-https://hermescall.opus-sem-limites.com.br}
API=${HERMES_ASAAS_API_URL:-https://api.asaas.com/v3}

die() { echo; echo "PAROU: $*" >&2; exit 1; }
prod_ok() { curl -s -m3 http://127.0.0.1:8080/api/version | grep -q '"build"'; }
ligacao_agora() { [ "$(journalctl -u hermes-call --since '-90 seconds' --no-pager -o cat | grep -cE 'call ACTIVE|voice latência real|voice transcribed' || true)" -gt 0 ]; }

reiniciar() {
  if ligacao_agora; then
    read -r -p "Parece haver uma ligação em andamento. Reiniciar mesmo assim? (digite SIM) " r
    [ "$r" = "SIM" ] || die "nada foi reiniciado. A configuração já está gravada: rode de novo quando não houver ligação."
  fi
  systemctl daemon-reload
  systemctl restart hermes-call
  for _ in $(seq 1 30); do prod_ok && break; sleep 3; done
  prod_ok || die "a produção não respondeu depois de reiniciar. Veja: journalctl -u hermes-call -n 50"
}

bancada_sem_cobranca() {
  [ -f "$BANC" ] || return 0
  sed -i -E '/^HERMES_ASAAS_(API_KEY|WEBHOOK_TOKEN)=/d' "$BANC"
  printf 'HERMES_ASAAS_API_KEY=\nHERMES_ASAAS_WEBHOOK_TOKEN=\n' >> "$BANC"
}

[ "$(id -u)" = 0 ] || die "rode como root"

if [ "${1:-}" = "desligar" ]; then
  rm -f "$DROP" "$ENVF"
  reiniciar
  echo "Cobrança DESLIGADA. Produção: $(curl -s -m3 http://127.0.0.1:8080/api/version)"
  exit 0
fi

[ -t 0 ] || die "rode num terminal de verdade:  ssh -t hermes-prod /opt/hermes-call/ops/configurar-asaas.sh"

echo "== Ligar a cobrança (Asaas) na produção do Hermes Call"
echo "   A chave fica só neste servidor, num arquivo que só o root lê."
echo
read -r -s -p "Cole a chave da API do Asaas e aperte Enter (ela NÃO aparece na tela): " CHAVE
echo
# Tira espaços, quebras de linha e caracteres invisíveis que alguns terminais colam junto.
CHAVE=$(printf '%s' "$CHAVE" | sed -E $'s/\x1b\\[[0-9;]*[~A-Za-z]//g' | tr -cd '[:graph:]')
[ ${#CHAVE} -ge 40 ] || die "isso não parece uma chave do Asaas (curta demais: ${#CHAVE} caracteres). Copie de novo pelo botão de copiar do Asaas."
echo "   recebi ${#CHAVE} caracteres; a chave termina em …${CHAVE: -4} (confira com o fim da chave que o Asaas mostrou)."
case "$CHAVE" in
  '$aact_'*) ;;
  *) die "a chave do Asaas começa com \$aact_ . Copie de novo em Asaas › Integrações › Chave de API." ;;
esac
case "$CHAVE" in
  '$aact_prod_'*) echo "   chave de PRODUÇÃO (cobra de verdade)." ;;
  *) echo "   ATENÇÃO: não é chave de produção (sandbox?). Endereço usado: $API" ;;
esac

echo "== Conferindo a chave no Asaas (consulta de leitura)"
RESP=$(mktemp); trap 'rm -f "$RESP"' EXIT
COD=$(curl -s -m 20 -o "$RESP" -w '%{http_code}' -H "access_token: $CHAVE" -H 'User-Agent: hermes-call' "$API/customers?limit=1" || echo 000)
case "$COD" in
  200) echo "   chave aceita pelo Asaas." ;;
  401|403)
    echo "   o Asaas respondeu: $(head -c 400 "$RESP" | tr -d '\n' | sed -E 's/"access_token"[^,}]*//')"
    echo "   O que costuma ser:"
    echo "    - chave copiada pela metade (use o botão de copiar; ela tem perto de 170 caracteres);"
    echo "    - chave antiga: ao gerar uma chave nova no Asaas, a anterior para de valer;"
    echo "    - a chave tem \"endereços IP autorizados\" no Asaas e o desta VPS ($(curl -s -m 5 https://api.ipify.org || echo '62.171.128.241')) não está na lista;"
    echo "    - a chave é do ambiente de testes (sandbox) e não de produção."
    die "o Asaas RECUSOU a chave (código $COD). Nada foi alterado." ;;
  *) read -r -p "   o Asaas respondeu código $COD (rede?). Gravar assim mesmo? (digite SIM) " r; [ "$r" = "SIM" ] || die "nada foi alterado." ;;
esac

TOKEN=""
[ -f "$ENVF" ] && TOKEN=$(sed -n 's/^HERMES_ASAAS_WEBHOOK_TOKEN=//p' "$ENVF" | head -1)
if [ -n "$TOKEN" ]; then
  echo "== Mantendo o token do webhook que já existia (não precisa mexer no painel do Asaas)"
else
  TOKEN=$(openssl rand -hex 24)
fi

umask 077
mkdir -p /etc/hermes-call "$(dirname "$DROP")"
printf 'HERMES_ASAAS_API_KEY=%s\nHERMES_ASAAS_WEBHOOK_TOKEN=%s\n' "$CHAVE" "$TOKEN" > "$ENVF"
chmod 600 "$ENVF"
cat > "$DROP" <<EOF
# Cobrança (Asaas). Criado por ops/vps/configurar-asaas.sh. A chave fica em $ENVF (só root).
# Para desligar: /opt/hermes-call/ops/configurar-asaas.sh desligar
[Service]
EnvironmentFile=$ENVF
EOF
chmod 644 "$DROP"
unset CHAVE
bancada_sem_cobranca

echo "== Reiniciando a produção (as linhas ficam ~10 s fora)"
reiniciar
PID=$(systemctl show hermes-call -p MainPID --value)
LIGOU=$(tr '\0' '\n' < "/proc/$PID/environ" | grep -c '^HERMES_ASAAS_API_KEY=.' || true)
TOKOK=$(tr '\0' '\n' < "/proc/$PID/environ" | grep -c '^HERMES_ASAAS_WEBHOOK_TOKEN=.' || true)
echo "   produção: $(curl -s -m3 http://127.0.0.1:8080/api/version)"
[ "$LIGOU" = 1 ] && [ "$TOKOK" = 1 ] || die "a produção subiu, mas não enxergou a chave/token. Veja $DROP."
echo "   cobrança LIGADA na produção. Bancada: sem cobrança."

cat <<EOF

== ÚLTIMO PASSO (no site do Asaas): avisar o Hermes quando alguém pagar
   Asaas › Integrações › Webhooks › Adicionar webhook, e preencha:

     Nome:                 Hermes Call
     URL:                  $SITE/api/billing/webhook
     Token de autenticação: $TOKEN
     Eventos:              todos os de Cobranças e de Assinaturas
     Fila de sincronização: ativada

   Se você usa agendamento pago, crie um segundo webhook igual, com a URL:
                           $SITE/api/agenda/asaas-webhook

   Sem esse webhook a pessoa paga e o Hermes não fica sabendo.
   Depois faça UM pagamento de teste de valor baixo e avise o agente para conferir o registro.
EOF
