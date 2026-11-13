#!/usr/bin/env python3
"""Roda NA VPS 157 (cópia em /opt/omniroute/ordenar_contas_cw.py, cron 2 min). Ordena a prioridade das 18 contas
claude-web para o Sonnet web, do mesmo jeito que o ordenar_contas_opus faz com o Antigravity.

Pedido da dona (29/10/2026): "veja se ele está fazendo a rotação ou não está conectado em todas; se não, conserte a
rotação." Diagnóstico: ESTÁ conectado nas 18 e roda por prioridade (fill-first); o problema é que contas que só dão
403/429/502 ficavam na frente (ex.: conta_exemplo prio 1 = só 403) e o combo caía cedo no Claude Code (que esgotou).
Aqui as contas que respondem 200 vão para a frente e as que falham vão para o fim. Nada é desligado. --simular mostra.
"""
import json
import sqlite3
import sys
from datetime import datetime, timedelta, timezone

DB = "/opt/omniroute/data/storage.sqlite"
LOG = "/opt/omniroute/ordenar_contas_cw.log"


def iso(d):
    return d.strftime("%Y-%m-%dT%H:%M:%S")


def main():
    simular = "--simular" in sys.argv
    agora = datetime.now(timezone.utc)
    db = sqlite3.connect(DB, timeout=30)
    contas = {}
    for cid, nome, prio, rl in db.execute(
            "select id,name,priority,rate_limited_until from provider_connections "
            "where provider='claude-web' and is_active=1"):
        contas[cid] = {"nome": nome, "prio": prio or 999,
                       "limitada": bool(rl and rl[:19] > iso(agora))}
    ok, falha, ult = {}, {}, {}
    for cid, sucesso, status, ts in db.execute(
            "select connection_id,success,status,timestamp from usage_history "
            "where provider='claude-web' and timestamp>? order by timestamp", (iso(agora - timedelta(hours=24)),)):
        if cid not in contas:
            continue
        status = int(status or 0)
        ult[cid] = (ts, bool(sucesso), status)
        if sucesso and status == 200:
            ok[cid] = ts
        elif status in (401, 403, 429, 499, 502, 503, 504):
            falha[cid] = ts
    uma_hora = iso(agora - timedelta(hours=1))

    def grupo(cid):
        c = contas[cid]
        u = ult.get(cid)
        # sessão caiu (401/403) sem 200 depois, ou limitada agora -> fim da fila
        if (u and not u[1] and u[2] in (401, 403) and ok.get(cid, "") < u[0]) or c["limitada"]:
            return 3
        if cid in ok and falha.get(cid, "") < ok[cid]:
            return 0  # respondeu 200 e não falhou depois
        if cid not in falha or falha.get(cid, "") < uma_hora:
            return 1  # sem falha recente
        return 2      # falhou na última hora (429/502): atrás, mas antes das caídas

    def chave(cid):
        g = grupo(cid)
        recente = -datetime.fromisoformat(ok[cid][:19]).timestamp() if g == 0 else 0
        return (g, recente, contas[cid]["prio"], cid)

    ordem = sorted(contas, key=chave)
    mudancas = [(i + 1, cid) for i, cid in enumerate(ordem) if contas[cid]["prio"] != i + 1]
    resumo = {g: sum(1 for c in contas if grupo(c) == g) for g in range(4)}
    topo = ", ".join("%s(g%d)" % (contas[c]["nome"].replace("claude-web ", ""), grupo(c)) for c in ordem[:4])
    linha = "%s respondeu=%d ok=%d falha_recente=%d caidas=%d | topo: %s | mudou %d" % (
        iso(agora), resumo[0], resumo[1], resumo[2], resumo[3], topo, len(mudancas))
    if simular:
        print(linha)
        for i, cid in enumerate(ordem):
            print(" ", i + 1, "g%d" % grupo(cid), contas[cid]["nome"], "era", contas[cid]["prio"])
        return
    if mudancas:
        db.executemany("update provider_connections set priority=? where id=?", mudancas)
        db.commit()
        with open(LOG, "a") as fh:
            fh.write(linha + "\n")
    print(linha)


if __name__ == "__main__":
    main()
