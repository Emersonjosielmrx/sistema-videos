#!/usr/bin/env python3
"""So leitura: chaves do AI Studio que listam Gemini 4 (nome, plano, ultimo sucesso por modelo) e quem desligou o Kiro
em 23/11 05h (audit_log, scripts com cron). NAO chama Google/Kiro."""
import glob
import json
import re
import sqlite3

db = sqlite3.connect("file:/opt/omniroute/data/storage.sqlite?mode=ro", uri=True, timeout=30)
Q = lambda s, p=(): db.execute(s, p).fetchall()

print("== chaves do AI Studio que listam algum gemini-4 ==")
for k, v in Q("SELECT key, value FROM key_value WHERE namespace='syncedAvailableModels' AND key LIKE 'gemini:%'"):
    cid = k.split(":")[-1]
    try:
        ms = {m.get("id") if isinstance(m, dict) else str(m) for m in json.loads(v)}
    except ValueError:
        continue
    g4 = sorted(m for m in ms if "gemini-4" in m)
    if not g4:
        continue
    r = Q("SELECT name, is_active, test_status, synced_models_at FROM provider_connections WHERE id=?", (cid,))
    nome, ativa, st, sync = r[0] if r else ("?", None, None, None)
    ok = {m: Q("SELECT max(timestamp) FROM usage_history WHERE connection_id=? AND model=? AND success=1", (cid, m))[0][0]
          for m in g4}
    tent = Q("SELECT count(*), sum(success) FROM usage_history WHERE connection_id=? AND model LIKE 'gemini-4%' "
             "AND timestamp >= strftime('%Y-%m-%dT%H:%M:%S','now','-3 days')", (cid,))[0]
    print(f"  {str(nome)[:28]} ativa={ativa} st={st} sync={str(sync)[:10]} g4={g4}")
    print(f"     tentativas gemini-4 em 3 dias: {tent[0]} ok={tent[1]} | ultimo sucesso: "
          + ", ".join(f"{m}={str(t)[:16]}" for m, t in ok.items()))

print("\n== Gemini 4 (AI Studio) sucesso por modelo, 7 dias ==")
for r in Q("""SELECT model, count(*), sum(success), max(CASE WHEN success=1 THEN timestamp END) FROM usage_history
              WHERE provider='gemini' AND model LIKE 'gemini-4%' AND timestamp >= strftime('%Y-%m-%dT%H:%M:%S','now','-7 days')
              GROUP BY 1"""):
    print("  ", " | ".join(str(x) for x in r))

print("\n== audit_log 23/11 04:30-06:30 que nao seja spec_violation ==")
for r in Q("""SELECT timestamp, action, actor, substr(target,1,50), substr(CAST(details AS TEXT),1,140) FROM audit_log
              WHERE timestamp BETWEEN '2026-11-23T04:30' AND '2026-11-23T06:30' AND action NOT LIKE '%spec_violation%'
              ORDER BY timestamp LIMIT 15"""):
    print("  ", " | ".join(str(x) for x in r))
print("  acoes por tipo nesse intervalo:",
      Q("SELECT action, count(*) FROM audit_log WHERE timestamp BETWEEN '2026-11-23T04:30' AND '2026-11-23T06:30' GROUP BY 1"))

print("\n== kiro desligadas: ultimo erro e quando ==")
for r in Q("""SELECT test_status, coalesce(error_code,'-'), coalesce(last_error_type,'-'), substr(coalesce(last_error,''),1,70),
              count(*), max(updated_at) FROM provider_connections WHERE provider='kiro' AND is_active=0 GROUP BY 1,2,3,4
              ORDER BY 5 DESC LIMIT 8"""):
    print("  ", " | ".join(str(x) for x in r))

print("\n== scripts que mexem em is_active do kiro ==")
for f in sorted(glob.glob("/opt/omniroute/*.py") + glob.glob("/opt/omniroute/*.sh")):
    try:
        s = open(f, errors="replace").read()
    except OSError:
        continue
    if "kiro" in s and re.search(r"is_active\s*=\s*0|is_active=0|isActive.{0,5}false|desliga", s):
        print("  ", f)
print("  cron que menciona kiro:")
for f in glob.glob("/etc/cron.d/*"):
    s = open(f, errors="replace").read()
    if "kiro" in s.lower():
        print("    ", f, "->", " ".join(l for l in s.splitlines() if l and not l.startswith("#"))[:160])
