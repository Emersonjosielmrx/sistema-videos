#!/usr/bin/env python3
"""Roda NA VPS 157 (/opt/omniroute/sonnet_oi.py), timer systemd sonnet-oi a cada 1 min. Cópia em D:\\sonnet web.
Regra da dona (igual ao Argon): conta do claude-web que bate no limite fica marcada com a hora da volta; quando essa
hora passa, recebe um "oi" SÓ NELA (cabeçalho x-omniroute-connection). Respondeu pela própria conta = voltou (hora
gravada). Deu 429 de novo = o OmniRoute põe outro limite e ela entra na espera outra vez.
Estado: /opt/omniroute/sonnet_oi.json  |  log: /opt/omniroute/sonnet_oi.log  |  --status só imprime."""
import json
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

DB = "/opt/omniroute/data/storage.sqlite"
ESTADO = "/opt/omniroute/sonnet_oi.json"
LOG = "/opt/omniroute/sonnet_oi.log"
URL = "http://127.0.0.1:20128/v1/chat/completions"
RUINS = ("expired", "error", "invalid")
MAX_POR_RODADA = 8
ESPERA_FALHA = timedelta(minutes=10)


def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} {msg}\n")


def data(iso):
    try:
        return datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
    except ValueError:
        return None


def iso(x):
    """ISO com fuso. Os 'voltou_em' antigos (antes de 30/10) eram hora local da VPS sem fuso."""
    d = data(x)
    if d is None:
        return str(x)
    if d.tzinfo is None:
        d = d.astimezone()  # sem fuso = hora local desta máquina
    return d.isoformat(timespec="minutes")


def ler():
    try:
        with open(ESTADO, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def gravar(st):
    with open(ESTADO + ".tmp", "w", encoding="utf-8") as f:
        json.dump(st, f, indent=1, ensure_ascii=False)
    import os
    os.replace(ESTADO + ".tmp", ESTADO)


def oi(chave, conn_id):
    """(ok, detalhe). ok só se respondeu 200 pela conta pedida."""
    corpo = json.dumps({"model": "cw/claude-sonnet-5-5", "stream": False,
                        "messages": [{"role": "user", "content": "responda so: oi"}]}).encode()
    req = urllib.request.Request(URL, data=corpo, headers={
        "Authorization": f"Bearer {chave}", "Content-Type": "application/json", "x-omniroute-connection": conn_id})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            usada = r.headers.get("x-omniroute-selected-connection-id")
            txt = r.read().decode("utf-8", "replace")
        if usada != conn_id:
            return False, f"atendida por outra conta ({usada})"
        if '"chatcmpl-' not in txt:
            return False, "resposta sem chatcmpl: " + txt[:100]
        return True, "ok"
    except urllib.error.HTTPError as e:
        usada = e.headers.get("x-omniroute-selected-connection-id")
        outra = f" (atendida por outra conta {usada})" if usada and usada != conn_id else ""
        return False, f"HTTP {e.code}{outra}: {e.read().decode('utf-8', 'replace')[:100]}"
    except Exception as e:  # noqa: BLE001
        return False, str(e)[:100]


def main(a):
    db = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    contas = db.execute("SELECT id, name, rate_limited_until, test_status FROM provider_connections "
                        "WHERE provider='claude-web' AND is_active=1").fetchall()
    chave = db.execute("SELECT key FROM api_keys WHERE revoked_at IS NULL AND is_active=1 LIMIT 1").fetchone()[0]
    db.close()
    agora = datetime.now(timezone.utc)
    st = ler()
    ativos = {cid for cid, *_ in contas}
    for cid in [k for k in st if k not in ativos]:  # conta apagada/desligada no painel: não fica "esperando" pra sempre
        del st[cid]
    if "--status" in a:
        # 30/10: horas SEMPRE com fuso (a VPS é CET e o PC1 é -03; antes o Telegram mostrava a hora da VPS)
        esperando = sorted((iso(c["volta"]), c["nome"]) for c in st.values() if c.get("volta") and not c.get("confirmado"))
        print(json.dumps({"agora": agora.isoformat(timespec="seconds"), "esperando_oi": esperando, "ultimas_voltas": sorted(
            ((iso(c["voltou_em"]), c["nome"]) for c in st.values() if c.get("voltou_em")), reverse=True)[:10]},
            ensure_ascii=False, indent=1))
        return
    feitos = 0
    for cid, nome, ate, status in contas:
        nome = nome.replace("claude-web ", "")
        c = st.setdefault(cid, {"nome": nome})
        c["nome"] = nome
        volta = data(ate) if ate else None
        if not volta and c.get("volta") and not c.get("confirmado"):
            # 30/10: o gateway limpou o limite sozinho (pedido real deu certo) antes do oi: sai da espera, sem contar
            # como "volta confirmada" (a regra é aviso só com prova do oi). Antes ficava "esperando oi" pra sempre.
            c.update(confirmado=True, liberada_em=datetime.now(timezone.utc).isoformat(timespec="minutes"))
            log(f"{nome}: limite limpo pelo gateway antes do oi (sai da espera)")
            continue
        if not volta or (status or "") in RUINS:
            continue
        if c.get("volta") != ate:  # limite novo: agenda o oi pra hora da volta
            c.update(volta=ate, confirmado=False, tentativas=0)
            c.pop("proximo_oi", None)
            if volta > agora:
                log(f"{nome}: no limite, oi agendado pra {volta.astimezone():%H:%M}")
        if c.get("confirmado") or volta > agora or feitos >= MAX_POR_RODADA:
            continue
        if c.get("proximo_oi") and data(c["proximo_oi"]) > agora:
            continue
        feitos += 1
        t = time.time()
        ok, det = oi(chave, cid)
        c["tentativas"] = c.get("tentativas", 0) + 1
        if ok:
            c.update(confirmado=True, voltou_em=datetime.now(timezone.utc).isoformat(timespec="minutes"))
            c.setdefault("historico", []).append({"limite_ate": ate, "voltou_em": c["voltou_em"]})
            c["historico"] = c["historico"][-10:]
            log(f"{nome}: VOLTOU (oi respondido em {time.time() - t:.0f} s; limite era até {volta.astimezone():%H:%M})")
        else:
            c["proximo_oi"] = (agora + ESPERA_FALHA).isoformat()
            log(f"{nome}: oi falhou ({det}); tenta de novo em 10 min ou no próximo limite")
        gravar(st)
    gravar(st)


if __name__ == "__main__":
    main(sys.argv[1:])
