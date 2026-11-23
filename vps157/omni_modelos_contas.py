#!/usr/bin/env python3
"""So leitura: onde ficam os modelos de cada conta, quais contas tem Gemini 4 Neon/Argon/Carbon/Hydrogen e
modelos novos no Kiro; por que o Kiro esta todo desligado. NAO chama Google/Kiro."""
import collections
import json
import re
import sqlite3

db = sqlite3.connect("file:/opt/omniroute/data/storage.sqlite?mode=ro", uri=True, timeout=30)
Q = lambda s, p=(): db.execute(s, p).fetchall()

print("== chaves de provider_specific_data (antigravity, 1 conta) ==")
psd = Q("SELECT provider_specific_data FROM provider_connections WHERE provider='antigravity' AND is_active=1 LIMIT 1")
if psd:
    d = json.loads(psd[0][0] or "{}")
    print("  ", sorted(d.keys()))

print("\n== namespaces de key_value com lista de modelos ==")
for ns, n in Q("SELECT namespace, count(*) FROM key_value GROUP BY 1 ORDER BY 2 DESC LIMIT 25"):
    print(f"   {ns}: {n}")

def modelos_kv(prov):
    ids = {r[0]: r[1] for r in Q("SELECT id, is_active FROM provider_connections WHERE provider=?", (prov,))}
    cont, ativos = collections.Counter(), collections.Counter()
    contas = 0
    for k, v in Q("SELECT key, value FROM key_value WHERE namespace=?", (prov,)):
        if k not in ids:
            continue
        try:
            lst = json.loads(v)
        except ValueError:
            continue
        if not isinstance(lst, list):
            continue
        contas += 1
        for m in lst:
            nome = m.get("id") if isinstance(m, dict) else str(m)
            cont[nome] += 1
            if ids[k]:
                ativos[nome] += 1
    return contas, cont, ativos

for prov in ("antigravity", "gemini", "kiro"):
    contas, cont, ativos = modelos_kv(prov)
    print(f"\n== [{prov}] modelos por conta (key_value namespace={prov}): {contas} contas com lista ==")
    for nome, c in sorted(cont.items(), key=lambda x: (-x[1], x[0])):
        print(f"   {nome} | {c} contas (ativas: {ativos[nome]})")

print("\n== Kiro: por que esta desligado ==")
for r in Q("""SELECT coalesce(test_status,'-'), coalesce(substr(last_error,1,90),'-'), count(*)
              FROM provider_connections WHERE provider='kiro' GROUP BY 1,2 ORDER BY 3 DESC LIMIT 8"""):
    print("  ", " | ".join(str(x) for x in r))
print("  ultimo uso do kiro:", Q("SELECT max(timestamp) FROM usage_history WHERE provider='kiro'"))
print("  uso kiro por dia (7 d):")
for r in Q("""SELECT substr(timestamp,1,10), count(*), sum(success) FROM usage_history WHERE provider='kiro'
              AND timestamp >= strftime('%Y-%m-%dT%H:%M:%S','now','-7 days') GROUP BY 1 ORDER BY 1"""):
    print("    ", r)
print("  pedidos kr/ nos call_logs (6 h):")
for r in Q("""SELECT requested_model, provider||'/'||model, status, substr(coalesce(error_summary,''),1,100), count(*)
              FROM call_logs WHERE requested_model LIKE 'kr/%' AND timestamp >= strftime('%Y-%m-%dT%H:%M:%S','now','-6 hours')
              GROUP BY 1,2,3,4 ORDER BY 5 DESC LIMIT 8"""):
    print("    ", " | ".join(str(x) for x in r))
