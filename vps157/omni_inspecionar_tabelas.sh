#!/bin/bash
DB=/opt/omniroute/data/storage.sqlite
echo "== esquema das candidatas =="
for t in conversation_turn_nodes usage_history call_logs quota_snapshots; do
  sqlite3 "$DB" ".schema $t"
  echo
done
echo "== todas as tabelas (linhas) =="
for t in $(sqlite3 "$DB" "select name from sqlite_master where type='table' and name not like 'sqlite_%' order by name"); do
  echo "$t|$(timeout 20 sqlite3 "$DB" "select count(*) from \"$t\"")"
done
echo "== logs/application =="
ls -lh --time-style=long-iso /opt/omniroute/data/logs/application | head -40
echo "== call_logs =="
ls -la --time-style=long-iso /opt/omniroute/data/call_logs | head -20
du -sh /opt/omniroute/data/call_logs/* 2>/dev/null | head -10
echo "== retencao em key_value =="
sqlite3 "$DB" "select key, substr(value,1,80) from key_value where lower(key) like '%retention%' or lower(key) like '%log%' limit 20" 2>&1
