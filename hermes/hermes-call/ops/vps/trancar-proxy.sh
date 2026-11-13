#!/usr/bin/env bash
# trancar-proxy.sh — tranca o proxy "entre as VPS" (tinyproxy, porta 8888) da produção para ele
# atender SÓ as máquinas da dona. Roda NA VPS de produção, pela DONA:
#
#     ssh -t hermes-prod /opt/hermes-call/ops/trancar-proxy.sh
#
# Por que existe (05/10/2026): o tinyproxy foi instalado em 03/10 com "Allow 0.0.0.0/0" e a porta
# 8888 liberada no firewall para qualquer um. Em 2 dias: 43.600 conexões de 80 endereços, quase
# todas de robôs de compra (Nike, Vans, bol.com) e de um verificador de proxies públicos. Quem usa
# é visto pelos sites como o IP da produção, o mesmo das linhas do WhatsApp.
# É mudança de firewall: o agente prepara, a dona roda.
#
#   trancar-proxy.sh            tranca: só 127.0.0.1 e os endereços de PERMITIDOS abaixo
#   trancar-proxy.sh remover    desliga o tinyproxy de vez e fecha a porta (se ninguém seu usa)
#   trancar-proxy.sh estado     só mostra como está
set -euo pipefail

PORTA=8888
CONF=/etc/tinyproxy/tinyproxy.conf
# As outras duas VPS da dona. Para liberar mais uma máquina: acrescente o endereço aqui e rode de novo.
PERMITIDOS=${PERMITIDOS:-"209.145.60.53 157.173.207.22"}

die() { echo; echo "PAROU: $*" >&2; exit 1; }
[ "$(id -u)" = 0 ] || die "rode como root"

estado() {
  echo "tinyproxy: $(systemctl is-active tinyproxy 2>/dev/null || true) | no boot: $(systemctl is-enabled tinyproxy 2>/dev/null || true)"
  echo "quem o tinyproxy aceita: $(grep -E '^Allow ' "$CONF" 2>/dev/null | awk '{print $2}' | tr '\n' ' ')"
  echo "firewall da porta $PORTA:"
  local regras
  regras=$(ufw status 2>/dev/null | grep -E "^$PORTA[ /]" || true)
  if [ -n "$regras" ]; then echo "$regras" | sed 's/^/   /'; else echo "   (nenhuma regra: porta fechada para fora)"; fi
  echo "o tinyproxy que está RODANDO carregou a lista em: $(systemctl show -p ActiveEnterTimestamp --value tinyproxy 2>/dev/null) (a lista foi gravada em $(stat -c %y "$CONF" 2>/dev/null | cut -c1-19))"
  echo "origens diferentes nos últimos 10 min: $(journalctl -u tinyproxy --since '-10 min' --no-pager -o cat 2>/dev/null | grep -a 'Connect (file descriptor' | awk '{print $NF}' | sort -u | wc -l)"
}

fechar_para_todos() {
  # apaga TODAS as regras da porta (as "Anywhere" e as por endereço), da maior para a menor
  for n in $(ufw status numbered | grep -E "\b$PORTA(/tcp)?\b" | sed -E 's/^\[ *([0-9]+)\].*/\1/' | sort -rn); do
    # --force em vez de "yes |": com "set -o pipefail" o "yes" morre por SIGPIPE quando o ufw
    # termina, o pipeline dá erro e o "set -e" abortava o script na 1ª regra (05/10: ficou pela
    # metade — lista nova gravada, proxy sem reiniciar e a regra aberta ainda lá).
    ufw --force delete "$n" >/dev/null
  done
}

case "${1:-trancar}" in
  estado) estado; exit 0 ;;
  remover)
    systemctl disable --now tinyproxy >/dev/null 2>&1 || true
    fechar_para_todos
    echo "== tinyproxy DESLIGADO e porta $PORTA fechada. (O programa continua instalado; para apagar: apt-get remove tinyproxy)"
    estado; exit 0 ;;
  trancar) ;;
  *) die "uso: $0 [trancar|remover|estado]" ;;
esac

[ -f "$CONF" ] || die "não achei $CONF"
cp -p "$CONF" "$CONF.antes-de-trancar-$(date +%Y%m%d-%H%M%S)"
sed -i -E '/^Allow /d' "$CONF"
{
  echo "Allow 127.0.0.1"
  for ip in $PERMITIDOS; do echo "Allow $ip"; done
} >> "$CONF"

fechar_para_todos
for ip in $PERMITIDOS; do
  ufw allow from "$ip" to any port "$PORTA" proto tcp comment 'proxy entre as VPS' >/dev/null
done

systemctl restart tinyproxy
sleep 2
systemctl is-active --quiet tinyproxy || die "o tinyproxy não voltou. A configuração anterior está em $CONF.antes-de-trancar-*"
# Prova: de dentro da própria máquina, pelo endereço público, tem que ser RECUSADO (não está na lista).
MEU_IP=$(curl -s -m 5 https://api.ipify.org || true)
if [ -n "$MEU_IP" ]; then
  COD=$(curl -s -m 8 -o /dev/null -w '%{http_code}' -x "http://$MEU_IP:$PORTA" http://example.com/ || true)
  echo "== teste pelo endereço público ($MEU_IP): código ${COD:-sem resposta} (403 ou sem resposta = trancado; 200 = ainda aberto)"
fi

echo "== TRANCADO: o proxy da porta $PORTA só atende 127.0.0.1 e: $PERMITIDOS"
estado
echo
echo "Teste de fora (de um PC que não seja uma das VPS): tem que dar erro ou ficar sem resposta."
echo "Se alguma coisa sua parar de funcionar, o endereço dela faltou em PERMITIDOS: avise o agente."
