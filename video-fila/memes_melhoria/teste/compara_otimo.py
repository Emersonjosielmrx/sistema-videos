# -*- coding: utf-8 -*-
# PC1, so leitura: compara atual (MEMES_MOMENTO_OTIMO=0) x novo, nos 2 roteiros reais. Usa a COPIA em teste\copia_mv.
import importlib, json, os, random, re, sys
from pathlib import Path
os.environ["ANIME_MEMES_SO_NOVOS"] = "1"
sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"D:\recapd-ambientes\producao\bin")
sys.path.insert(0, sys.argv[1])
import memes_visuais as mv
print("modulo:", mv.__file__)
mv.MEMES_IMG = Path(r"D:\hipercool-materiais\assets\memes_img"); mv.NOVOS_DIR = mv.MEMES_IMG / "memes_novos"
mv.FICHAS = mv.NOVOS_DIR / "fichas.json"; mv.CATALOGO = Path(r"D:\recapd-ambientes\producao\config\memes_catalogo.json")
mv.HISTORICO = Path(r"D:\video-fila\memes_melhoria\teste\_hist_vazio.json"); mv._cat = None; mv._fichas = None
print("catalogo:", len(mv.catalogo()))
mv._hist_cache = []
CACHE = Path(r"D:\recapd-ambientes\producao\workspace\roteiro_cache")
def nota(fr, k):
    t, ant = fr[k], fr[k-1] if k else ""
    emo, _ = mv.pede_meme(t, ant)
    return mv._pontos({"file": "x"} , t, ant, emo) if False else max([mv._pontos(m, t, ant, emo) or 0 for m in mv.catalogo()] or [0])
for h in ("069d6b2714360774e3ffb2ea7c6edb40", "0cef08cbc210a43574f4ae6427b02d2e"):
    fr = [re.sub(r"^\[[\d.]+s\]\s*", "", x) for x in json.loads((CACHE/f"{h}.json").read_text(encoding="utf-8"))["roteiro"]]
    for modo in ("0", "1"):
        os.environ["MEMES_MOMENTO_OTIMO"] = modo
        inter = mv.escolher_interrupcoes(fr, inicio=10, cada=12, rnd=random.Random(3))
        ns = [nota(fr, k) for k, _ in inter]
        metade = sum(1 for k, _ in inter if k > len(fr) / 2)
        print(f"\n== {h[:8]} {len(fr)} frases | {'NOVO ' if modo=='1' else 'ATUAL'}: {len(inter)} memes | nota total {sum(ns):.0f} | 2a metade: {metade}")
        if modo == "1":
            for (k, m), n in zip(inter, ns):
                print(f"   {k:4} {n:4.1f} {Path(m['file']).name[:30]:30} <- {fr[k][:75]}")
