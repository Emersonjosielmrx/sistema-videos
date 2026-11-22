#!/usr/bin/env python3
"""22/11 (dona): sonnet-fila so com o Sonnet web (cw/). Tira o claude/claude-sonnet-5-5 (gasta a conta cc).
Copia do combo antes em /opt/omniroute/backup_sonnet_fila_22nov.json."""
import json
import os
import sqlite3
import sys

sys.path.insert(0, "/opt/omniroute")
from ag55_guarda import BASE, DB, login  # noqa: E402
import urllib.request  # noqa: E402

con = sqlite3.connect(DB, timeout=30)
cid, dados = con.execute("SELECT id, data FROM combos WHERE name='sonnet-fila'").fetchone()
dados = json.loads(dados)
bk = "/opt/omniroute/backup_sonnet_fila_22nov.json"
if not os.path.exists(bk):
    with open(bk, "w") as f:
        json.dump(dados, f)
passos = [m for m in dados.get("models", []) if str(m.get("model", "")).startswith("cw/")]
print("antes:", [m.get("model") for m in dados.get("models", [])])
if not passos:
    sys.exit("sem passo cw/ no combo; nada feito")
if len(passos) == len(dados.get("models", [])):
    sys.exit("ja esta so com o Sonnet web")
req = urllib.request.Request(f"{BASE}/api/combos/{cid}", data=json.dumps({"models": passos}).encode(),
                             headers={"Content-Type": "application/json", "Cookie": f"auth_token={login()}"},
                             method="PUT")
print("PUT", urllib.request.urlopen(req, timeout=30).status)
novo = json.loads(con.execute("SELECT data FROM combos WHERE id=?", (cid,)).fetchone()[0])
print("depois:", [m.get("model") for m in novo.get("models", [])])
