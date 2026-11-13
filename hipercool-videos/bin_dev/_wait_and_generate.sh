#!/bin/bash
# Espera a API do Claude (proxy) voltar e então gera a parte 2 do cap 2.
# Roda em background; loga em /tmp/cap2_parte2.log.
cd "/Users/emerson-ia/Downloads/apps/hipercool videos" || exit 1
source venv/bin/activate

LOG=/tmp/cap2_parte2.log
echo "[$(date +%H:%M:%S)] Aguardando API do Claude voltar..." > "$LOG"

# Polling de saúde da API (1 chamada barata) a cada 90s
while true; do
  if python3 - <<'PY'
import sys
from pathlib import Path
env={}
for l in Path('.env').read_text().splitlines():
    if '=' in l and not l.startswith('#'):
        k,v=l.split('=',1); env[k.strip()]=v.strip()
import anthropic
c=anthropic.Anthropic(api_key=env.get('ANTHROPIC_API_KEY'), base_url=env.get('ANTHROPIC_BASE_URL'))
try:
    c.messages.create(model='claude-sonnet-4-5-20250514',max_tokens=10,
                      messages=[{'role':'user','content':'ok'}])
    sys.exit(0)
except Exception:
    sys.exit(1)
PY
  then
    echo "[$(date +%H:%M:%S)] ✅ API voltou! Iniciando geração da parte 2..." >> "$LOG"
    break
  else
    echo "[$(date +%H:%M:%S)] API ainda fora (529). Nova checagem em 90s." >> "$LOG"
    sleep 90
  fi
done

# Gera a parte 2 (painéis 56+)
python bin/hiper-pipeline.py \
  --panels-dir workspace/panels-preview/taming-noona-cap02/ \
  --titulo "Taming the New Noona cap 2 parte 2" \
  --max-panels 55 --start-panel 55 --skip-notify >> "$LOG" 2>&1

echo "[$(date +%H:%M:%S)] Geração finalizada (ver acima)." >> "$LOG"
