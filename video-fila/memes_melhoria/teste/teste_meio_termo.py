# -*- coding: utf-8 -*-
import json, os, random, re, sys, types
from pathlib import Path
sys.modules["fx_detect"] = types.SimpleNamespace(meme_proibido=lambda _p: False)
sys.path.insert(0, r"D:\recapd-ambientes\producao\bin")
os.environ["ANIME_MEMES_SO_NOVOS"] = "1"
import memes_visuais as mv
mv.MEMES_IMG = Path(r"D:\hipercool-materiais\assets\memes_img"); mv.NOVOS_DIR = mv.MEMES_IMG / "memes_novos"
mv.FICHAS = mv.NOVOS_DIR / "fichas.json"; mv.HISTORICO = Path(r"D:\video-fila\memes_melhoria\teste\_hist_vazio.json")
# meio-termo: tira os gatilhos comuns demais (só na memória do teste)
for e in mv.GATILHOS:
    mv.GATILHOS[e] = [g for g in mv.GATILHOS[e] if g not in ("coitado", "coitada", "tadinho", "tadinha", "de repente", "hein", "ué", "finalmente", "chora", "triste", "sozinho", "sozinha")]
os.environ["MEMES_SORTEIO_GATILHO"] = "1"
for arq in sys.argv[1:]:
    fr = [re.sub(r"^\[[\d.]+s\]\s*", "", f) for f in json.load(open(arq, encoding="utf-8"))["roteiro"]]
    mv._cat = None
    inter = mv.escolher_interrupcoes(fr, inicio=10, cada=12, rnd=random.Random(3))
    print(f"\n== {Path(arq).stem[:8]} {len(fr)} frases: {len(inter)} memes")
    for k, m in inter:
        e, f = mv.pede_meme(fr[k], fr[k-1])
        print(f"  {k:4} {'FICHA' if f == 2 else 'gatilho':7} {Path(m['file']).name[:26]:26} <- {fr[k][:78]}")
