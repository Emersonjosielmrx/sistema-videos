"""memes_catalogo.py — escolhe o MEME pelo que a cena diz, usando o catalogo descrito
(config/memes_catalogo.json, gerado por visao no manhwa-react: desc/tags/uso de cada um
dos 251 memes de assets/memes_img).

Antes: build_meme_clip era chamado com os argumentos trocados (o caminho de um SFX virava
o arquivo de SAIDA) e falhava sempre -> nenhum dos 251 memes entrou em video. E quando
funcionava, sorteava qualquer .mp4 da pasta, sem relacao com a cena.

Flag: MEMES=1 (default). So em generos leves (MEMES_GENEROS).
"""
import json
import os
import random
import re
import unicodedata
from pathlib import Path

CATALOGO = Path(__file__).resolve().parent.parent / "config" / "memes_catalogo.json"
MEMES_GENEROS = {"comedia", "curiosidades", "superacao", "motivacional", "romance"}
_STOP = {"quando", "para", "como", "mais", "muito", "isso", "essa", "esse", "algo", "momento",
         "reacao", "reação", "pessoa", "personagem", "anime", "meme", "cena", "uma", "com", "que",
         "dos", "das", "nos", "nas", "pela", "pelo", "sobre", "depois", "antes", "ainda"}

_cache = None


def ativo(genero):
    return os.environ.get("MEMES", "1") == "1" and (genero or "").lower() in MEMES_GENEROS


def _norm(t):
    t = unicodedata.normalize("NFKD", str(t).lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9 ]+", " ", t)


def _tokens(t):
    return {w[:6] for w in _norm(t).split() if len(w) > 3 and w not in _STOP}


def _itens():
    global _cache
    if _cache is None:
        try:
            c = json.load(open(CATALOGO, encoding="utf-8"))
            itens = list(c.values()) if isinstance(c, dict) else c
        except Exception:
            itens = []
        _cache = []
        for it in itens:
            if not it.get("ok", True) or not Path(it.get("file", "")).exists():
                continue
            txt = " ".join([it.get("desc", ""), " ".join(it.get("tags", [])), it.get("uso", "")])
            _cache.append((it, _tokens(txt)))
    return _cache


def escolher(texto, usados=(), seed=None, minimo=2):
    """Meme cujo desc/tags/uso mais combina com o texto da cena. None se nada combina
    o suficiente (melhor sem meme que meme aleatorio)."""
    alvo = _tokens(texto)
    if not alvo:
        return None
    rnd = random.Random(str(seed))
    melhores, top = [], 0
    for it, toks in _itens():
        if it["file"] in usados:
            continue
        s = len(alvo & toks)
        if s > top:
            melhores, top = [it], s
        elif s == top and s > 0:
            melhores.append(it)
    if top < minimo or not melhores:
        return None
    return rnd.choice(melhores)
