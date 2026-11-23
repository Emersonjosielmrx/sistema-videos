#!/usr/bin/env python3
"""So leitura: dados para consertar os modelos. Quem chama o que falha, cota do Hydrogen, Kiro novo, provedores extras."""
import json
import sqlite3

db = sqlite3.connect("file:/opt/omniroute/data/storage.sqlite?mode=ro", uri=True, timeout=30)
Q = lambda s, p=(): db.execute(s, p).fetchall()
H24 = "strftime('%Y-%m-%dT%H:%M:%S','now','-24 hours')"

print("== quem pede gemini-4 pelo AI Studio (24 h): chave | pedido | combo | n | ok ==")
for r in Q(f"""SELECT coalesce(api_key_name,'-'), requested_model, coalesce(combo_name,'-'), count(*), sum(status=200)
               FROM call_logs WHERE provider='gemini' AND model LIKE 'gemini-4%' AND timestamp>={H24}
               GROUP BY 1,2,3 ORDER BY 4 DESC LIMIT 10"""):
    print("  ", " | ".join(str(x) for x in r))

print("\n== pedidos por nome pedido que falharam muito (24 h, >=10, <50% ok) ==")
for r in Q(f"""SELECT requested_model, count(*), sum(status=200), round(100.0*sum(status=200)/count(*))
               FROM call_logs WHERE timestamp>={H24} GROUP BY 1 HAVING count(*)>=10 AND sum(status=200)*2<count(*)
               ORDER BY 2 DESC LIMIT 15"""):
    print("  ", " | ".join(str(x) for x in r))

print("\n== combos (nome: modelos) ==")
for nome, data in Q("SELECT name, data FROM combos ORDER BY name"):
    ms = [m.get("model") for m in json.loads(data).get("models", [])]
    uniq = []
    for m in ms:
        if m not in uniq:
            uniq.append(m)
    print(f"  {nome}: {len(ms)} passos {uniq[:8]}")

print("\n== mapeamentos ==")
for r in Q("SELECT m.pattern, c.name, m.enabled FROM model_combo_mappings m LEFT JOIN combos c ON c.id=m.combo_id"):
    print("  ", r)

print("\n== Hydrogen no Antigravity: ultima foto de cota por conta ==")
fotos = Q(f"""SELECT s.connection_id, s.window_key, s.remaining_percentage, s.is_exhausted, s.next_reset_at
              FROM quota_snapshots s JOIN (SELECT connection_id, window_key, max(id) mid FROM quota_snapshots
              WHERE provider='antigravity' AND created_at>={H24} GROUP BY 1,2) u ON s.id=u.mid""")
wk = {}
for cid, w, rem, ex, nr in fotos:
    wk.setdefault(w, []).append((rem, ex, nr))
for w in sorted(wk):
    if any(x in w.lower() for x in ("hydrogen", "gemini", "flash", "neon", "argon", "carbon")):
        v = wk[w]
        print(f"  {w}: {len(v)} contas, esgotadas {sum(1 for x in v if x[1])}, "
              f"media restante {sum((x[0] or 0) for x in v) / len(v):.0f}%, proximo reset {min((x[2] or 'z') for x in v)[:16]}")
print("  hydrogen pelo antigravity 24 h:", Q(f"""SELECT status, count(*) FROM usage_history WHERE provider='antigravity'
      AND model LIKE '%hydrogen%' AND timestamp>={H24} GROUP BY 1"""))

print("\n== Kiro: conta com modelos novos e conta-gota ==")
for k, v in Q("SELECT key, value FROM key_value WHERE namespace='syncedAvailableModels' AND key LIKE 'kiro:%'"):
    if "opus-5.5" in v or "gpt-5.6" in v:
        cid = k.split(":")[-1]
        print("  ", Q("SELECT name, is_active, test_status, substr(coalesce(last_error,''),1,80), created_at "
                      "FROM provider_connections WHERE id=?", (cid,)))
        print("   modelos:", [m.get("id") for m in json.loads(v)])
print("  kiro ativas/pausadas/banidas:", Q("SELECT test_status, is_active, count(*) FROM provider_connections "
                                          "WHERE provider='kiro' GROUP BY 1,2"))
try:
    est = json.load(open("/opt/omniroute/kiro_conta_gota.json"))
    print("  conta-gota:", {k: (v if not isinstance(v, (list, dict)) else len(v)) for k, v in est.items()})
except OSError as e:
    print("  conta-gota sem estado:", e)
try:
    print("  config:", open("/opt/omniroute/kiro_conta_gota_config.json").read()[:200])
except OSError:
    print("  config: padrao (folga 1.0)")
print("  saldo kiro (ultima foto por conta):", Q(f"""SELECT count(*), round(sum(remaining_percentage)) FROM quota_snapshots s
      JOIN (SELECT connection_id, max(id) mid FROM quota_snapshots WHERE provider='kiro' AND created_at>={H24} GROUP BY 1) u
      ON s.id=u.mid"""))

print("\n== provedores extras: sucesso 7 dias por modelo ==")
for r in Q("""SELECT provider||'/'||model, count(*), sum(success), round(avg(latency_ms)/1000.0,1), max(timestamp)
              FROM usage_history WHERE provider IN ('fireworks','groq','deepinfra','openrouter','novita','cohere','gemini-web','agy')
              AND timestamp >= strftime('%Y-%m-%dT%H:%M:%S','now','-7 days') GROUP BY 1 ORDER BY 2 DESC LIMIT 20"""):
    print("  ", " | ".join(str(x)[:60] for x in r))
print("  contas ativas:", Q("""SELECT provider, count(*), sum(is_active) FROM provider_connections
      WHERE provider IN ('fireworks','groq','deepinfra','openrouter','novita','cohere','gemini-web','agy') GROUP BY 1"""))
