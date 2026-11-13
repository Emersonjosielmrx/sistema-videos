#!/usr/bin/env python3
"""
Reseta rateLimitedUntil das contas Antigravity no OmniRouter.
O OmniRouter marca contas com cooldown de 24h no 429, mas o upstream
se recupera muito antes. Este script limpa o bloqueio artificial.

Rodar via Task Scheduler a cada 30-60min, ou manualmente:
  d:/hipercool-videos/venv/Scripts/python.exe bin/omnirouter_reset_ratelimits.py
"""
import json, urllib.request, sys, os
from datetime import datetime

BASE = "http://157.173.207.22:20128"
PASSWORD = "<SEGREDO_REMOVIDO>"

def get_token():
    req = urllib.request.Request(
        f"{BASE}/api/auth/login",
        data=json.dumps({"password": PASSWORD}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        for h in resp.headers.get_all("Set-Cookie") or []:
            if "auth_token=" in h:
                return h.split("auth_token="<SEGREDO_REMOVIDO>";")[0]
    raise RuntimeError("login falhou — sem auth_token no cookie")

def main():
    token = get_token()
    headers = {"Cookie": f"auth_token={token}", "Content-Type": "application/json"}

    req = urllib.request.Request(f"{BASE}/api/providers", headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())

    conns = data.get("connections", data if isinstance(data, list) else [])
    cleared = 0
    for p in conns:
        if not isinstance(p, dict):
            continue
        if p.get("provider") != "antigravity":
            continue

        # Apenas reseta se for conta PRO (g1-pro-tier), pois as free-tier duram 7 dias bloqueadas
        tier = p.get("providerSpecificData", {}).get("tier", "?")
        if tier != "g1-pro-tier":
            continue

        if not p.get("rateLimitedUntil"):
            continue
        pid = p["id"]
        name = p.get("name", "?")
        put = urllib.request.Request(
            f"{BASE}/api/providers/{pid}",
            data=json.dumps({"rateLimitedUntil": None}).encode(),
            headers=headers,
            method="PUT",
        )
        try:
            with urllib.request.urlopen(put, timeout=10):
                cleared += 1
        except Exception as e:
            print(f"FAIL {name}: {e}", file=sys.stderr)

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    total_ag = sum(1 for p in conns if isinstance(p, dict) and p.get("provider") == "antigravity")
    if cleared:
        print(f"[{now}] Reset {cleared}/{total_ag} contas Antigravity")
    else:
        print(f"[{now}] Nenhuma conta bloqueada ({total_ag} disponiveis)")

if __name__ == "__main__":
    main()
