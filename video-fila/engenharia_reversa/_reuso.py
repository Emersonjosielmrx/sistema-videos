import sys
from collections import defaultdict
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dados_nossos import L, led  # noqa: E402
import json
g = defaultdict(list)
for x in L:
    if x["fonte"]:
        r = led[x["vid"]]
        try:
            idi = json.loads((Path(r["caminho"]).parent / "postar.json").read_text(encoding="utf-8")).get("idioma")
        except Exception:
            idi = "?"
        g[x["fonte"]].append((r["ts"][:16], x["canal"], idi, x["v"]))
mesmo_canal = outra_lingua = 0
ordem = defaultdict(list)
for f, l in g.items():
    if len(l) < 2:
        continue
    l.sort()
    for i, t in enumerate(l):
        ordem[min(i, 2)].append(t[3])
    if len({t[1] for t in l}) < len(l): mesmo_canal += 1
    if len({t[2] for t in l}) > 1: outra_lingua += 1
print("fontes repetidas", sum(len(l) >= 2 for l in g.values()), "com repetição no MESMO canal", mesmo_canal, "em outra língua", outra_lingua)
import statistics
for k, v in sorted(ordem.items()):
    print(f"  {['1ª postagem','2ª','3ª+'][k]} n {len(v)} mediana {statistics.median(v)} >=500 {sum(a>=500 for a in v)}")
for f, l in sorted(g.items(), key=lambda kv: -len(kv[1]))[:5]:
    print(f); [print("   ", t) for t in l]
print("\n== só pt ==")
rep = {f for f, l in g.items() if len(l) >= 2}
for nome, c in (("fonte única", lambda f: f not in rep), ("fonte repetida (outra língua)", lambda f: f in rep)):
    v = [t[3] for f, l in g.items() if c(f) for t in l if t[2] == "pt"]
    print(f"  {nome}: n {len(v)} mediana {statistics.median(v)} >=500 {sum(a>=500 for a in v)/len(v):.0%}")
