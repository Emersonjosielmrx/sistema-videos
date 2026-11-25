#!/usr/bin/env python3
"""23/11: mapeia os nomes do AI Studio (acertavam 3-53%) para a gemini-studio-fila (Gemini 3.8 Antigravity 1o, o
AI Studio por ultimo). Desfazer: --desfazer (apaga so estes mapeamentos)."""
import json
import sys
import sqlite3
import urllib.request

sys.path.insert(0, "/opt/omniroute")
from ag55_guarda import BASE, DB, STUDIO, login  # noqa: E402


def pedir(metodo, rota, corpo, token):
    req = urllib.request.Request(BASE + rota, data=json.dumps(corpo).encode() if corpo is not None else None,
                                 method=metodo, headers={"Content-Type": "application/json", "Cookie": f"auth_token={token}"})
    try:
        r = urllib.request.urlopen(req, timeout=30)
        return r.status, r.read()[:200]
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:200]


c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
cid = c.execute("SELECT id FROM combos WHERE name='gemini-studio-fila'").fetchone()[0]
ja = {p: mid for mid, p in c.execute("SELECT id, pattern FROM model_combo_mappings")}
tok = login()
for nome in STUDIO:
    if "--desfazer" in sys.argv:
        if nome in ja:
            print(nome, "apagar", pedir("DELETE", f"/api/model-combo-mappings/{ja[nome]}", None, tok))
        continue
    if nome in ja:
        print(nome, "ja mapeado")
        continue
    print(nome, pedir("POST", "/api/model-combo-mappings",
                      {"pattern": nome, "comboId": cid, "priority": 1, "enabled": True,
                       "description": "23/11: AI Studio -> Gemini 3.8 Antigravity primeiro"}, tok))
