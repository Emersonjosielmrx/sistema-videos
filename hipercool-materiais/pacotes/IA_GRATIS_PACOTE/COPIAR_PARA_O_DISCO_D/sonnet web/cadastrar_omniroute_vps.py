#!/usr/bin/env python3
"""Roda NA VPS 157 (stdin = JSON {email: {"cookie": ...}}). Faz login no painel do OmniRoute com a INITIAL_PASSWORD
do contêiner e cadastra cada conta no provedor claude-web. 29/10 (Fable, D26): conta que JÁ existe (mesmo nome
"claude-web <apelido>") é ATUALIZADA pelo PUT /api/providers/<id> (campo apiKey = cookie) em vez de duplicada; só a
nova vai pela rota bulk-web-session. Não imprime cookie.
Uso: cat cookies.json | python3 cadastrar_omniroute_vps.py SENHA [--simular]"""
import json
import sys
import urllib.request

BASE = "http://localhost:20128"
senha = sys.argv[1]
simular = "--simular" in sys.argv
contas = json.loads(sys.stdin.read())


def pedir(metodo, rota, corpo=None, token=None):
    h = {"Content-Type": "application/json"}
    if token:
        h["Cookie"] = f"auth_token={token}"
    req = urllib.request.Request(BASE + rota, data=json.dumps(corpo).encode() if corpo is not None else None, headers=h, method=metodo)
    try:
        r = urllib.request.urlopen(req, timeout=60)
        txt = r.read().decode()
        return r.status, (json.loads(txt) if txt.strip().startswith(("{", "[")) else txt)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:400]


resp = urllib.request.urlopen(urllib.request.Request(f"{BASE}/api/auth/login", data=json.dumps({"password": senha}).encode(),
                                                     headers={"Content-Type": "application/json"}, method="POST"), timeout=30)
token = next((c.split("auth_token=")[1].split(";")[0] for c in resp.headers.get_all("Set-Cookie") or [] if "auth_token=" in c), "")
if not token:
    sys.exit("login no painel falhou (sem auth_token)")

st, lista = pedir("GET", "/api/providers", token=token)
existentes = {}
if st == 200:
    itens = lista if isinstance(lista, list) else (lista.get("providers") or lista.get("data") or lista.get("connections") or [])
    for p in itens:
        if isinstance(p, dict) and p.get("provider") == "claude-web" and p.get("name"):
            existentes[p["name"]] = p.get("id")
else:
    print(f"aviso: GET /api/providers deu {st}; vou criar todas (pode duplicar)")

novas = []
for email, info in contas.items():
    nome = f"claude-web {email.split('@')[0]}"
    if nome in existentes:
        if simular:
            print(f"  = {nome}: existe (id={existentes[nome][:8]}), seria atualizada")
            continue
        st, r = pedir("PUT", f"/api/providers/{existentes[nome]}", {"apiKey": info["cookie"], "isActive": True}, token)
        print(f"  ~ {nome}: {'atualizada' if st == 200 else 'falhou ' + str(st) + ' ' + str(r)[:200]}")
    else:
        novas.append({"name": nome, "credential": info["cookie"]})
        if simular:
            print(f"  + {nome}: seria criada")
if novas and not simular:
    st, body = pedir("POST", "/api/providers/bulk-web-session", {"provider": "claude-web", "entries": novas}, token)
    if st == 200 and isinstance(body, dict):
        print(f"OK: {body.get('success', 0)} criadas, {body.get('failed', 0)} falharam")
        for c in body.get("created", []):
            print(f"  + {c.get('name')} (id={str(c.get('id'))[:8]})")
        for e in body.get("errors", []):
            print(f"  ! {str(e)[:300]}")
    else:
        print(f"ERRO HTTP {st}: {str(body)[:400]}")
