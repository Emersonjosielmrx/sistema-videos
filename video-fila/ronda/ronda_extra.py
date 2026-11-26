# D:\video-fila\ronda_extra.py  (copia mestre: /mnt/win-bootcamp/claude-central/ronda/ronda_extra.py)
# Parte da RONDA GERAL que e mais facil em Python. Somente leitura. Chamado por ronda_geral.ps1 (secao 16).
# 1) VIEWS por canal: ganho das ultimas 24 h x das 24 h anteriores (estado\canais_views_hist.jsonl, coletado ~1x/h)
#    -> "!!" se caiu mais de 70% num canal que fazia >= 500 views/dia, ou se o historico parou de ser coletado.
# 2) KAGGLE (estado\balanco_kaggle.json): GPUs ativas, reserva, idade do balanco.
import json
import os
import sys
import time
from datetime import datetime, timedelta

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

EST = r"D:\video-fila\estado"
agora = datetime.now()

# ---------- 1) views ----------
hist = os.path.join(EST, "canais_views_hist.jsonl")
try:
    tam = os.path.getsize(hist)
    with open(hist, "rb") as fh:
        fh.seek(max(0, tam - 2_500_000))
        linhas = fh.read().decode("utf-8", "ignore").splitlines()[1:]
    serie = {}
    for l in linhas:
        try:
            j = json.loads(l)
            t = datetime.fromisoformat(j["ts"])
        except Exception:  # noqa: BLE001
            continue
        if j.get("views") is None:
            continue
        serie.setdefault(j["slug"], {"nome": j.get("nome", j["slug"]), "p": []})["p"].append((t, int(j["views"])))
    ult = max((p[-1][0] for s in serie.values() for p in [s["p"]]), default=None)
    idade_h = (agora - ult).total_seconds() / 3600 if ult else 999
    def valor_em(pts, quando):
        antes = [v for t, v in pts if t <= quando]
        return antes[-1] if antes else None
    caiu, subiu, n = [], [], 0
    for slug, s in serie.items():
        pts = sorted(s["p"])
        v0 = pts[-1][1]
        t0 = pts[-1][0]
        v24 = valor_em(pts, t0 - timedelta(hours=24))
        v48 = valor_em(pts, t0 - timedelta(hours=48))
        if v24 is None or v48 is None:
            continue
        g, gp = v0 - v24, v24 - v48
        n += 1
        if gp >= 500 and g < gp * 0.3:
            caiu.append(f"{s['nome']} {gp}->{g}")
        elif gp >= 200 and g > gp * 2:
            subiu.append(f"{s['nome']} {gp}->{g}")
    print(f"[VIEWS 24h x 24h antes] {n} canais medidos | coleta de {idade_h:.0f} h atras"
          + (f" | subiram: {', '.join(subiu[:6])}" if subiu else ""))
    for c in caiu[:10]:
        print(f"  !! VIEWS DESABARARAM: {c} (ganho do dia anterior -> ultimas 24 h)")
    if idade_h > 6:
        print(f"  !! historico de views parado ha {idade_h:.0f} h (estado\\canais_views_hist.jsonl)")
except OSError as e:
    print(f"  !! views: nao li {hist} ({e})")

# ---------- 2) kaggle ----------
bk = os.path.join(EST, "balanco_kaggle.json")
try:
    j = json.load(open(bk, encoding="utf-8-sig"))
    g = j.get("gpus", {})
    em = datetime.fromisoformat(j["em"])
    idade = (agora - em).total_seconds() / 3600
    sem_estoque = [c["canal"] for c in j.get("canais", []) if c.get("agendados", 0) == 0 and c.get("prontos", 0) == 0]
    print(f"[KAGGLE] GPUs curto {g.get('curto_ativas')}/{g.get('curto_total')} | longo {g.get('longo_ativas')}/{g.get('longo_total')}"
          f" | reserva na meta {j.get('reserva', {}).get('na_meta')}/{j.get('reserva', {}).get('total')}"
          f" | balanco de {idade:.1f} h atras | canais sem estoque: {len(sem_estoque)}")
    if (g.get("curto_ativas") or 0) + (g.get("longo_ativas") or 0) == 0:
        print("  !! NENHUMA GPU do Kaggle rodando")
    if idade > 3:
        print(f"  !! balanco do Kaggle parado ha {idade:.0f} h (tarefa BalancoKaggle)")
except (OSError, ValueError, KeyError) as e:
    print(f"  !! kaggle: nao li {bk} ({e})")
