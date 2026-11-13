#!/usr/bin/env python3
"""Guarda do Claude 5.5 pelo Antigravity no OmniRoute (VPS 157, cron 5 min).

Por que existe (04/11/2026): o OmniRoute corta o sufixo de esforco do nome do modelo
(claude-opus-5-5-high -> claude-opus-5-5) antes de mandar ao Google. No daily-cloudcode-pa
o nome sem sufixo da 404 e ele cai no cloudcode-pa, que responde 429 "Resource has been
exhausted" (enganoso). O apelido mitmAlias[antigravity]["claude-opus-5-5"] = "...-high"
devolve o nome certo. Uma sincronizacao de modelos pode reescrever esse mapa: este guarda repoe.

Tambem mantem os combos ag-opus-5-5 / ag-sonnet-5-5 com TODAS as contas antigravity ativas
cuja lista sincronizada (syncedAvailableModels) ja tem o modelo. So LE o banco e chama a API
LOCAL do OmniRoute; NAO fala com o Google (nao toca conta nenhuma).

Uso: python3 ag55_guarda.py [--simular]
"""
import json
import sqlite3
import subprocess
import sys
import urllib.request

DB = "/opt/omniroute/data/storage.sqlite"
BASE = "http://localhost:20128"
SIMULAR = "--simular" in sys.argv
# combo -> (modelo com sufixo que funciona, nome cortado que o OmniRoute manda)
ALVOS = {
    "ag-opus-5-5": ("claude-opus-5-5-high", "claude-opus-5-5"),
    "ag-sonnet-5-5": ("claude-sonnet-5-5-high", "claude-sonnet-5-5"),
}


def log(msg):
    print(msg, flush=True)


def apelidos(c):
    linha = c.execute("SELECT value FROM key_value WHERE namespace='mitmAlias' AND key='antigravity'").fetchone()
    mapa = json.loads(linha[0]) if linha else {}
    mudou = False
    for modelo, cortado in ALVOS.values():
        certo = f"antigravity/{modelo}"
        if mapa.get(cortado) != certo:
            log(f"apelido {cortado} -> {certo} (era {mapa.get(cortado)!r})")
            mapa[cortado] = certo
            mudou = True
    if mudou and not SIMULAR:
        if linha:
            c.execute("UPDATE key_value SET value=? WHERE namespace='mitmAlias' AND key='antigravity'", (json.dumps(mapa),))
        else:
            c.execute("INSERT INTO key_value(namespace,key,value) VALUES('mitmAlias','antigravity',?)", (json.dumps(mapa),))
        c.commit()


def contas_com(c, modelo):
    ids = []
    for (cid,) in c.execute("SELECT id FROM provider_connections WHERE provider='antigravity' AND is_active=1 ORDER BY priority"):
        v = c.execute("SELECT value FROM key_value WHERE namespace='syncedAvailableModels' AND key=?", (f"antigravity:{cid}",)).fetchone()
        if v and any(m.get("id") == modelo for m in json.loads(v[0])):
            ids.append(cid)
    return ids


def login():
    senha = subprocess.check_output(["docker", "exec", "omniroute", "printenv", "INITIAL_PASSWORD"], text=True).strip()
    req = urllib.request.Request(f"{BASE}/api/auth/login", data=json.dumps({"password": senha}).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    r = urllib.request.urlopen(req, timeout=30)
    for ck in r.headers.get_all("Set-Cookie") or []:
        if "auth_token=" in ck:
            return ck.split("auth_token=")[1].split(";")[0]
    raise SystemExit("login no painel falhou")


def combos(c):
    token = None
    for nome, (modelo, _) in ALVOS.items():
        linha = c.execute("SELECT id, data FROM combos WHERE name=?", (nome,)).fetchone()
        if not linha:
            log(f"combo {nome} nao existe (criar pelo painel/API)")
            continue
        cid, dados = linha[0], json.loads(linha[1])
        atuais = [m.get("connectionId") for m in dados.get("models", [])]
        quero = contas_com(c, modelo)
        if not quero or quero == atuais:
            continue
        log(f"{nome}: contas {len(atuais)} -> {len(quero)}")
        if SIMULAR:
            continue
        token = token or login()
        corpo = {"name": nome, "strategy": "priority",
                 "models": [{"kind": "model", "model": f"antigravity/{modelo}", "providerId": "antigravity",
                             "connectionId": x, "weight": 0} for x in quero]}
        req = urllib.request.Request(f"{BASE}/api/combos/{cid}", data=json.dumps(corpo).encode(),
                                     headers={"Content-Type": "application/json", "Cookie": f"auth_token={token}"},
                                     method="PUT")
        r = urllib.request.urlopen(req, timeout=30)
        log(f"{nome}: PUT {r.status}")


if __name__ == "__main__":
    con = sqlite3.connect(DB, timeout=30)
    apelidos(con)
    combos(con)
