"""Hora de publicação DENTRO do mesmo canal (29/10): para cada canal pt de parceiro, a taxa de >=500 por faixa de
hora (BR) menos a taxa do próprio canal. Soma os desvios: faixa boa de verdade fica positiva em vários canais."""
import statistics
import sys
from collections import defaultdict
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from dados_nossos import L  # noqa: E402
FAIXAS = {"madrugada 0-5": range(0, 6), "manhã 6-10": range(6, 11), "almoço 11-14": range(11, 15),
          "tarde 15-18": range(15, 19), "noite 19-21": range(19, 22), "noite 22-23": range(22, 24)}
por_canal = defaultdict(list)
for x in L:
    if x["projeto"].startswith("parceiro") and x["hora"] is not None:
        por_canal[x["canal"]].append(x)
desvio = defaultdict(list)
for c, xs in por_canal.items():
    if len(xs) < 6:
        continue
    base = sum(x["v"] >= 500 for x in xs) / len(xs)
    if base in (0, 1):
        continue  # canal que nunca/sempre pega não diz nada sobre hora
    for nome, hs in FAIXAS.items():
        l = [x for x in xs if x["hora"] in hs]
        if len(l) >= 2:
            desvio[nome].append((sum(x["v"] >= 500 for x in l) / len(l) - base, len(l), c))
print("faixa | canais | desvio médio da taxa >=500 vs o próprio canal | canais acima / abaixo")
for nome in FAIXAS:
    d = desvio.get(nome) or []
    if d:
        print(f"  {nome:<14} {len(d):>2} | {statistics.mean(t[0] for t in d):+.0%} | "
              f"{sum(t[0] > 0 for t in d)} / {sum(t[0] < 0 for t in d)}  (vídeos {sum(t[1] for t in d)})")
