#!/usr/bin/env python3
"""Fila propria do Gemini no combo "gemini-fila" (cron a cada 2 min).

Pedido do dono (27/10/2026, refinado 29/10): Gemini e Opus nao podem se atrapalhar.
As contas com credito de Opus ficam FORA daqui (combo_opus_fila.py cuida delas).
Aqui so entram contas sem Opus (as "free") e com credito de Gemini, em ordem:
  1. a conta Pro do provedor agy (unica que serve gemini-3.8-flash-high);
  2. contas antigravity SEM credito Opus, COM credito Gemini: a que respondeu ok primeiro,
     depois as sem falha no Gemini na ultima hora;
  3. como rede de seguranca, contas COM Opus E Gemini que nao estao pausadas (so se sobrar).
Fora: inativas, sem projeto, em pausa, isoladas, e as que falharam no Gemini na ultima hora.
--simular mostra a fila sem gravar.
"""
import json
import sqlite3
import subprocess
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

DB = "/opt/omniroute/data/storage.sqlite"
LOG = "/opt/omniroute/ordenar_contas_gemini.log"
ISOLADAS = "/opt/omniroute/contas_isoladas.json"
BASE = "http://localhost:20128"
COMBO = "gemini-fila"
MODELO_PRO = "agy/gemini-3.8-flash-high"
MODELO_GRATIS = "antigravity/gemini-3.8-flash-tiered"
MODELO_OPUS = "claude-opus-4-6-thinking"
MAX_GRATIS = 56


def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


def fila():
    db = sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=30)
    agora = datetime.now(timezone.utc)
    try:
        isoladas = set(json.load(open(ISOLADAS)))
    except (OSError, ValueError):
        isoladas = set()
    pro = [r[0] for r in db.execute(
        "select id from provider_connections where provider='agy' and is_active=1 order by priority")]

    contas = {}
    for cid, name, psd, rl, prio in db.execute(
            "select id,name,provider_specific_data,rate_limited_until,priority "
            "from provider_connections where provider='antigravity' and is_active=1"):
        try:
            projeto = json.loads(psd or "{}").get("projectId")
        except ValueError:
            projeto = None
        if not projeto or cid in isoladas or (rl and rl[:19] > iso(agora)):
            continue
        contas[cid] = {"name": name, "prio": prio or 999, "ok": "", "falha": ""}

    desde = iso(agora - timedelta(hours=24))

    # credito opus (pra excluir)
    opus = set()
    for cid, ex in db.execute(
            "select s.connection_id,s.is_exhausted from quota_snapshots s "
            "join (select connection_id,max(id) mid from quota_snapshots "
            "where provider='antigravity' and window_key=? and created_at>? "
            "group by connection_id) u on s.id=u.mid", (MODELO_OPUS, desde)):
        if cid in contas and ex == 0:
            opus.add(cid)
    for cid, in db.execute(
            "select distinct connection_id from usage_history "
            "where provider='antigravity' and model=? and status='200' and timestamp>?",
            (MODELO_OPUS, desde)):
        if cid in contas:
            opus.add(cid)

    # historico gemini
    for cid, st, ts in db.execute(
            "select connection_id,status,max(timestamp) from usage_history "
            "where provider='antigravity' and model='gemini-3.8-flash-tiered' "
            "and timestamp>? group by 1,2", (desde,)):
        if cid in contas:
            if st == "200":
                contas[cid]["ok"] = ts
            else:
                contas[cid]["falha"] = max(contas[cid]["falha"], ts)

    uma_hora = iso(agora - timedelta(hours=1))

    def grupo(cid):
        c = contas[cid]
        if c["falha"] >= uma_hora:
            return 9  # falhou no Gemini recente -> excluir
        if cid not in opus:
            # sem opus: prioridade maxima pro gemini
            if c["ok"] and c["ok"] > c["falha"]:
                return 1
            return 2
        else:
            # com opus: so como rede de seguranca
            if c["ok"] and c["ok"] > c["falha"]:
                return 5
            return 6

    def chave(k):
        g = grupo(k)
        recente = datetime.fromisoformat(
            contas[k]["ok"].replace("Z", "+00:00")).timestamp() if contas[k]["ok"] else 0
        return g, -recente, contas[k]["prio"]

    ordem = sorted(contas, key=chave)
    ordem = [k for k in ordem if grupo(k) < 9][:MAX_GRATIS]
    return pro, ordem, contas, grupo


def api(metodo, caminho, corpo=None, cookie=None):
    req = urllib.request.Request(
        BASE + caminho, method=metodo,
        data=json.dumps(corpo).encode() if corpo is not None else None,
        headers={"Content-Type": "application/json", "Origin": BASE,
                 **({"Cookie": cookie} if cookie else {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.headers.get("Set-Cookie"), json.loads(r.read() or b"{}")


def main():
    pro, ordem, contas, grupo = fila()
    passos = [{"kind": "model", "model": MODELO_PRO, "providerId": "agy",
               "connectionId": c} for c in pro]
    passos += [{"kind": "model", "model": MODELO_GRATIS, "providerId": "antigravity",
                "connectionId": c} for c in ordem]
    sem_opus = sum(1 for c in ordem if grupo(c) <= 2)
    com_opus = sum(1 for c in ordem if grupo(c) >= 5)
    resumo = "pro=%d so_gem=%d backup=%d | %s" % (
        len(pro), sem_opus, com_opus,
        ", ".join("%s(%d)" % (contas[c]["name"].split("@")[0], grupo(c))
                  for c in ordem[:8]))
    if "--simular" in sys.argv:
        print(resumo)
        return
    senha = subprocess.run(["docker", "exec", "omniroute", "printenv", "INITIAL_PASSWORD"],
                           capture_output=True, text=True).stdout.strip()
    ck, _ = api("POST", "/api/auth/login", {"password": senha})
    cookie = ck.split(";")[0]
    _, lista = api("GET", "/api/combos", cookie=cookie)
    atual = next((c for c in lista.get("combos", []) if c["name"] == COMBO), None)
    if atual is None:
        api("POST", "/api/combos", {"name": COMBO, "strategy": "priority", "models": passos},
            cookie)
        mudou = "criado"
    else:
        antes = [(m.get("model"), m.get("connectionId")) for m in atual.get("models", [])]
        if antes == [(p["model"], p["connectionId"]) for p in passos]:
            return
        api("PUT", "/api/combos/" + atual["id"], {"models": passos}, cookie)
        mudou = "mudou"
    with open(LOG, "a") as f:
        f.write(f"{datetime.now():%Y-%m-%dT%H:%M:%S} {mudou} {resumo}\n")


if __name__ == "__main__":
    main()
