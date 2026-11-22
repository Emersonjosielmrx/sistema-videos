#!/usr/bin/env python3
"""Somente leitura: confere contas x copia de antes da limpeza, saude do gateway e arquivos de call_logs."""
import datetime
import json
import os
import sqlite3
import subprocess
import urllib.request

DATA = "/opt/omniroute/data"
DB = DATA + "/storage.sqlite"
BK = "/opt/omniroute/backup_contas_antes_limpeza_21nov.sqlite"
LOGDIR = DATA + "/call_logs"

con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=30)
con.execute("PRAGMA busy_timeout=30000")
bk = sqlite3.connect(f"file:{BK}?mode=ro", uri=True)


def cols(c, t):
    return [r[1] for r in c.execute(f"PRAGMA table_info({t})")]


print("== contas (provider_connections): copia de antes x agora ==")
idb = {r[0]: r for r in bk.execute("SELECT id, provider, is_active FROM provider_connections")}
idn = {r[0]: r for r in con.execute("SELECT id, provider, is_active FROM provider_connections")}
print("copia:", len(idb), "agora:", len(idn))
print("so na copia:", len(set(idb) - set(idn)), "so agora:", len(set(idn) - set(idb)))
dif = [i for i in idb if i in idn and idb[i][2] != idn[i][2]]
print("is_active diferente:", len(dif), [(idb[i][1], idb[i][2], idn[i][2]) for i in dif[:10]])
for r in con.execute("SELECT provider, sum(is_active), count(*) FROM provider_connections "
                     "GROUP BY provider ORDER BY 3 DESC LIMIT 8"):
    print("  ", r)

print("== outras protegidas: ids iguais? ==")
for t in ("api_keys", "combos", "proxy_assignments", "model_combo_mappings"):
    c = cols(con, t)
    a = {tuple(r) for r in bk.execute(f"SELECT {c[0]} FROM {t}")}
    b = {tuple(r) for r in con.execute(f"SELECT {c[0]} FROM {t}")}
    print(f"  {t}: copia={len(a)} agora={len(b)} so_copia={len(a - b)} so_agora={len(b - a)}")

print("== key_value (config do gateway) ==")
kc = cols(con, "key_value")
pk = [c for c in kc if c != "value"]
sel = ",".join(pk)
kb = {tuple(r) for r in bk.execute(f"SELECT {sel} FROM key_value")}
kn = {tuple(r) for r in con.execute(f"SELECT {sel} FROM key_value")}
print("colunas:", kc)
print("so na copia:", len(kb - kn), [tuple(str(x)[:50] for x in k) for k in sorted(kb - kn)[:8]])
print("so agora:", len(kn - kb))

print("== pedidos por 15 min (UTC); a limpeza rodou 21:55 a 22:13 UTC ==")
since = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M")
for b, n, ok in con.execute(
        "SELECT substr(timestamp,1,13)||':'||printf('%02d',(CAST(substr(timestamp,15,2) AS INT)/15)*15), "
        "count(*), sum(success) FROM usage_history WHERE timestamp>=? GROUP BY 1 ORDER BY 1", (since,)):
    print(f"  {b}  pedidos={n}  ok={ok}  ({100 * ok / n:.0f}%)")

print("== gateway ==")
try:
    ps = subprocess.run(["docker", "ps", "--format", "{{.Names}} {{.Status}}"], capture_output=True,
                        text=True, timeout=30).stdout
    print([l for l in ps.splitlines() if "omniroute" in l])
except Exception as e:
    print("docker ps falhou:", e)
try:
    k = con.execute("SELECT key FROM api_keys WHERE is_active=1 AND revoked_at IS NULL LIMIT 1").fetchone()
    req = urllib.request.Request("http://localhost:20128/v1/models",
                                 headers={"Authorization": "Bearer " + k[0]})
    with urllib.request.urlopen(req, timeout=30) as r:
        print("GET /v1/models:", r.status, "modelos:", len(json.load(r).get("data", [])))
except Exception as e:
    print("GET /v1/models falhou:", e)
try:
    lg = subprocess.run(["docker", "logs", "--since", "90m", "omniroute"], capture_output=True,
                        text=True, timeout=60)
    linhas = (lg.stdout + lg.stderr).splitlines()
    ruins = [l for l in linhas if any(x in l for x in ("SQLITE_", "database is locked", "no such table",
                                                       "no such column", "malformed"))]
    print("linhas de log:", len(linhas), "com erro de banco:", len(ruins))
    for l in ruins[-5:]:
        print("   ", l[:250])
except Exception as e:
    print("docker logs falhou:", e)

print("== arquivos de call_logs ==")
print("realpath data:", os.path.realpath(DATA), "| call_logs:", os.path.realpath(LOGDIR))
rel = {r[0] for r in con.execute("SELECT artifact_relpath FROM call_logs WHERE artifact_relpath IS NOT NULL")}
n = tam = orf = orf_tam = 0
mn = mx = None
for raiz, _d, files in os.walk(LOGDIR):
    for f in files:
        p = os.path.join(raiz, f)
        try:
            st = os.stat(p)
        except OSError:
            continue
        n += 1
        tam += st.st_size
        mn = st.st_mtime if mn is None else min(mn, st.st_mtime)
        mx = st.st_mtime if mx is None else max(mx, st.st_mtime)
        if os.path.relpath(p, LOGDIR) not in rel:
            orf += 1
            orf_tam += st.st_size
f = lambda t: datetime.datetime.fromtimestamp(t, datetime.timezone.utc).strftime("%m-%d %H:%M") if t else "-"
print(f"arquivos: {n} ({tam / 1e6:.0f} MB), mtime de {f(mn)} ate {f(mx)} UTC")
print(f"linhas de call_logs com arquivo: {len(rel)}; arquivos sem linha (orfaos): {orf} ({orf_tam / 1e6:.0f} MB)")
