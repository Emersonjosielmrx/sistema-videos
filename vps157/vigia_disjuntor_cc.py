#!/usr/bin/env python3
"""Roda NA VPS 157 (cron 1 min). Destrava o Opus pago quando o disjuntor do cc/claude fica preso aberto.

23/11 (dona: "usando o Opus pago no seletor ele parou com 'all targets were skipped by pre-dispatch filters', mas a
conta tinha credito; no Opus 5.5 direto respondia"): o log mostrava "Skipping cc/claude-opus-5-5 — circuit breaker OPEN
for cc" por 20+ min. O disjuntor abre com 8 falhas (502 vazio, pedido longo cortado) e o proprio Claude Code reenvia
em rajada, entao ele nunca fica calmo para fechar. So o combo respeita o disjuntor; o cc direto passa por fora.
Aqui: se nos ultimos 2 min o log tem >= LIMITE "circuit breaker OPEN for cc/claude" E ha conta cc com credito
(quota_snapshots, so leitura), chama POST /api/resilience/reset (o mesmo do botao "liberar" do painel). No maximo 1
reset a cada 3 min. NAO chama Anthropic nem conta nenhuma. Arquivo /opt/omniroute/vigia_disjuntor.desligar = desliga.
"""
import json
import os
import sqlite3
import subprocess
import time
import urllib.request
from datetime import datetime, timedelta, timezone

DB = "/opt/omniroute/data/storage.sqlite"
BASE = "http://localhost:20128"
LOG = "/opt/omniroute/vigia_disjuntor_cc.log"
ESTADO = "/opt/omniroute/vigia_disjuntor_cc.json"
DESLIGAR = "/opt/omniroute/vigia_disjuntor.desligar"
LIMITE = 3
INTERVALO_S = 180


def log(msg):
    with open(LOG, "a") as f:
        f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} {msg}\n")


def cc_com_credito():
    db = sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=30)
    agora = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    desde = (datetime.now(timezone.utc) - timedelta(hours=12)).strftime("%Y-%m-%dT%H:%M:%S")
    ativas = {r[0] for r in db.execute("SELECT id FROM provider_connections WHERE provider='claude' AND is_active=1 "
                                       "AND (rate_limited_until IS NULL OR rate_limited_until < ?)", (agora,))}
    esgot = set()
    for cid, ex, nr in db.execute(
            "SELECT s.connection_id, s.is_exhausted, s.next_reset_at FROM quota_snapshots s JOIN (SELECT connection_id, "
            "window_key, max(id) mid FROM quota_snapshots WHERE provider='claude' AND created_at>? AND window_key IN "
            "('session (5h)','weekly (7d)') GROUP BY 1,2) u ON s.id=u.mid", (desde,)):
        if ex and nr and nr[:19] > agora:
            esgot.add(cid)
    return len(ativas - esgot)


def login():
    senha = subprocess.check_output(["docker", "exec", "omniroute", "printenv", "INITIAL_PASSWORD"], text=True).strip()
    r = urllib.request.urlopen(urllib.request.Request(f"{BASE}/api/auth/login", data=json.dumps({"password": senha}).encode(),
                                                      headers={"Content-Type": "application/json"}, method="POST"), timeout=30)
    for ck in r.headers.get_all("Set-Cookie") or []:
        if "auth_token=" in ck:
            return ck.split("auth_token=")[1].split(";")[0]
    raise SystemExit("login falhou")


def main():
    if os.path.exists(DESLIGAR):
        return
    try:
        est = json.load(open(ESTADO))
    except (OSError, ValueError):
        est = {}
    if time.time() - est.get("ultimo", 0) < INTERVALO_S:
        return
    saida = subprocess.run(["docker", "logs", "--since", "2m", "omniroute"], capture_output=True, text=True, timeout=60)
    texto = saida.stdout + saida.stderr
    abertos = texto.count("circuit breaker OPEN for cc") + texto.count("Circuit breaker OPEN for claude")
    if abertos < LIMITE:
        return
    credito = cc_com_credito()
    if credito == 0:
        log(f"disjuntor aberto ({abertos}x em 2 min), mas nenhuma conta cc com credito: nao reseto")
        return
    req = urllib.request.Request(f"{BASE}/api/resilience/reset", data=b"{}", method="POST",
                                 headers={"content-type": "application/json", "Cookie": f"auth_token={login()}"})
    r = urllib.request.urlopen(req, timeout=30)
    est["ultimo"] = time.time()
    est["resets"] = est.get("resets", 0) + 1
    json.dump(est, open(ESTADO, "w"))
    log(f"disjuntor do cc aberto {abertos}x em 2 min com {credito} conta(s) cc com credito: reset {r.status}")


if __name__ == "__main__":
    main()
