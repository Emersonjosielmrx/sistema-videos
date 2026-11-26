# -*- coding: utf-8 -*-
# Roda no PC1 (so leitura, nao grava historico): confere os 37 memes novos com o codigo da producao.
import json
import os
import random
import re
import sys
from pathlib import Path

os.environ["ANIME_MEMES_SO_NOVOS"] = "1"  # como no config/longo.json
sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"D:\recapd-ambientes\producao\bin")
import memes_visuais as mv  # noqa: E402

NOVOS = Path(r"D:\hipercool-materiais\assets\memes_img\memes_novos")
CACHE = Path(r"D:\recapd-ambientes\producao\workspace\roteiro_cache")

cat = mv.catalogo()
print(f"catalogo: {len(cat)} memes | fichas: {len(mv.fichas())}")
nomes = sorted(Path(m["file"]).name for m in cat)
print("de 21 em diante no catalogo:", len([n for n in nomes if int(n[:2]) >= 21]), "de 17")
faltam = [n for n in sorted(p.name for p in NOVOS.glob("*.mp4")) if n not in nomes]
print("mp4 na pasta fora do catalogo:", faltam or "nenhum")

print("\n== fora do resumo (abertura) ==")
for p in sorted(NOVOS.glob("*.mp4")):
    if mv.fora_do_resumo(p.name):
        print("  fora:", p.name)

print("\n== frases soltas ==")
frases = [
    "Ele destruiu tudo e não restou nada da cidade inteira.",
    "A garota pediu socorro, desesperada, no meio da rua.",
    "Ela tratou mal o garçom, uma atitude feia na frente de todo mundo.",
    "O protagonista garantiu que estava tudo sob controle.",
    "O garoto não entendeu nada do que estava acontecendo.",
    "Todos ficaram parados pensando: que poder é esse?",
    "O cliente ficou esperando o pagamento por meses, mas levou calote.",
    "Ele só falou besteira durante toda a reunião.",
    "Ele recebeu o troco na mesma moeda.",
    "O tio da vila morreu e todos foram ao funeral, com muito luto.",
    "Ele pediu socorro enquanto o amigo morria nos braços dele.",
]
for f in frases:
    emo, forca = mv.pede_meme(f)
    m = mv._por_contexto(f, [x for x in cat if x.get("has_audio")], emo, random.Random(1)) if forca else None
    print(f"  {forca} {Path(m['file']).name if m else '-':38} <- {f[:70]}")

print("\n== roteiros reais (sem gravar historico) ==")
mv._hist_cache = []
for h in ("069d6b2714360774e3ffb2ea7c6edb40", "0cef08cbc210a43574f4ae6427b02d2e"):
    fr = json.loads((CACHE / f"{h}.json").read_text(encoding="utf-8"))["roteiro"]
    fr = [re.sub(r"^\[[\d.]+s\]\s*", "", x) for x in fr]
    inter = mv.escolher_interrupcoes(fr, inicio=10, cada=12, rnd=random.Random(3))
    print(f"{h[:8]}: {len(fr)} frases -> {len(inter)} memes")
    for k, m in inter:
        n = Path(m["file"]).name
        print(f"   {k:4} {n[:36]:36} <- {fr[k][:60]}")
