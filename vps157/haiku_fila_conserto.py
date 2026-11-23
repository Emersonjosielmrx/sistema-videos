#!/usr/bin/env python3
"""23/11: haiku-fila dava 0/35 (1o passo agy/ com conta desativada; 2o fixo em 1 conta antigravity). Passa a usar
as mesmas contas da gemini-fila (41, 100% ok) e o Kiro Haiku no fim. Backup do combo em backup_haiku_fila_23nov.json."""
import json
import os
import sqlite3
import sys
import urllib.request

sys.path.insert(0, "/opt/omniroute")
from ag55_guarda import BASE, DB, login  # noqa: E402

c = sqlite3.connect(DB, timeout=30)
hid, hdata = c.execute("SELECT id, data FROM combos WHERE name='haiku-fila'").fetchone()
gdata = json.loads(c.execute("SELECT data FROM combos WHERE name='gemini-fila'").fetchone()[0])
bk = "/opt/omniroute/backup_haiku_fila_23nov.json"
if not os.path.exists(bk):
    open(bk, "w").write(hdata)
gem = [{k: m[k] for k in ("kind", "model", "providerId", "connectionId", "weight") if k in m}
       for m in gdata["models"] if str(m.get("model", "")).startswith("antigravity/")]
novos = gem + [{"kind": "model", "model": "kr/claude-haiku-4.5", "providerId": "kiro", "weight": 0}]
req = urllib.request.Request(f"{BASE}/api/combos/{hid}", data=json.dumps({"models": novos}).encode(), method="PUT",
                             headers={"Content-Type": "application/json", "Cookie": f"auth_token={login()}"})
print("PUT", urllib.request.urlopen(req, timeout=30).status, "passos", len(novos))
