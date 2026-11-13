#!/bin/sh
# Vigia de memoria do OmniRoute (26/10/2026; 11/11/2026: cron de 1 em 1 min, FORCAR 5500, amostras).
# 11/11: 5 mortes por OOM em 30 min (memoria de ~1 GB a 7,2 GB em 6-8 min, ~15 MB/s); o vigia de 5 em 5 min nao alcancava.
# O processo vaza memoria fora do heap e os pedidos chegam em RAJADA (limites voltam, chats do ultracode).
# - acima de LIMITE_MB: reinicia so quando estiver calmo (<= CALMO pedidos nos ultimos 3 min)
# - acima de FORCAR_MB: reinicia mesmo assim (reinicio com -t 40 deixa terminar o que esta em andamento; o OOM mata tudo)
# Cron a cada 1 min (/etc/cron.d/omniroute-vigia-memoria). Logs: vigia_memoria.log e memoria_amostras.log (1 linha/min: hora, MB anon, pedidos no ultimo min).
# Backup do original: /opt/omniroute/backup_vigia_11nov/
LIMITE_MB=4500
FORCAR_MB=5500
CALMO=1
LOG=/opt/omniroute/vigia_memoria.log
AMOSTRAS=/opt/omniroute/memoria_amostras.log
DB=/opt/omniroute/data/storage.sqlite
exec 9>/run/vigia_memoria.lock
flock -n 9 || exit 0
ID=$(docker inspect -f "{{.Id}}" omniroute 2>/dev/null) || exit 0
B=$(awk '/^anon /{print $2}' /sys/fs/cgroup/system.slice/docker-$ID.scope/memory.stat 2>/dev/null)
[ -z "$B" ] && exit 0
MB=$((B/1024/1024))
PED1=$(sqlite3 -cmd ".timeout 3000" "$DB" \
  "SELECT count(*) FROM usage_history WHERE timestamp > strftime('%Y-%m-%dT%H:%M:%S','now','-1 minutes');" 2>/dev/null || echo "?")
echo "$(date '+%F %T') ${MB} ${PED1}" >> "$AMOSTRAS"
if [ "$(wc -l < "$AMOSTRAS")" -gt 4000 ]; then
  tail -n 2000 "$AMOSTRAS" > "$AMOSTRAS.tmp" && mv "$AMOSTRAS.tmp" "$AMOSTRAS"
fi
[ "$MB" -le "$LIMITE_MB" ] && exit 0
CONN=$(sqlite3 -cmd ".timeout 5000" "$DB" \
  "SELECT count(*) FROM usage_history WHERE timestamp > strftime('%Y-%m-%dT%H:%M:%S','now','-3 minutes');" 2>/dev/null || echo 99)
if [ "$MB" -gt "$FORCAR_MB" ] || [ "$CONN" -le "$CALMO" ]; then
  echo "$(date '+%F %T') memoria ${MB} MB, pedidos_3min ${CONN}: reiniciando omniroute" >> "$LOG"
  docker restart -t 40 omniroute >> "$LOG" 2>&1
else
  echo "$(date '+%F %T') memoria ${MB} MB mas ${CONN} pedidos nos ultimos 3 min: espera ficar calmo" >> "$LOG"
fi
