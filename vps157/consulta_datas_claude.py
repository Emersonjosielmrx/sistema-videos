import sqlite3, json
db = sqlite3.connect('file:/opt/omniroute/data/storage.sqlite?mode=ro', uri=True, timeout=10)
cols = [r[1] for r in db.execute("PRAGMA table_info(provider_connections)")]
print("COLS", cols)
rows = db.execute("SELECT id, coalesce(email,name), created_at, updated_at, is_active FROM provider_connections WHERE provider='claude' ORDER BY created_at").fetchall()
for r in rows:
    pri = db.execute("SELECT min(created_at) FROM quota_snapshots WHERE connection_id=?", (r[0],)).fetchone()[0]
    pu = db.execute("SELECT min(timestamp) FROM usage_history WHERE connection_id=?", (r[0],)).fetchone()[0]
    print(json.dumps({"id": r[0][:8], "email": r[1], "criado": r[2], "atualizado": r[3], "ativo": r[4], "1o_snap": pri, "1o_uso": pu}))
# emails duplicados / readicionados: snapshots de ids que nao existem mais
orf = db.execute("SELECT connection_id, min(created_at), max(created_at) FROM quota_snapshots WHERE provider='claude' AND connection_id NOT IN (SELECT id FROM provider_connections) GROUP BY 1").fetchall()
print("ORFAOS", orf)
print("MIN_SNAP_GERAL", db.execute("SELECT min(created_at) FROM quota_snapshots").fetchone())
