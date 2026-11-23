#!/usr/bin/env python3
"""So leitura: (1) quando e por que as 50 contas Kiro 'active' ficaram com is_active=0; (2) Neon/Argon/Carbon/Hydrogen
nos modelos sincronizados (key_value namespace syncedAvailableModels) por provedor. NAO chama Google/Kiro."""
import collections
import json
import sqlite3

db = sqlite3.connect("file:/opt/omniroute/data/storage.sqlite?mode=ro", uri=True, timeout=30)
Q = lambda s, p=(): db.execute(s, p).fetchall()
cols = [c[1] for c in Q("PRAGMA table_info(provider_connections)")]
print("colunas provider_connections:", cols)

print("\n== Kiro 'active' com is_active=0 ==")
tempo = [c for c in cols if "updated" in c or "error_at" in c or "last_used" in c or "test" in c]
sel = ", ".join(["id", "is_active", "test_status"] + [c for c in tempo if c not in ("test_status",)])
lin = Q(f"SELECT {sel} FROM provider_connections WHERE provider='kiro' AND test_status='active' LIMIT 50")
print("  ", sel)
datas = collections.Counter()
for r in lin:
    d = dict(zip(sel.split(", "), r))
    datas[str(d.get("updated_at", ""))[:13]] += 1
print("   updated_at por hora:", sorted(datas.items())[-8:])
for r in lin[:3]:
    print("   ", [str(x)[:40] for x in r])

print("\n== audit_log sobre kiro (ultimos) ==")
acols = [c[1] for c in Q("PRAGMA table_info(audit_log)")]
print("   colunas:", acols)
tcol = next((c for c in acols if "time" in c or "created" in c), acols[0])
for r in Q(f"SELECT * FROM audit_log WHERE lower(CAST(details AS TEXT)) LIKE '%kiro%' OR lower(CAST(action AS TEXT)) LIKE '%kiro%' "
           f"ORDER BY {tcol} DESC LIMIT 8") if "details" in acols and "action" in acols else []:
    print("   ", [str(x)[:90] for x in r])

print("\n== ultimos pedidos ao kiro (usage_history) ==")
for r in Q("""SELECT substr(timestamp,1,19), substr(connection_id,1,8), status, coalesce(error_code,'-'), model
              FROM usage_history WHERE provider='kiro' ORDER BY timestamp DESC LIMIT 12"""):
    print("   ", " | ".join(str(x) for x in r))
print("  falhas kiro 22-23/11 por erro:")
for r in Q("""SELECT status, coalesce(error_code,'-'), count(*) FROM usage_history WHERE provider='kiro' AND success=0
              AND timestamp >= '2026-11-22' GROUP BY 1,2 ORDER BY 3 DESC LIMIT 8"""):
    print("    ", r)

print("\n== modelos sincronizados (key_value syncedAvailableModels) ==")
prov_de = {r[0]: (r[1], r[2]) for r in Q("SELECT id, provider, is_active FROM provider_connections")}
cont = collections.defaultdict(collections.Counter)
ativ = collections.defaultdict(collections.Counter)
for k, v in Q("SELECT key, value FROM key_value WHERE namespace='syncedAvailableModels'"):
    cid = k.split(":")[-1]
    prov, ok = prov_de.get(cid, (k.split(":")[0], None))
    try:
        lst = json.loads(v)
    except ValueError:
        continue
    for m in lst if isinstance(lst, list) else []:
        nome = m.get("id") if isinstance(m, dict) else str(m)
        cont[prov][nome] += 1
        if ok:
            ativ[prov][nome] += 1
for prov in sorted(cont):
    print(f"  [{prov}] {len(cont[prov])} modelos")
    for nome, c in sorted(cont[prov].items(), key=lambda x: x[0]):
        if any(a in nome.lower() for a in ("gemini-4", "gemini-5", "neon", "argon", "carbon", "hydrogen", "opus",
                                            "sonnet", "fable", "gpt-5", "deepseek", "qwen", "kimi", "glm", "minimax")):
            print(f"     {nome} | {c} contas (ativas {ativ[prov][nome]})")
