#!/bin/sh
# Vigia de memoria do OmniRoute (26/10/2026, revisto no mesmo dia).
# O processo vaza memoria fora do heap (chegou a 10 GB e o kernel matou tudo por OOM).
# Mas os pedidos chegam em RAJADA (limites voltam, chats do ultracode): a memoria sobe de verdade
# nessas horas, entao NAO reiniciar no meio da rajada.
# - acima de LIMITE_MB: reinicia so quando estiver calmo (<= CALMO pedidos nos ultimos 3 min)
# - acima de FORCAR_MB (perto do mem_limit 7g do compose): reinicia mesmo assim, melhor que o OOM matar
# Cron a cada 5 min (/etc/cron.d/omniroute-vigia-memoria). Log: /opt/omniroute/vigia_memoria.log
LIMITE_MB=4500
FORCAR_MB=6300
CALMO=1
LOG=/opt/omniroute/vigia_memoria.log
ID=$(docker inspect -f "{{.Id}}" omniroute 2>/dev/null) || exit 0
B=$(awk '/^anon /{print $2}' /sys/fs/cgroup/system.slice/docker-$ID.scope/memory.stat 2>/dev/null)
[ -z "$B" ] && exit 0
MB=$((B/1024/1024))
[ "$MB" -le "$LIMITE_MB" ] && exit 0
# "calmo" = quantos pedidos terminaram nos ultimos 3 min (contar conexoes nao serve: o Claude Code
# do PC deixa 6-7 abertas mesmo parado)
CONN=$(sqlite3 -cmd ".timeout 5000" /opt/omniroute/data/storage.sqlite \
  "SELECT count(*) FROM usage_history WHERE timestamp > strftime('%Y-%m-%dT%H:%M:%S','now','-3 minutes');" 2>/dev/null || echo 99)
if [ "$MB" -gt "$FORCAR_MB" ] || [ "$CONN" -le "$CALMO" ]; then
  echo "$(date "+%F %T") memoria ${MB} MB, pedidos_3min ${CONN}: reiniciando omniroute" >> $LOG
  docker restart -t 40 omniroute >> $LOG 2>&1
else
  echo "$(date "+%F %T") memoria ${MB} MB mas ${CONN} pedidos nos ultimos 3 min: espera ficar calmo" >> $LOG
fi
