#!/usr/bin/env python3
"""Teste da regra nova do painel, sem rodar o painel: no momento T, o que o painel mostraria para a paulocarva.
Repete a logica de painel_creditos.dados_json (foto mais recente ate T; ultimo 200 ate T)."""
import datetime
import sqlite3
import sys

T = sys.argv[1] if len(sys.argv) > 1 else "2026-11-23T05:00:00"
db = sqlite3.connect("file:/opt/omniroute/data/storage.sqlite?mode=ro", uri=True, timeout=30)
dt = lambda s: datetime.datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None
cid = db.execute("SELECT id FROM provider_connections WHERE provider='claude' AND email LIKE 'paulocarva%'").fetchone()[0]
ws = db.execute("""SELECT window_key, remaining_percentage, is_exhausted, next_reset_at, created_at FROM quota_snapshots
                   WHERE id IN (SELECT max(id) FROM quota_snapshots WHERE connection_id=? AND created_at<=? GROUP BY window_key)""",
                (cid, T)).fetchall()
agora = dt(T + "Z")
esg = [(w, dt(nr), dt(cri)) for w, rem, ex, nr, cri in ws if (rem or 0) <= 0 and nr and dt(nr) > agora - datetime.timedelta(days=8)]
quando = max(dt(cri) for *_, cri in ws)
print("momento", T, "| fotos:", [(w, rem, str(nr)[5:16], str(cri)[5:16]) for w, rem, ex, nr, cri in ws])
ult_ok = db.execute("SELECT max(timestamp) FROM usage_history WHERE connection_id=? AND status='200' AND timestamp>? AND timestamp<=?",
                    (cid, (agora - datetime.timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S"), T)).fetchone()[0]
if not esg:
    print("painel: conta com credito (nao estava esgotada)")
    raise SystemExit
libera = max(r for _, r, _ in esg)
print("painel ANTIGO: esgotada, volta", libera.strftime("%m-%d %H:%M"), "UTC")
if libera <= agora:
    if dt(ult_ok) and dt(ult_ok) >= libera:
        print("painel NOVO: VOLTOU", ult_ok[5:16], "UTC (respondeu depois da hora prevista)")
    elif quando < libera:
        print("painel NOVO: 'devia ter voltado", libera.strftime("%m-%d %H:%M"), "· leitura velha' (ultima leitura",
              quando.strftime("%m-%d %H:%M"), ")")
    else:
        print("painel NOVO: igual ao antigo (leitura nova ainda diz esgotada)")
else:
    print("painel NOVO: igual ao antigo (hora prevista ainda nao chegou)")
