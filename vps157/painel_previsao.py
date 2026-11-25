#!/usr/bin/env python3
"""So leitura: compara a "volta" que o painel mostra com quando a conta cc voltou a responder de verdade."""
import datetime
import sqlite3

db = sqlite3.connect("file:/opt/omniroute/data/storage.sqlite?mode=ro", uri=True, timeout=30)
agora = datetime.datetime.now(datetime.timezone.utc)
dt = lambda s: datetime.datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None

print("== ultima foto de cada conta cc ativa: janela | resta% | esgotada | reset | foto tirada ha ==")
contas = db.execute("SELECT id, coalesce(email,name) FROM provider_connections WHERE provider='claude' AND is_active=1").fetchall()
for cid, nome in contas:
    ws = db.execute("""SELECT window_key, remaining_percentage, is_exhausted, next_reset_at, created_at FROM quota_snapshots
                       WHERE id IN (SELECT max(id) FROM quota_snapshots WHERE provider='claude' AND connection_id=?
                       GROUP BY window_key)""", (cid,)).fetchall()
    ult = db.execute("SELECT status, timestamp FROM usage_history WHERE connection_id=? ORDER BY timestamp DESC LIMIT 1",
                     (cid,)).fetchone()
    print(f"-- {str(nome).split('@')[0][:10]}  ultimo pedido: {ult}")
    for w, rem, ex, nr, cri in ws:
        idade = (agora - dt(cri)).total_seconds() / 60 if cri else None
        print(f"   {w:14} {rem!s:>6} ex={ex} reset={str(nr)[:16]} foto ha {idade:.0f} min" if idade is not None else f"   {w} sem foto")

print("\n== 3 dias: quando a conta passou de 'esgotada' para responder 200 (a volta REAL) x o reset que a foto dizia ==")
for cid, nome in contas:
    fotos = db.execute("""SELECT created_at, window_key, is_exhausted, next_reset_at FROM quota_snapshots WHERE provider='claude'
                          AND connection_id=? AND created_at > strftime('%Y-%m-%dT%H:%M:%S','now','-3 days')
                          AND is_exhausted=1 ORDER BY created_at""", (cid,)).fetchall()
    if not fotos:
        continue
    vistos = set()
    for cri, w, ex, nr in fotos:
        chave = (w, str(nr)[:13])
        if chave in vistos:
            continue
        vistos.add(chave)
        ok = db.execute("SELECT min(timestamp) FROM usage_history WHERE connection_id=? AND status='200' AND timestamp>?",
                        (cid, cri)).fetchone()[0]
        if ok and nr:
            dif = (dt(ok) - dt(nr)).total_seconds() / 60
            print(f"   {str(nome).split('@')[0][:10]} {w:12} esgotou {cri[5:16]} reset dito {str(nr)[5:16]} "
                  f"voltou de verdade {ok[5:16]} ({dif:+.0f} min)")

print("\n== frequencia das fotos de cota cc (ultimas 3 h): por conta, intervalo medio entre fotos ==")
for cid, nome in contas:
    ts = [dt(r[0]) for r in db.execute("""SELECT DISTINCT substr(created_at,1,16) FROM quota_snapshots WHERE provider='claude'
                                            AND connection_id=? AND created_at > strftime('%Y-%m-%dT%H:%M:%S','now','-3 hours')
                                            ORDER BY 1""", (cid,))]
    if len(ts) > 1:
        gap = sum((b - a).total_seconds() for a, b in zip(ts, ts[1:])) / (len(ts) - 1) / 60
        print(f"   {str(nome).split('@')[0][:10]}: {len(ts)} fotos, a cada {gap:.0f} min")
    else:
        print(f"   {str(nome).split('@')[0][:10]}: {len(ts)} foto(s) em 3 h")
