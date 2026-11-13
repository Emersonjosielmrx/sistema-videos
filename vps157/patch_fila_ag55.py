#!/usr/bin/env python3
# 06/11/2026 (dona): "fila do Opus 5.5" igual a do 4.6. O ag55_guarda.py punha no combo TODAS as contas que tem o
# 5.5 (inclusive as sem cota) -> cada pedido batia em 4-5 contas com 429 (~20 s cada) antes da que responde.
# Agora a ordem do combo ag-opus-5-5 / ag-sonnet-5-5 e:
#   1) contas cujo ULTIMO resultado no modelo (7 dias) foi 200, a mais recente primeiro (a que esta respondendo);
#   2) contas que tem o 5.5 e nunca foram tentadas / sem resultado recente;
#   3) contas cujo ultimo resultado foi 429 HA MAIS de 3 h (podem ter renovado), no fim;
#   contas com 429 nas ultimas 3 h ficam FORA (a nao ser que nao sobre nenhuma).
# Continua so lendo o banco e a API LOCAL do OmniRoute (nao fala com o Google).
p = '/opt/omniroute/ag55_guarda.py'
s = open(p).read()

old = '''def contas_com(c, modelo):
    ids = []
    for (cid,) in c.execute("SELECT id FROM provider_connections WHERE provider='antigravity' AND is_active=1 ORDER BY priority"):
        v = c.execute("SELECT value FROM key_value WHERE namespace='syncedAvailableModels' AND key=?", (f"antigravity:{cid}",)).fetchone()
        if v and any(m.get("id") == modelo for m in json.loads(v[0])):
            ids.append(cid)
    return ids
'''
new = '''def contas_com(c, modelo):
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
    vivas = sorted([x for x in ids if ult.get(x, ("",))[0] == "200"], key=lambda x: ult[x][1], reverse=True)
    novas = [x for x in ids if x not in ult]
    velhas = sorted([x for x in ids if ult.get(x, ("",))[0] == "429" and ult[x][1][:19] <= recente], key=lambda x: ult[x][1])
    quero = vivas + novas + velhas
    if not quero:  # nunca deixa o combo vazio: as de 429 recente, a mais antiga primeiro
        quero = sorted(ids, key=lambda x: ult.get(x, ("", ""))[1])
    return quero
'''
assert s.count(old) == 1, 'contas_com mudou'
s = s.replace(old, new, 1)

# mesma lista tambem direto no opus-auto (sem combo dentro de combo: o OmniRoute pulava o passo "ag-opus-5-5"
# com "all targets were skipped by pre-dispatch filters")
old_main = '''if __name__ == "__main__":
    con = sqlite3.connect(DB, timeout=30)
    apelidos(con)
    combos(con)'''
new_main = '''def opus_auto(c):
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
    novos = [cc] + ag
    if [(m.get("model"), m.get("connectionId")) for m in dados.get("models", [])] == \\
       [(m.get("model"), m.get("connectionId")) for m in novos]:
        return
    log(f"opus-auto: cc + {len(ag)} conta(s) do Opus 5.5 Antigravity")
    if SIMULAR:
        return
    token = login()
    req = urllib.request.Request(f"{BASE}/api/combos/{cid}", data=json.dumps({"models": novos}).encode(),
                                 headers={"Content-Type": "application/json", "Cookie": f"auth_token={token}"},
                                 method="PUT")
    log(f"opus-auto: PUT {urllib.request.urlopen(req, timeout=30).status}")


if __name__ == "__main__":
    con = sqlite3.connect(DB, timeout=30)
    apelidos(con)
    combos(con)
    opus_auto(con)'''
assert s.count(old_main) == 1, 'main mudou'
s = s.replace(old_main, new_main, 1)
open(p, 'w').write(s)
print('ok')
