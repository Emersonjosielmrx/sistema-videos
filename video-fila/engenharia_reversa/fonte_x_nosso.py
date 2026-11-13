"""As views do Short ORIGINAL do parceiro preveem as do nosso? (29/10) Cruza a fonte de cada Short nosso (postar.json)
com as views dela na lista guardada do Cortes (discover_canal) e com o lugar dela dentro do canal do parceiro."""
import json, statistics, sys
from collections import defaultdict
from pathlib import Path
if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dados_nossos import L  # noqa: E402
CACHE = Path(r"D:\recapd-ambientes\producao\workspace\cache\discover_canal")
fonte = {}
for f in CACHE.glob("*.json"):
    try:
        itens = [i for i in json.loads(f.read_text(encoding="utf-8")) if i.get("views")]
    except (OSError, ValueError):
        continue
    vs = sorted(i["views"] for i in itens)
    for i in itens:
        # percentil dentro do canal do parceiro (1.0 = o mais visto dele)
        fonte[i["id"]] = (i["views"], sum(v <= i["views"] for v in vs) / len(vs))
pares = []
for x in L:
    if not (x["fonte"] and x["projeto"].startswith("parceiro")):
        continue
    vid = x["fonte"].rstrip("/").split("/")[-1].split("?")[0]
    if vid in fonte:
        pares.append((fonte[vid][0], fonte[vid][1], x["v"]))
print(f"Shorts nossos com a fonte achada na lista: {len(pares)} de {sum(1 for x in L if x['projeto'].startswith('parceiro'))}")
for nome, idx, cortes in (("views da fonte", 0, [0, 100_000, 1_000_000, 5_000_000, 10**12]),
                          ("percentil da fonte no canal dela", 1, [0, .5, .8, .95, 1.01])):
    print(f"\npor {nome}: n | mediana nossa | % >=500")
    for a, b in zip(cortes, cortes[1:]):
        l = [p[2] for p in pares if a <= p[idx] < b]
        if l:
            print(f"  {a:>12,} a {b:<14,} {len(l):>3} | {statistics.median(l):>6.0f} | {sum(v >= 500 for v in l) / len(l):.0%}")
