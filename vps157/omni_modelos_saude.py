#!/usr/bin/env python3
"""So leitura do banco do OmniRoute: saude por modelo (Gemini 4/Argon/Hydrogen/Kiro), modelos novos ja sincronizados
nas contas (syncedAvailableModels) e como o Kiro troca de conta. NAO chama Google/Kiro (regra: nunca varrer contas)."""
import collections
import json
import sqlite3

db = sqlite3.connect("file:/opt/omniroute/data/storage.sqlite?mode=ro", uri=True, timeout=30)
Q = lambda s, p=(): db.execute(s, p).fetchall()

print("== saude por modelo, 6 h (usage_history): provedor/modelo | n | ok | % | latencia media s ==")
for r in Q("""SELECT provider||'/'||model, count(*), sum(success), round(100.0*sum(success)/count(*)),
              round(avg(latency_ms)/1000.0,1) FROM usage_history
              WHERE timestamp >= strftime('%Y-%m-%dT%H:%M:%S','now','-6 hours')
                AND (model LIKE '%gemini-4%' OR model LIKE '%argon%' OR model LIKE '%hydrogen%' OR model LIKE '%neon%'
                     OR model LIKE '%carbon%' OR provider IN ('kiro','gemini') OR model LIKE '%3.8%' OR model LIKE '%3-8%')
              GROUP BY 1 HAVING count(*)>=3 ORDER BY 2 DESC LIMIT 30"""):
    print("  ", " | ".join(str(x) for x in r))

print("\n== erros mais comuns, 6 h, por modelo ==")
for r in Q("""SELECT provider||'/'||model, status, coalesce(error_code,'-'), count(*) FROM usage_history
              WHERE success=0 AND timestamp >= strftime('%Y-%m-%dT%H:%M:%S','now','-6 hours')
                AND (model LIKE '%argon%' OR model LIKE '%hydrogen%' OR provider='kiro' OR model LIKE '%gemini-4%')
              GROUP BY 1,2,3 ORDER BY 4 DESC LIMIT 15"""):
    print("  ", " | ".join(str(x) for x in r))
for r in Q("""SELECT provider||'/'||model, substr(coalesce(error_summary,''),1,140), count(*) FROM call_logs
              WHERE status>=400 AND timestamp >= strftime('%Y-%m-%dT%H:%M:%S','now','-6 hours')
                AND (model LIKE '%argon%' OR model LIKE '%hydrogen%' OR provider='kiro')
              GROUP BY 1,2 ORDER BY 3 DESC LIMIT 12"""):
    print("   call_logs:", " | ".join(str(x) for x in r))

print("\n== modelos sincronizados por provedor (contas ativas): modelo | contas ==")
alvo = ("neon", "argon", "carbon", "hydrogen", "gemini-4", "gemini-5", "opus", "sonnet", "fable", "haiku", "gpt", "3.9",
        "3-9", "4.5", "4-5")
for prov in ("antigravity", "gemini", "kiro"):
    cont = collections.Counter()
    n = 0
    for (psd,) in Q("SELECT provider_specific_data FROM provider_connections WHERE provider=? AND is_active=1", (prov,)):
        n += 1
        try:
            d = json.loads(psd or "{}")
        except ValueError:
            continue
        ms = d.get("syncedAvailableModels") or d.get("availableModels") or []
        for m in ms:
            nome = m if isinstance(m, str) else (m.get("id") or m.get("name") or m.get("model") or "")
            cont[str(nome)] += 1
    print(f"  [{prov}] {n} contas ativas, {len(cont)} modelos distintos sincronizados")
    for nome, c in sorted(cont.items(), key=lambda x: (-x[1], x[0])):
        if any(a in nome.lower() for a in alvo):
            print(f"     {nome} | {c}")

print("\n== catalogo do gateway com nomes novos (model_intelligence/model_context_overrides) ==")
for t in ("model_intelligence", "model_context_overrides"):
    cols = [c[1] for c in Q(f"PRAGMA table_info({t})")]
    col = next((c for c in cols if c in ("model", "model_id", "id", "name")), cols[0])
    for (m,) in Q(f"SELECT DISTINCT {col} FROM {t}"):
        if any(a in str(m).lower() for a in ("neon", "argon", "carbon", "hydrogen", "gemini-4", "gemini-5")):
            print(f"   {t}: {m}")

print("\n== Kiro: contas e troca (6 h) ==")
print("  contas:", Q("SELECT count(*), sum(is_active) FROM provider_connections WHERE provider='kiro'"))
print("  ativas com rate_limited_until futuro:",
      Q("SELECT count(*) FROM provider_connections WHERE provider='kiro' AND is_active=1 "
        "AND rate_limited_until > strftime('%Y-%m-%dT%H:%M:%S','now')"))
seq = Q("""SELECT timestamp, connection_id, success, status FROM usage_history
           WHERE provider='kiro' AND timestamp >= strftime('%Y-%m-%dT%H:%M:%S','now','-6 hours') ORDER BY timestamp""")
falhas_antes_troca = []
corrida = 0
ult = None
for ts, cid, ok, st in seq:
    if ok:
        if corrida:
            falhas_antes_troca.append((corrida, ult == cid))
        corrida = 0
    else:
        corrida += 1
    ult = cid
print(f"  {len(seq)} tentativas; sequencias de falha antes de um sucesso: {len(falhas_antes_troca)}")
if falhas_antes_troca:
    tam = [x[0] for x in falhas_antes_troca]
    print(f"  falhas seguidas: media {sum(tam)/len(tam):.1f}, max {max(tam)}; "
          f"sucesso na MESMA conta que falhou por ultimo: {sum(1 for x in falhas_antes_troca if x[1])}")
for r in Q("""SELECT substr(connection_id,1,8), count(*), sum(success), max(timestamp) FROM usage_history
              WHERE provider='kiro' AND timestamp >= strftime('%Y-%m-%dT%H:%M:%S','now','-6 hours')
              GROUP BY 1 ORDER BY 2 DESC LIMIT 8"""):
    print("   conta", " | ".join(str(x) for x in r))
print("  regras de erro do kiro (key_value):")
for k, v in Q("SELECT key, substr(value,1,300) FROM key_value WHERE lower(key) LIKE '%kiro%' OR "
              "(lower(key) LIKE '%providererrorrules%') LIMIT 6"):
    print("   ", k, "=", v)
