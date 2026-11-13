"""Alcance por PROJETO (29/10): views de 48-120 h de todos os uploads do ledger, separados por projeto/tipo,
com faixas (bimodal?), hora de publicação e reuso da mesma fonte. Grava resultado em alcance_projetos.json."""
import json, statistics, sys
from collections import defaultdict, Counter
from pathlib import Path
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from dados_nossos import L  # noqa: E402  (30/10: a carga dos dados saiu daqui; os outros scripts importam de lá)
FX = [(0, 0), (1, 9), (10, 99), (100, 499), (500, 1999), (2000, 10**9)]
out = {"n": len(L), "projetos": {}}
print("faixas = 0 | 1-9 | 10-99 | 100-499 | 500-1999 | 2000+")
g = defaultdict(list)
for x in L:
    g[x["projeto"]].append(x)
for p, xs in sorted(g.items(), key=lambda kv: -len(kv[1])):
    vs = [x["v"] for x in xs]
    fx = [sum(a <= v <= b for v in vs) for a, b in FX]
    hrs = defaultdict(list)
    for x in xs:
        if x["hora"] is not None:
            hrs[x["hora"]].append(x["v"])
    boas = sorted(((h, sum(v >= 500 for v in l) / len(l), len(l)) for h, l in hrs.items() if len(l) >= 5), key=lambda t: -t[1])
    cnt = Counter(x["fonte"] for x in xs if x["fonte"])
    um = [x["v"] for x in xs if x["fonte"] and cnt[x["fonte"]] == 1]
    rep = [x["v"] for x in xs if x["fonte"] and cnt[x["fonte"]] >= 2]
    d = dict(n=len(vs), mediana=statistics.median(vs), media=round(statistics.mean(vs)), faixas=fx,
             pct500=round(sum(v >= 500 for v in vs) / len(vs), 2),
             horas_top=[(h, round(p_, 2), n) for h, p_, n in boas[:3]], horas_piores=[(h, round(p_, 2), n) for h, p_, n in boas[-3:]],
             fonte_unica=(len(um), statistics.median(um) if um else None),
             fonte_repetida=(len(rep), statistics.median(rep) if rep else None))
    out["projetos"][p] = d
    print(f"\n{p}: n {d['n']} | mediana {d['mediana']:.0f} | média {d['media']} | >=500 {d['pct500']:.0%} | faixas {fx}")
    print(f"   horas boas {d['horas_top']}  piores {d['horas_piores']}")
    if rep:
        print(f"   fonte única n {len(um)} med {d['fonte_unica'][1]} | repetida n {len(rep)} med {d['fonte_repetida'][1]}")
(AQUI / "alcance_projetos.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
