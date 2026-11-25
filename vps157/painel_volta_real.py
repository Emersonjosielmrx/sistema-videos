#!/usr/bin/env python3
"""So leitura: para cada vez que uma conta cc ficou esgotada (foto is_exhausted=1), compara o reset que a foto
dizia com a primeira foto NOVA mostrando credito (>0%) e com o primeiro 200 depois de 2 min do esgotamento."""
import datetime
import sqlite3

db = sqlite3.connect("file:/opt/omniroute/data/storage.sqlite?mode=ro", uri=True, timeout=30)
dt = lambda s: datetime.datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None
contas = db.execute("SELECT id, coalesce(email,name) FROM provider_connections WHERE provider='claude' AND is_active=1").fetchall()
cedo = tarde = certo = 0
for cid, nome in contas:
    fotos = db.execute("""SELECT created_at, window_key, remaining_percentage, is_exhausted, next_reset_at FROM quota_snapshots
                          WHERE provider='claude' AND connection_id=? AND created_at > strftime('%Y-%m-%dT%H:%M:%S','now','-2 days')
                          ORDER BY created_at""", (cid,)).fetchall()
    for w in ("session (5h)", "weekly (7d)"):
        fw = [f for f in fotos if f[1] == w]
        i = 0
        while i < len(fw):
            if fw[i][3] == 1 and (i == 0 or fw[i - 1][3] == 0):
                esg, reset = dt(fw[i][0]), dt(fw[i][4])
                j = next((k for k in range(i + 1, len(fw)) if fw[k][3] == 0 and (fw[k][2] or 0) > 0), None)
                volta_foto = dt(fw[j][0]) if j is not None else None
                ok = db.execute("SELECT min(timestamp) FROM usage_history WHERE connection_id=? AND status='200' AND timestamp>?",
                                (cid, (esg + datetime.timedelta(minutes=2)).strftime("%Y-%m-%dT%H:%M:%S"))).fetchone()[0]
                ok = dt(ok)
                if reset and volta_foto:
                    d = (volta_foto - reset).total_seconds() / 60
                    d200 = (ok - reset).total_seconds() / 60 if ok else None
                    if d < -10: cedo += 1
                    elif d > 30: tarde += 1
                    else: certo += 1
                    if d < -10 or d > 30:
                        print(f"{str(nome).split('@')[0][:10]:10} {w:12} esgotou {esg:%m-%d %H:%M} reset dito {reset:%m-%d %H:%M} "
                              f"foto com credito {volta_foto:%m-%d %H:%M} ({d:+.0f} min) 1o 200 {ok:%m-%d %H:%M}" if ok else "")
                i = j or len(fw)
            i += 1
print(f"\nresumo 2 dias: volta na hora dita (-10..+30 min) = {certo} | voltou ANTES = {cedo} | voltou DEPOIS = {tarde}")
