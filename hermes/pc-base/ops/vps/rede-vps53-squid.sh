#!/usr/bin/env bash
# ops/vps/rede-vps53-squid.sh — proxy da VPS 53 (209.145.60.53) pras chamadas do Groq (03/10/2026).
#
# QUEM RODA: a dona (mudança de segurança no servidor). Rodar NA VPS 53:
#   ssh hermes-staging 'bash -s' < ops/vps/rede-vps53-squid.sh
#
# O que faz (e só isso):
#   - instala o Squid e escuta na porta 3128;
#   - aceita conexão SÓ da produção (62.171.128.241) e SÓ pra api.groq.com:443 (CONNECT/TLS — o
#     proxy não vê a chave nem o conteúdo, só "api.groq.com");
#   - sem cache e sem guardar conteúdo; firewall (ufw, se ativo) só libera a 3128 pra produção.
# Pra também servir de reserva do WhatsApp (botão "WhatsApp pela outra VPS"), rode com
#   WHATSAPP=1 (libera também *.whatsapp.net/*.whatsapp.com).
#
# Depois, a PRODUÇÃO precisa saber o endereço (o agente faz, não é segredo):
#   /etc/systemd/system/hermes-call.service.d/30-rede-vps.conf com
#   Environment="HERMES_GROQ_VPS_PROXY=http://209.145.60.53:3128"
#   (e HERMES_WHATSAPP_VPS_PROXY=http://209.145.60.53:3128 se WHATSAPP=1) + daemon-reload + restart.
# Desfazer: apt-get remove -y squid && ufw delete allow from 62.171.128.241 to any port 3128 proto tcp
set -euo pipefail
PROD=62.171.128.241
WA=${WHATSAPP:-0}

apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq squid >/dev/null
[ -f /etc/squid/squid.conf.original ] || cp /etc/squid/squid.conf /etc/squid/squid.conf.original

DESTINOS=".groq.com"
[ "$WA" = "1" ] && DESTINOS="$DESTINOS .whatsapp.net .whatsapp.com"

cat > /etc/squid/squid.conf <<EOF
# Hermes Call — proxy só pra produção ($PROD) e só pros destinos abaixo (03/10/2026).
http_port 3128
acl producao src $PROD/32
acl destinos dstdomain $DESTINOS
acl SSL_ports port 443
acl CONNECT method CONNECT
http_access deny CONNECT !SSL_ports
http_access allow producao CONNECT destinos
http_access deny all
cache deny all
cache_mem 8 MB
access_log daemon:/var/log/squid/access.log squid
forwarded_for delete
via off
dns_nameservers 1.1.1.1 8.8.8.8
EOF

squid -k parse
systemctl enable --now squid
systemctl restart squid
if command -v ufw >/dev/null && ufw status | grep -q "Status: active"; then
  ufw allow from $PROD to any port 3128 proto tcp comment 'Hermes: Groq via VPS 53'
fi
sleep 2
systemctl is-active squid
echo "Pronto. Teste NA PRODUÇÃO (deve dar 401, sinal de que o túnel chegou no Groq):"
echo "  curl -s -o /dev/null -w '%{http_code}\n' -x http://209.145.60.53:3128 https://api.groq.com/openai/v1/models"
