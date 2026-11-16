set -e
cd /opt/omniroute
cp painel_creditos.py painel_creditos.py.bak-antes-entrou-16nov
python3 -m py_compile /tmp/pc_novo.py
cp /tmp/pc_novo.py painel_creditos.py
systemctl restart painel-creditos
sleep 4
systemctl is-active painel-creditos
K=$(cat painel_creditos.chave)
curl -s "http://127.0.0.1:20172/dados?k=$K&p=claude" > /tmp/pc_dados.json
python3 - <<'EOF'
import json
d = json.load(open('/tmp/pc_dados.json'))
for c in sorted(d['contas'], key=lambda c: c.get('entrou') or 'z'):
    print(c.get('entrou', '')[:10], c.get('dias'), (c.get('renova') or '')[:10], c['nome'])
EOF
curl -s "http://127.0.0.1:20172/?k=$K&p=claude" | grep -c "Entrou"
