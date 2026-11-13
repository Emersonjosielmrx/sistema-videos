#!/usr/bin/env python3
"""Roda NA VPS 157. Cria o combo `sonnet-fila` (claude/claude-sonnet-5-5 -> cw/claude-sonnet-5-5) e o mapeamento
claude/claude-sonnet-5-5 -> sonnet-fila: quem pede o Sonnet das contas do Claude Code cai nas contas web quando a cota
acaba, sem mudar settings (mesmo molde do haiku-fila). Uso: python3 combo_sonnet_fila.py SENHA"""
import json
import sys
import urllib.request

BASE = "http://localhost:20128"


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
token = next((c.split("auth_token="<SEGREDO_REMOVIDO>";")[0] for c in r.headers.get_all("Set-Cookie") or [] if "auth_token=" in c), "")
if not token:
    sys.exit("login falhou")

_, combo = pedir("POST", "/api/combos", {
    "name": "sonnet-fila", "strategy": "priority",
    "models": [{"kind": "model", "model": "claude/claude-sonnet-5-5", "providerId": "claude", "weight": 0},
               {"kind": "model", "model": "cw/claude-sonnet-5-5", "providerId": "claude-web", "weight": 0}]}, token)
print("combo:", json.dumps(combo)[:400])
cid = (combo.get("combo") or combo).get("id")
if not cid:
    sys.exit("combo não criado")
_, m = pedir("POST", "/api/model-combo-mappings", {"pattern": "claude/claude-sonnet-5-5", "comboId": cid, "priority": 1,
                                                   "enabled": True,
                                                   "description": "Sonnet Claude Code -> contas claude.ai web (29/10)"},
             token)
print("mapeamento:", json.dumps(m)[:400])
