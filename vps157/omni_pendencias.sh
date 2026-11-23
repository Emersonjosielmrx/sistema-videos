#!/bin/bash
# So leitura: pendencias da sessao 21-23/11 na VPS 157.
cd /opt/omniroute
DB="file:/opt/omniroute/data/storage.sqlite?mode=ro"
Q() { timeout 60 sqlite3 -separator ' | ' "$DB" "$1"; }
echo "== 1. envio dos backups antigos pro Drive =="
grep -E "bkp_1411_agopus|backup_storage_antes_cli_17nov" /opt/limpeza-vps/drive.log | tail -4 | cut -c1-160
ls -lh data/storage.sqlite.bkp_1411_agopus backup_storage_antes_cli_17nov.sqlite backup_contas_antes_limpeza_21nov.sqlite 2>&1 | cut -c1-140
df -h / | tail -1
echo "== 2. limpeza semanal (domingo 04:30) =="
grep -nE "docker (stop|start|restart)|VACUUM|cp |backup|sqlite3|find .*-delete|DIAS|dias" limpeza_omniroute.sh | cut -c1-150 | head -20
tail -n 6 limpeza_omniroute.log 2>/dev/null | cut -c1-160
echo "== 3. quem chama o AI Studio (gemini/) 24 h: chave | combo | pedido | n | ok =="
Q "SELECT coalesce(api_key_name,'-'), coalesce(combo_name,'-'), requested_model, count(*), sum(status=200) FROM call_logs
   WHERE provider='gemini' AND timestamp>=strftime('%Y-%m-%dT%H:%M:%S','now','-24 hours') GROUP BY 1,2,3 ORDER BY 4 DESC LIMIT 10;"
echo "== 4. haiku-fila e agy/ (24 h): pedido | destino | status | erro | n =="
Q "SELECT requested_model, provider||'/'||coalesce(model,''), status, substr(coalesce(error_summary,''),1,90), count(*) FROM call_logs
   WHERE requested_model IN ('kr/claude-haiku-4.5','agy/gemini-3.8-flash-high','_probe_opus') AND timestamp>=strftime('%Y-%m-%dT%H:%M:%S','now','-24 hours')
   GROUP BY 1,2,3,4 ORDER BY 5 DESC LIMIT 10;"
echo "== 5. crons novos =="
tail -n 2 cw_pausa_429.log; cat cw_pausa_429.erros vigia_disjuntor_cc.erros 2>/dev/null | tail -3
tail -n 3 vigia_disjuntor_cc.log 2>/dev/null || echo "disjuntor: nenhum reset"
Q "SELECT 'opus-auto 30 min: n='||count(*)||' ok='||sum(status=200) FROM call_logs WHERE requested_model='opus-auto' AND timestamp>=strftime('%Y-%m-%dT%H:%M:%S','now','-30 minutes');"
Q "SELECT 'web 30 min: n='||count(*)||' ok='||sum(status=200) FROM call_logs WHERE provider='claude-web' AND timestamp>=strftime('%Y-%m-%dT%H:%M:%S','now','-30 minutes');"
Q "SELECT 'hydrogen 30 min: n='||count(*)||' ok='||sum(status=200) FROM call_logs WHERE model LIKE '%hydrogen%' AND timestamp>=strftime('%Y-%m-%dT%H:%M:%S','now','-30 minutes');"
echo "== 6. memoria e reinicios =="
docker inspect -f 'inicio={{.State.StartedAt}} saude={{.State.Health.Status}}' omniroute
tail -n 2 memoria_amostras.log; grep -c "reiniciando" vigia_memoria.log; grep "reiniciando" vigia_memoria.log | tail -3
echo "== 7. meus scripts temporarios na VPS =="
ls -1 omni_*.py omni_*.sh vigia_pressao_patch.py sonnet_fila_so_web.py /root/omni_inspecionar_tabelas.sh /tmp/levantamento.sh 2>/dev/null
find / -xdev -maxdepth 3 \( -name 'rev_ro.sh' -o -name 't_db.py' -o -name 't_gw.sh' \) 2>/dev/null
