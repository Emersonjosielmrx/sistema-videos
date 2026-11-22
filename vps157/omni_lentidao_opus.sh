#!/bin/bash
# So leitura: por que o opus-auto (Opus 5.5) esta lento. Ultimos 60 min.
DB="file:/opt/omniroute/data/storage.sqlite?mode=ro"
Q() { timeout 60 sqlite3 -separator ' | ' "$DB" "$1"; }
echo "agora UTC: $(date -u '+%F %T')"
echo "== pedidos do opus-auto por destino (call_logs, 60 min): n | ok | media s | ttft medio s | max s =="
Q "SELECT coalesce(provider,'?')||'/'||coalesce(model,'?'), count(*), sum(status=200),
   round(avg(duration)/1000.0,1), round(avg(ttft_ms)/1000.0,1), round(max(duration)/1000.0,1)
   FROM call_logs WHERE combo_name='opus-auto' AND timestamp >= strftime('%Y-%m-%dT%H:%M:%S','now','-60 minutes')
   GROUP BY 1 ORDER BY 2 DESC LIMIT 12;"
echo "== status dos pedidos do opus-auto (60 min) =="
Q "SELECT status, count(*), substr(coalesce(error_summary,''),1,90) FROM call_logs
   WHERE combo_name='opus-auto' AND timestamp >= strftime('%Y-%m-%dT%H:%M:%S','now','-60 minutes')
   GROUP BY 1,3 ORDER BY 2 DESC LIMIT 10;"
echo "== espera somada pelo gateway (added_wait) =="
Q "SELECT coalesce(added_wait_cause,'-'), count(*), round(avg(added_wait_ms)/1000.0,1) FROM call_logs
   WHERE combo_name='opus-auto' AND timestamp >= strftime('%Y-%m-%dT%H:%M:%S','now','-60 minutes')
   GROUP BY 1 ORDER BY 2 DESC LIMIT 6;"
echo "== ultimos 12 pedidos opus-auto: hora | destino | status | s | ttft s | tokens entrada =="
Q "SELECT substr(timestamp,12,8), provider||'/'||model, status, round(duration/1000.0,1),
   round(ttft_ms/1000.0,1), tokens_in FROM call_logs WHERE combo_name='opus-auto'
   ORDER BY timestamp DESC LIMIT 12;"
echo "== tentativas por conta no Opus 5.5 (usage_history, 60 min): conta | n | ok | latencia media s | ttft s =="
Q "SELECT provider||' '||coalesce(account_label,substr(connection_id,1,8)), count(*), sum(success),
   round(avg(latency_ms)/1000.0,1), round(avg(ttft_ms)/1000.0,1) FROM usage_history
   WHERE model LIKE '%opus-5-5%' AND timestamp >= strftime('%Y-%m-%dT%H:%M:%S','now','-60 minutes')
   GROUP BY 1 ORDER BY 2 DESC LIMIT 12;"
echo "== ordem atual do combo opus-auto =="
Q "SELECT substr(data,1,600) FROM combos WHERE name='opus-auto';" | sed -E 's/[A-Za-z0-9_-]{40,}/<id>/g'
echo "== gateway =="
docker inspect -f 'saude={{.State.Health.Status}} reinicios={{.RestartCount}} inicio={{.State.StartedAt}}' omniroute
docker stats --no-stream --format '{{.Name}} cpu={{.CPUPerc}} mem={{.MemUsage}}' omniroute
uptime
for i in 1 2 3; do curl -s -o /dev/null -m 20 -w 'v1/models http=%{http_code} %{time_total}s\n' http://localhost:20128/v1/models; done
echo "429/503/locked nos ultimos 15 min no log: 429=$(docker logs --since 15m omniroute 2>&1 | grep -c ' 429\|"status":429') 503=$(docker logs --since 15m omniroute 2>&1 | grep -c 'pressure') locked=$(docker logs --since 15m omniroute 2>&1 | grep -c 'database is locked')"
