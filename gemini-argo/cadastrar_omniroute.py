#!/usr/bin/env python3
"""Cadastra contas gemini-web no OmniRoute via API. Roda NA VPS."""
import json, sys, urllib.request

TOKEN = sys.argv[1]  # auth_token do OmniRoute
BASE = "http://localhost:20128"


def cadastrar_bulk(contas):
    entries = [{"name": c["name"], "credential": c["cookie"]} for c in contas]
    payload = json.dumps({
        "provider": "gemini-web",
        "entries": entries,
    }).encode()
    req = urllib.request.Request(
        f"{BASE}/api/providers/bulk-web-session",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Cookie": f"auth_token={TOKEN}",
        },
        method="POST",
    )
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        body = json.loads(resp.read().decode())
        print(f"OK: {body.get('success', 0)} criadas, {body.get('failed', 0)} falharam")
        for c in body.get("created", []):
            print(f"  + {c['name']} (id={c['id']})")
        for e in body.get("errors", []):
            print(f"  ! {e}")
    except urllib.error.HTTPError as e:
        print(f"ERRO HTTP {e.code}: {e.read().decode()[:500]}")
    except Exception as e:
        print(f"ERRO: {e}")


if __name__ == "__main__":
    contas = json.loads(open("/tmp/gweb_contas.json").read())
    cadastrar_bulk(contas)
