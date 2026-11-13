#!/usr/bin/env python3
"""Roda NA VPS 157. Põe as contas WEB (cw/) em 1º no combo sonnet-fila; Claude Code (claude/) só de reserva.
Uso: python3 combo_inverter.py SENHA"""
import json
import sys
import urllib.request

BASE = "http://localhost:20128"
CID = "ID_UUID_DA_SUA_INSTALACAO"


def pedir(metodo, rota, corpo=None, token=None):
    h = {"Content-Type": "application/json"}
    if token:
        h["Cookie"] = f"auth_token={token}"
    req = urllib.request.Request(BASE + rota, data=json.dumps(corpo).encode() if corpo is not None else None,
                                 headers=h, method=metodo)
    try:
        r = urllib.request.urlopen(req, timeout=60)
        return r, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        return e, {"erro": e.code, "corpo": e.read().decode()[:500]}


r, _ = pedir("POST", "/api/auth/login", {"password": sys.argv[1]})
token = next((c.split("auth_token=")[1].split(";")[0] for c in r.headers.get_all("Set-Cookie") or [] if "auth_token=" in c), "")
modelos = [{"kind": "model", "model": "cw/claude-sonnet-5-5", "providerId": "claude-web", "weight": 0},
           {"kind": "model", "model": "claude/claude-sonnet-5-5", "providerId": "claude", "weight": 0}]
for metodo in ("PUT", "PATCH"):
    _, res = pedir(metodo, f"/api/combos/{CID}", {"name": "sonnet-fila", "strategy": "priority", "models": modelos}, token)
    print(metodo, json.dumps(res)[:300])
    if "erro" not in res:
        break
