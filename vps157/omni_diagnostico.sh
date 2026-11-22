#!/bin/bash
# Somente leitura: reinicio do contêiner, OOM, erros de banco por janela, pedidos recentes, integridade do banco.
DB=/opt/omniroute/data/storage.sqlite
echo "agora UTC: $(date -u '+%F %T')"
echo "== contêiner =="
docker inspect omniroute --format 'iniciado={{.State.StartedAt}} reinicios={{.RestartCount}} oom={{.State.OOMKilled}} saude={{.State.Health.Status}}'
echo "== OOM do kernel (ultimos) =="
dmesg -T 2>/dev/null | grep -iE 'out of memory|killed process' | tail -3
echo "== vigia de memoria =="
tail -n 6 /opt/omniroute/vigia_memoria.log 2>/dev/null
tail -n 4 /opt/omniroute/memoria_amostras.log 2>/dev/null
echo "== 'database is locked' no log do gateway =="
for j in 5m 15m 40m; do
  echo "ultimos $j: $(docker logs --since $j omniroute 2>&1 | grep -c 'database is locked')"
done
echo "== sinais de reinicio no log =="
docker logs --since 60m omniroute 2>&1 | grep -iE 'SIGTERM|shutting down|heap pressure|uncaught|fatal|Server started|Ready in' | tail -6
echo "== pedidos recentes (usage_history, UTC) =="
for m in 5 15 30; do
  sqlite3 -readonly $DB "SELECT 'ultimos ${m} min: pedidos=' || count(*) || ' ok=' || coalesce(sum(success),0) FROM usage_history WHERE timestamp >= strftime('%Y-%m-%dT%H:%M:%S','now','-${m} minutes')"
done
echo "== integridade do banco (quick_check) =="
ionice -c3 nice -n19 timeout 150 sqlite3 -readonly $DB "PRAGMA quick_check;" 2>&1 | head -5
echo "== disco e memoria =="
df -h / | tail -1
free -m | sed -n '1,2p'
ls -lh $DB $DB-wal 2>/dev/null
