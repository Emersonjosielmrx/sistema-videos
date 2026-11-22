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
    # 17/11 (dona): Gemini 4 Hydrogen (Ultra/Pro) no seletor; o nome nao e cortado, o apelido fica igual a ele
    "ag-hydrogen": ("gemini-4-hydrogen-sonar", "gemini-4-hydrogen-sonar"),
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
    return fila(c, modelo, ids)


def fila(c, modelo, ids):
    """06/11: ordem de fila (como a do 4.6): quem respondeu por ultimo 1o; 429 recente (3 h) fora."""
    import datetime
    agora = datetime.datetime.now(datetime.timezone.utc)
    desde = (agora - datetime.timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S")
    recente = (agora - datetime.timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M:%S")
    ult = {}
    for cid, st, ts in c.execute("SELECT connection_id, status, timestamp FROM usage_history WHERE provider='antigravity' "
                                 "AND model=? AND timestamp>? AND status IN ('200','429') ORDER BY timestamp",
                                 (modelo, desde)):
        ult[cid] = (st, ts)
    # medicao de cota (quota_snapshots): janela do modelo ou semanal esgotada com reset no futuro = sem cota ate la
    agora_s = agora.strftime("%Y-%m-%dT%H:%M:%S")
    volta = {}
    for cid, wk, ex, nr in c.execute("SELECT connection_id, window_key, is_exhausted, next_reset_at FROM quota_snapshots "
                                     "WHERE id IN (SELECT max(id) FROM quota_snapshots WHERE provider='antigravity' "
                                     "AND window_key IN (?, 'claude_gpt_weekly', 'gpt-oss-120b-medium') GROUP BY connection_id, window_key)", (modelo,)):
        if ex and nr and nr[:19] > agora_s:
            volta[cid] = max(volta.get(cid, ""), nr)
    esgotadas = sorted([x for x in ids if x in volta], key=lambda x: volta[x])  # a que renova primeiro 1o
    ids = [x for x in ids if x not in volta]
    vivas = sorted([x for x in ids if ult.get(x, ("",))[0] == "200"], key=lambda x: ult[x][1], reverse=True)
    novas = [x for x in ids if x not in ult]
    velhas = sorted([x for x in ids if ult.get(x, ("",))[0] == "429" and ult[x][1][:19] <= recente], key=lambda x: ult[x][1])
    quero = vivas + novas + velhas
    if not quero:  # nunca deixa o combo vazio: as de 429 recente, a mais antiga primeiro
        quero = sorted(ids, key=lambda x: ult.get(x, ("", ""))[1])
    if not quero:  # todas esgotadas pela medicao: so a que renova primeiro (falha rapido, sem varrer todas)
        quero = esgotadas[:1]
    return quero


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


def opus_auto(c):
    """06/11 (dona): opus-auto = [cc pago] + contas da fila do Opus 5.5 Antigravity (passos diretos, sem combo aninhado)."""
    linha = c.execute("SELECT id, data FROM combos WHERE name='opus-auto'").fetchone()
    if not linha:
        return
    cid, dados = linha[0], json.loads(linha[1])
    cc = next((m for m in dados.get("models", []) if str(m.get("model", "")).startswith("cc/")),
              {"kind": "model", "model": "cc/claude-opus-5-5", "providerId": "cc"})
    cc = {k: cc[k] for k in ("kind", "model", "providerId") if k in cc}
    ag = [{"kind": "model", "model": "antigravity/claude-opus-5-5-high", "providerId": "antigravity",
           "connectionId": x, "weight": 0} for x in contas_com(c, "claude-opus-5-5-high")]
    # 12/11 (dona): Opus 4.6 Antigravity como ULTIMO do pago, so quando cc e 5.5 derem erro.
    # Usa as contas do opus46-direto (combo_opus_fila: so vivas/429 rapida, nunca a que trava 160 s).
    l46 = c.execute("SELECT data FROM combos WHERE name='opus46-direto'").fetchone()
    ag46 = [{"kind": "model", "model": "antigravity/claude-opus-4-6-thinking", "providerId": "antigravity",
             "connectionId": m["connectionId"], "weight": 0}
            for m in (json.loads(l46[0]).get("models", []) if l46 else []) if m.get("connectionId")]
    novos = [cc] + ag + ag46
    if [(m.get("model"), m.get("connectionId")) for m in dados.get("models", [])] == \
       [(m.get("model"), m.get("connectionId")) for m in novos]:
        return
    log(f"opus-auto: cc + {len(ag)} conta(s) do Opus 5.5 Antigravity + {len(ag46)} do 4.6 no fim")
    if SIMULAR:
        return
    token = login()
    req = urllib.request.Request(f"{BASE}/api/combos/{cid}", data=json.dumps({"models": novos}).encode(),
                                 headers={"Content-Type": "application/json", "Cookie": f"auth_token={token}"},
                                 method="PUT")
    log(f"opus-auto: PUT {urllib.request.urlopen(req, timeout=30).status}")


SONNET_WEB = {"kind": "model", "model": "cw/claude-sonnet-5-5", "providerId": "claude-web", "weight": 0}


def opus_sonnetweb(c):
    """22/11 (dona): "Opus pago + Sonnet web" = mesma fila do opus-auto e, quando todos os Opus falham,
    o Sonnet 5.5 web (contas claude-web, limite separado). So o cw/, nunca o claude/ (gasta a conta cc)."""
    base = c.execute("SELECT data FROM combos WHERE name='opus-auto'").fetchone()
    if not base:
        return
    passos = [{k: m[k] for k in ("kind", "model", "providerId", "connectionId", "weight") if k in m}
              for m in json.loads(base[0]).get("models", [])]
    novos = passos + [SONNET_WEB]
    linha = c.execute("SELECT id, data FROM combos WHERE name='opus-pago-sonnetweb'").fetchone()
    if linha and [(m.get("model"), m.get("connectionId")) for m in json.loads(linha[1]).get("models", [])] == \
            [(m.get("model"), m.get("connectionId")) for m in novos]:
        return
    log(f"opus-pago-sonnetweb: {len(passos)} passo(s) do opus-auto + Sonnet web no fim")
    if SIMULAR:
        return
    token = login()
    if linha:
        rota, metodo, corpo = f"/api/combos/{linha[0]}", "PUT", {"models": novos}
    else:
        rota, metodo, corpo = "/api/combos", "POST", {"name": "opus-pago-sonnetweb", "strategy": "priority",
                                                      "models": novos}
    req = urllib.request.Request(BASE + rota, data=json.dumps(corpo).encode(),
                                 headers={"Content-Type": "application/json", "Cookie": f"auth_token={token}"},
                                 method=metodo)
    log(f"opus-pago-sonnetweb: {metodo} {urllib.request.urlopen(req, timeout=30).status}")


if __name__ == "__main__":
    con = sqlite3.connect(DB, timeout=30)
    apelidos(con)
    combos(con)
    opus_auto(con)
    opus_sonnetweb(con)
