#!/usr/bin/env python3
"""Roda NA VPS 157. Imprime em JSON o estado das contas claude-web do OmniRoute (sem cookie):
{"agora": iso, "contas": [{"nome","ativa","status","erro","limitada_ate"}]}. Usado pelo monitor_sonnet.py e
zelador_sonnet.py do PC1 (D:\\sonnet web). status "error" também quando a conta só leva 403 (ver so_403)."""
import json
import sqlite3
from datetime import datetime, timezone

db = sqlite3.connect("file:/opt/omniroute/data/storage.sqlite?mode=ro", uri=True)
agora = datetime.now(timezone.utc)
out = []
def so_403(cid):
    """30/10: com o health check desligado, conta com sessão morta (claude.ai devolve 403 permission_denied) seguia
    'pronta'. Em 24 h: 5+ respostas 403 e nenhuma 200 = cookie ruim (o zelador renova). Um 200 depois limpa."""
    n403, n200 = db.execute(
        "SELECT SUM(CAST(status AS INTEGER)=403), SUM(CAST(status AS INTEGER)=200) FROM usage_history "
        "WHERE provider='claude-web' AND connection_id=? AND timestamp > strftime('%Y-%m-%dT%H:%M:%S','now','-24 hours')",
        (cid,)).fetchone()
    return (n403 or 0) >= 5 and not n200


for cid, nome, ativa, status, erro, ate in db.execute(
        "SELECT id, name, is_active, test_status, last_error, rate_limited_until FROM provider_connections "
        "WHERE provider='claude-web' ORDER BY priority").fetchall():
    if so_403(cid):
        status, erro = "error", "403 permission_denied seguidos (sessão do claude.ai recusada)"
    limitada = None
    if ate:
        try:
            t = datetime.fromisoformat(str(ate).replace("Z", "+00:00"))
            if t > agora:
                limitada = t.isoformat()
        except ValueError:
            pass
    out.append({"nome": nome, "ativa": bool(ativa), "status": status, "erro": (erro or "")[:120],
                "limitada_ate": limitada})
print(json.dumps({"agora": agora.isoformat(), "contas": out}, ensure_ascii=False))
