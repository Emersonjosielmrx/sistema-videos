"""Confere na página PÚBLICA do canal se banner e foto estão no ar (sem login, sem Chrome).

Uso:  python conferir_marca.py                 # os 3 Noturnos
      python conferir_marca.py UCxxxx UCyyyy   # outros canais

Baixa foto e banner para %TEMP%\\conferir_marca\\ para olhar as imagens.
Banner "NAO TEM" = canal sem banner. A foto sempre existe (sem foto própria o YouTube põe uma letra): olhe a imagem.
"""
import os
import re
import sys
import urllib.request
from pathlib import Path

PADRAO = ["UCCF2-yciERdJbuTnruw4jVg", "UCRdCdrORHLWiki711nRgkeQ", "UCfP-zfZaA-n6lK7CyQl197g"]
SAIDA = Path(os.environ.get("TEMP", ".")) / "conferir_marca"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Accept-Language": "pt-BR"}


def baixar(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40).read()


SAIDA.mkdir(exist_ok=True)
for cid in sys.argv[1:] or PADRAO:
    html = baixar(f"https://www.youtube.com/channel/{cid}").decode("utf8", "replace")
    titulo = re.search(r'"title":"([^"]{1,80})","description"', html)
    banner = re.search(r"https://yt3\.googleusercontent\.com/[\w\-/]+?=w\d{3,4}-fcrop", html)
    foto = re.search(r"https://yt3\.googleusercontent\.com/[\w\-/]+?=s900", html)
    print(f"{cid}  {titulo.group(1) if titulo else '?'}")
    for nome, m in (("banner", banner), ("foto", foto)):
        if not m:
            print(f"   {nome}: NAO TEM")
            continue
        url = m.group(0).rsplit("=", 1)[0] + ("=w1060" if nome == "banner" else "=s900")
        arq = SAIDA / f"{cid}_{nome}.jpg"
        arq.write_bytes(baixar(url))
        print(f"   {nome}: no ar -> {arq}")
