import sqlite3, subprocess
db = sqlite3.connect('file:/opt/omniroute/data/storage.sqlite?mode=ro', uri=True, timeout=10)
cols = [r[1] for r in db.execute("PRAGMA table_info(audit_log)")]
print("AUDIT COLS", cols)
for r in db.execute("SELECT * FROM audit_log WHERE target LIKE '%solangecarnero%' OR details LIKE '%solangecarnero%'"):
    print([str(x)[:200] for x in r])
print("AUDIT MIN", db.execute("SELECT min(rowid), count(*) FROM audit_log").fetchone(), cols and db.execute(f"SELECT min({cols[1]}) FROM audit_log").fetchone())
print("USO MIN SOLANGE", db.execute("SELECT min(timestamp) FROM usage_history WHERE account_label LIKE '%solangecarnero%'").fetchone())
print("USO MIN GERAL", db.execute("SELECT min(timestamp) FROM usage_history").fetchone())
sh = r"""
cd /opt/omniroute
for f in $(ls -tr *.log *.txt *.json 2>/dev/null); do
  l=$(grep -m1 -n solangecarnero "$f" 2>/dev/null | cut -c1-160); [ -n "$l" ] && echo "$f: $l";
done
zgrep -l solangecarnero /opt/omniroute/*.gz /opt/omniroute/data/logs/application/* 2>/dev/null | head
ls /opt/omniroute/data/call_logs | head -3
for d in $(ls /opt/omniroute/data/call_logs); do if grep -rlq solangecarnero /opt/omniroute/data/call_logs/$d 2>/dev/null; then echo "1o dia call_logs: $d"; break; fi; done
grep -m1 solangecarnero /opt/omniroute/data/logs/application/app.log | cut -c1-200
head -c 200 /opt/omniroute/data/logs/application/app.log
"""
print(subprocess.run(sh, shell=True, capture_output=True, text=True, executable='/bin/bash').stdout)
