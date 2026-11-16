import sqlite3, json, subprocess
db = sqlite3.connect('file:/opt/omniroute/data/storage.sqlite?mode=ro', uri=True, timeout=10)
for cid, em, psd, exp in db.execute("SELECT id, email, provider_specific_data, expires_at FROM provider_connections WHERE provider='claude' AND email LIKE 'solange%' OR email LIKE 'clara%'"):
    try:
        d = json.loads(psd or '{}')
    except Exception:
        d = {}
    print(em, "expires_at:", exp, "chaves:", list(d.keys()))
    print({k: v for k, v in d.items() if not any(s in k.lower() for s in ('token', 'secret', 'key', 'cookie'))})
tabs = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
print("TABELAS", tabs)
# rastro da solange em qualquer tabela de texto
for t in tabs:
    try:
        cols = [r[1] for r in db.execute(f"PRAGMA table_info('{t}')")]
        for c in cols:
            n = db.execute(f"SELECT count(*), min(rowid) FROM '{t}' WHERE CAST(\"{c}\" AS TEXT) LIKE '%solangecarnero%'").fetchone()
            if n[0]:
                print("ACHOU", t, c, n[0])
    except Exception as e:
        pass
print(subprocess.run("grep -rl solangecarnero /opt/omniroute --include=*.log --include=*.txt --include=*.json 2>/dev/null | head; grep -h solangecarnero /opt/omniroute/*.log 2>/dev/null | head -3", shell=True, capture_output=True, text=True).stdout)
