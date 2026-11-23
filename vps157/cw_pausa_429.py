#!/usr/bin/env python3
"""Roda NA VPS 157 (cron 1 min). Pausa as contas claude-web (Sonnet web) que deram 429 "Rate limited".

23/11 (dona: "resolva e deixe funcionando o melhor que der"): o gateway so pausa a conta 60 s na memoria e a regra
de 10 min (providerErrorRules) nao era aplicada; com 45 contas cada pedido do chat varria todas em 0,3 s cada
(46 mil tentativas/dia, 2% de sucesso). Medido 23/11: depois do 429 a conta volta em mediana 2,4 h (p25 1 min).
Aqui: 429 sem 200 depois -> rate_limited_until = ultimo 429 + escada (20 min, 1 h, 3 h conforme os 429 seguidos
desde o ultimo 200). 200 depois do 429 -> tira a pausa. So mexe em claude-web e so em rate_limited_until.
Nunca pausa todas: deixa sempre as 2 que renovam primeiro sem pausa (o chat precisa de alguem para tentar).
--simular mostra sem gravar. CW_PAUSA=0 em /opt/omniroute/cw_pausa.desligar desliga (arquivo existe = nao faz nada).
"""
import os
import sqlite3
import sys
from datetime import datetime, timedelta, timezone

DB = "/opt/omniroute/data/storage.sqlite"
LOG = "/opt/omniroute/cw_pausa_429.log"
DESLIGAR = "/opt/omniroute/cw_pausa.desligar"
ESCADA = [(1, 20), (3, 60), (10 ** 9, 180)]  # (ate N 429 seguidos, minutos de pausa)
LIVRES_MIN = 2


def iso(d):
    return d.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def main():
    if os.path.exists(DESLIGAR):
        return
    simular = "--simular" in sys.argv
    agora = datetime.now(timezone.utc)
    db = sqlite3.connect(DB, timeout=30)
    db.execute("PRAGMA busy_timeout=30000")
    contas = {cid: (nome, rl) for cid, nome, rl in db.execute(
        "SELECT id, name, rate_limited_until FROM provider_connections WHERE provider='claude-web' AND is_active=1")}
    desde = (agora - timedelta(hours=12)).strftime("%Y-%m-%dT%H:%M:%S")
    seguidos, ult429, ult200 = {}, {}, {}
    for cid, st, ts in db.execute("SELECT connection_id, status, timestamp FROM usage_history WHERE provider='claude-web' "
                                  "AND timestamp>? AND status IN ('200','429') ORDER BY timestamp", (desde,)):
        if cid not in contas:
            continue
        if st == "200":
            ult200[cid] = ts
            seguidos[cid] = 0
        else:
            ult429[cid] = ts
            seguidos[cid] = seguidos.get(cid, 0) + 1
    quero = {}
    for cid in contas:
        if cid in ult429 and ult429[cid] > ult200.get(cid, ""):
            n = seguidos[cid]
            mins = next(m for lim, m in ESCADA if n <= lim)
            fim = datetime.fromisoformat(ult429[cid][:19]).replace(tzinfo=timezone.utc) + timedelta(minutes=mins)
            if fim > agora:
                quero[cid] = iso(fim)
    # nunca todas pausadas: as que voltam primeiro ficam livres
    livres = len(contas) - len(quero)
    if livres < LIVRES_MIN:
        for cid in sorted(quero, key=lambda x: quero[x])[:LIVRES_MIN - livres]:
            quero.pop(cid)
    mudar = []
    for cid, (nome, rl) in contas.items():
        novo = quero.get(cid)
        atual = rl if rl and rl[:19] > agora.strftime("%Y-%m-%dT%H:%M:%S") else None
        if novo and (not atual or atual[:19] < novo[:19]):
            mudar.append((novo, cid))
        elif not novo and atual and cid in ult200 and ult200[cid] > (ult429.get(cid) or ""):
            mudar.append((None, cid))  # respondeu 200 depois: tira a pausa nossa
    linha = (f"{agora:%Y-%m-%dT%H:%M} contas={len(contas)} pausadas={len(quero)} livres={len(contas) - len(quero)} "
             f"mudou={len(mudar)}")
    if simular:
        print(linha)
        for v, cid in mudar[:10]:
            print("  ", contas[cid][0], "->", v)
        return
    if mudar:
        db.executemany("UPDATE provider_connections SET rate_limited_until=? WHERE id=? AND provider='claude-web'", mudar)
        db.commit()
        with open(LOG, "a") as f:
            f.write(linha + "\n")


if __name__ == "__main__":
    main()
