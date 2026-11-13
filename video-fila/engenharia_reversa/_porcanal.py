import statistics, sys
from collections import defaultdict
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dados_nossos import L  # noqa: E402
for filtro in ("None", "hipercool", "manhwa"):
    g = defaultdict(list)
    for x in L:
        if x["projeto"].startswith(filtro):
            g[(x["projeto"], x["canal"])].append(x["v"])
    for c, l in sorted(g.items(), key=lambda kv: -len(kv[1])):
        print(c, len(l), statistics.median(l), max(l))
