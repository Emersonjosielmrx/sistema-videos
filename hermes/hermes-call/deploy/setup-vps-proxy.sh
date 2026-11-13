#!/bin/bash
# setup-vps-proxy.sh — Configura proxy HTTP simples entre VPS para Groq (03/10/2026)
#
# Instalação:
#   bash setup-vps-proxy.sh
#
# Cria um proxy HTTP na porta 3128 usando Squid (leve e confiável).

set -e

echo "=========================================="
echo "Configurando Proxy HTTP para VPS"
echo "=========================================="
echo ""

# Detecta IP da VPS atual
CURRENT_IP=$(curl -s https://api.ipify.org)
echo "📍 IP detectado: $CURRENT_IP"
echo ""

# Instala Squid
if ! command -v squid &> /dev/null; then
    echo "📦 Instalando Squid..."
    apt-get update -qq
    apt-get install -y squid
    echo "✅ Squid instalado"
else
    echo "✅ Squid já instalado"
fi

# Configura Squid para aceitar conexões das outras VPS
echo ""
echo "⚙️  Configurando Squid..."

cat > /etc/squid/squid.conf << 'EOF'
# Squid proxy para comunicação entre VPS Hermes Call
# Porta 3128 (padrão)

# ACLs para as VPS autorizadas
acl vps1 src 209.145.60.53/32
acl vps2 src 157.173.207.22/32
acl vps3 src 62.171.128.241/32
acl localhost src 127.0.0.1/32

# Portas SSL permitidas
acl SSL_ports port 443
acl Safe_ports port 80          # http
acl Safe_ports port 443         # https
acl CONNECT method CONNECT

# Nega acesso a portas não seguras
http_access deny !Safe_ports
http_access deny CONNECT !SSL_ports

# Permite acesso das VPS autorizadas
http_access allow vps1
http_access allow vps2
http_access allow vps3
http_access allow localhost

# Nega todo o resto
http_access deny all

# Porta do proxy
http_port 3128

# Cache (mínimo - não queremos cache de API)
cache_dir ufs /var/spool/squid 100 16 256
maximum_object_size 1 MB
cache_mem 32 MB

# Logs
access_log /var/log/squid/access.log squid
cache_log /var/log/squid/cache.log

# Performance
dns_nameservers 8.8.8.8 8.8.4.4
EOF

echo "✅ Squid configurado"

# Cria diretório de cache
echo ""
echo "📁 Inicializando cache..."
squid -z 2>/dev/null || true

# Reinicia Squid
echo ""
echo "🔄 Reiniciando Squid..."
systemctl enable squid
systemctl restart squid

# Verifica status
echo ""
echo "🔍 Verificando status..."
if systemctl is-active --quiet squid; then
    echo "✅ Squid rodando"
else
    echo "❌ Erro: Squid não está rodando"
    systemctl status squid
    exit 1
fi

# Configura firewall (se ufw estiver ativo)
if command -v ufw &> /dev/null && ufw status | grep -q "Status: active"; then
    echo ""
    echo "🔥 Configurando firewall..."
    ufw allow from 209.145.60.53 to any port 3128 comment 'VPS1 proxy'
    ufw allow from 157.173.207.22 to any port 3128 comment 'VPS2 proxy'
    ufw allow from 62.171.128.241 to any port 3128 comment 'VPS3 proxy'
    echo "✅ Firewall configurado"
fi

# Testa o proxy localmente
echo ""
echo "🧪 Testando proxy..."
if curl -x http://127.0.0.1:3128 -s -o /dev/null -w "%{http_code}" https://api.groq.com/openai/v1/models | grep -q "200\|401"; then
    echo "✅ Proxy funcionando"
else
    echo "⚠️  Proxy pode não estar funcionando corretamente"
fi

echo ""
echo "=========================================="
echo "✅ Configuração Completa!"
echo "=========================================="
echo ""
echo "📋 Informações:"
echo "  Porta: 3128"
echo "  IP desta VPS: $CURRENT_IP"
echo "  Config: /etc/squid/squid.conf"
echo "  Logs: /var/log/squid/"
echo ""
echo "🔧 Comandos úteis:"
echo "  Reiniciar: systemctl restart squid"
echo "  Status: systemctl status squid"
echo "  Logs: tail -f /var/log/squid/access.log"
echo ""
echo "📝 Próximos passos:"
echo "  1. Execute este script nas outras VPS"
echo "  2. Configure HERMES_VPS_IP no Hermes Call:"
echo "     export HERMES_VPS_IP=\"$CURRENT_IP\""
echo "  3. Reinicie o Hermes Call"
echo ""
