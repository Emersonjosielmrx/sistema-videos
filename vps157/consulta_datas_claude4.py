import sqlite3
db = sqlite3.connect('file:/opt/omniroute/data/storage.sqlite?mode=ro', uri=True, timeout=10)
print(db.execute("SELECT action, count(*) FROM audit_log WHERE target LIKE 'claude:%' GROUP BY 1").fetchall())
for r in db.execute("SELECT timestamp, action, target FROM audit_log WHERE target LIKE 'claude:%' AND action NOT LIKE '%updated%' ORDER BY timestamp"):
    print(r)
