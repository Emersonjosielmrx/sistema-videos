#!/usr/bin/env python3
"""Roda NA VPS 157 (cópia em /opt/omniroute/ler_claude_web.py). Só leitura do banco do OmniRoute: contas claude-web
(nome, ativa, prioridade, limitada até) e uso das últimas 24 h por conta/status/latência. Imprime JSON. Sem segredos."""
import json
import sqlite3
import datetime as dt

db = sqlite3.connect("file:/opt/omniroute/data/storage.sqlite?mode=ro", uri=True, timeout=30)
agora = dt.datetime.utcnow()
contas = []
for cid, nome, ativa, prio, rl in db.execute(
        "select id,name,is_active,priority,rate_limited_until from provider_connections where provider='claude-web' order by priority"):
    uso = {}
    for st, n, lat in db.execute(
            "select status,count(*),round(avg(latency_ms)) from usage_history where provider='claude-web' and connection_id=? "
            "and timestamp>? group by status", (cid, (agora - dt.timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%S"))):
        uso[str(st)] = {"n": n, "ms": lat}
    ultimo = db.execute("select timestamp,status from usage_history where provider='claude-web' and connection_id=? "
                        "order by timestamp desc limit 1", (cid,)).fetchone()
    contas.append({"id": cid[:8], "nome": nome, "ativa": bool(ativa), "prioridade": prio,
                   "limitada_ate": (rl or "")[:19] or None, "limitada_agora": bool(rl and rl[:19] > agora.strftime("%Y-%m-%dT%H:%M:%S")),
                   "uso_24h": uso, "ultimo": list(ultimo) if ultimo else None})
# Opus 4.6 (antigravity): sonda individual "oi" (probe_opus.py) — vivas agora, últimas voltas, e o estado do funil
opus = {}
try:
    import os
    v = json.load(open("/opt/omniroute/probe_opus_voltas.json")) if os.path.exists("/opt/omniroute/probe_opus_voltas.json") else {}
    opus["vivas"] = sorted(n for n, x in v.items() if x.get("ultimo") == "viva")
    opus["ultimas_voltas"] = sorted(((x.get("voltou_em"), n) for n, x in v.items() if x.get("voltou_em")), reverse=True)[:8]
    opus["sondadas"] = len(v)
    with open("/opt/omniroute/probe_opus.log") as f:
        opus["ultima_sonda"] = f.readlines()[-1].strip()[:300]
    ag = {}
    for st, n in db.execute("select status,count(*) from usage_history where provider='antigravity' and model='claude-opus-4-6-thinking' "
                            "and timestamp>? group by status", ((agora - dt.timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M:%S"),)):
        ag[str(st)] = n
    opus["opus_3h_por_status"] = ag
    opus["ativas"] = db.execute("select count(*) from provider_connections where provider='antigravity' and is_active=1").fetchone()[0]
    opus["pausadas_agora"] = db.execute("select count(*) from provider_connections where provider='antigravity' and is_active=1 and rate_limited_until>?",
                                        (agora.strftime("%Y-%m-%dT%H:%M:%S"),)).fetchone()[0]
except Exception as e:  # noqa: BLE001
    opus["erro"] = str(e)[:120]
print(json.dumps({"em_utc": agora.strftime("%Y-%m-%dT%H:%M:%S"), "contas": contas, "opus": opus}, ensure_ascii=False))
