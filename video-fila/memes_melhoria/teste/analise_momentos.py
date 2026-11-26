# -*- coding: utf-8 -*-
# PC1, so leitura: para cada frase, nota do melhor meme; compara o que o codigo escolhe (1o que casa apos o intervalo)
# com os momentos de MAIOR nota. Mostra contexto (frase anterior/seguinte) dos escolhidos.
import json, os, random, re, sys
from pathlib import Path
os.environ["ANIME_MEMES_SO_NOVOS"] = "1"
sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"D:\recapd-ambientes\producao\bin")
import memes_visuais as mv
mv._hist_cache = []
CACHE = Path(r"D:\recapd-ambientes\producao\workspace\roteiro_cache")
cat = [m for m in mv.catalogo() if m.get("has_audio")]

def nota(fr, k):
    t, ant = fr[k], fr[k-1] if k else ""
    if mv.triste(t) or mv.triste(ant): return 0, None
    emo, forca = mv.pede_meme(t, ant)
    if not forca: return 0, None
    best = (0, None)
    for m in cat:
        p = mv._pontos(m, t, ant, emo)
        if p and p > best[0]: best = (p, m)
    return best

for h in ("069d6b2714360774e3ffb2ea7c6edb40", "0cef08cbc210a43574f4ae6427b02d2e"):
    fr = [re.sub(r"^\[[\d.]+s\]\s*", "", x) for x in json.loads((CACHE/f"{h}.json").read_text(encoding="utf-8"))["roteiro"]]
    notas = [nota(fr, k) for k in range(len(fr))]
    cands = [(k, p, m) for k, (p, m) in enumerate(notas) if m and 10 <= k <= len(fr)-4]
    inter = mv.escolher_interrupcoes(fr, inicio=10, cada=12, rnd=random.Random(3))
    print(f"\n===== {h[:8]} {len(fr)} frases | candidatos: {len(cands)} | escolhidos pelo codigo: {len(inter)}")
    print("distribuicao das notas dos candidatos:", sorted([round(p,1) for _,p,_ in cands], reverse=True)[:40])
    print("\n-- ESCOLHIDOS PELO CODIGO (nota | melhor nota nas 12 frases seguintes que ele bloqueou):")
    for k, m in inter:
        p = notas[k][0]
        bloq = max([(notas[j][0], j) for j in range(k+1, min(len(fr), k+12))] or [(0, k)])
        print(f"  {k:4} nota {p:4.1f} {Path(m['file']).name[:30]:30} | bloqueou {bloq[0]:4.1f} na {bloq[1]}")
        print(f"       antes: {fr[k-1][:90]}")
        print(f"       FRASE: {fr[k][:90]}")
        print(f"       depois:{fr[k+1][:90] if k+1 < len(fr) else ''}")
    print("\n-- TOP 15 momentos por nota:")
    for k, p, m in sorted(cands, key=lambda x: -x[1])[:15]:
        print(f"  {k:4} nota {p:4.1f} {Path(m['file']).name[:30]:30} <- {fr[k][:80]}")
