# -*- coding: utf-8 -*-
"""Teste a seco com roteiro REAL (roteiro_cache): quantos memes e quais, NOVO (fichas) x ANTIGO (MEMES_CONTEXTO=0).
Só lê; não grava histórico."""
import json, os, random, re, sys, types
from pathlib import Path
sys.modules["fx_detect"] = types.SimpleNamespace(meme_proibido=lambda _p: False)
sys.path.insert(0, r"D:\recapd-ambientes\producao\bin")
os.environ["ANIME_MEMES_SO_NOVOS"] = "1"
import memes_visuais as mv  # noqa: E402
mv.MEMES_IMG = Path(r"D:\hipercool-materiais\assets\memes_img"); mv.NOVOS_DIR = mv.MEMES_IMG / "memes_novos"
mv.FICHAS = mv.NOVOS_DIR / "fichas.json"; mv.HISTORICO = Path(r"D:\video-fila\memes_melhoria\teste\_hist_vazio.json")

arq = sys.argv[1]
fr = json.load(open(arq, encoding="utf-8"))["roteiro"]
fr = [re.sub(r"^\[[\d.]+s\]\s*", "", f) for f in fr]
print("frases:", len(fr))
for modo in ("1", "0"):
    os.environ["MEMES_CONTEXTO"] = modo
    mv._cat = None
    inter = mv.escolher_interrupcoes(fr, inicio=10, cada=12, rnd=random.Random(3))
    print(f"\n== MEMES_CONTEXTO={modo}: {len(inter)} memes")
    for k, m in inter[:40]:
        e, f = mv.pede_meme(fr[k], fr[k-1])
        via = "FICHA" if f == 2 and mv._por_contexto(fr[k], [m], e, random.Random(0), fr[k-1]) else "sorteio"
        print(f"  {k:4} {via:7} {Path(m['file']).name[:30]:30} <- {fr[k][:75]}")
