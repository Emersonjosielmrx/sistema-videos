# -*- coding: utf-8 -*-
"""pexels_broll.py — busca e cacheia clipes b-roll do Pexels por keyword.

API gratuita, 200 req/hora. Cache local evita re-baixar. Retorna Path do mp4
local ou None se nao encontrou/falhou.

Uso:
    from pexels_broll import buscar_broll
    clip = buscar_broll("business meeting")
    if clip:
        # usar clip em ffmpeg
"""
import hashlib
import json
import time
from pathlib import Path
import requests

_API_KEY = "<SEGREDO_REMOVIDO>"
_CACHE_DIR = Path(__file__).resolve().parent / "cache_pexels"
_CACHE_DIR.mkdir(parents=True, exist_ok=True)
_INDEX = _CACHE_DIR / "_index.json"  # keyword -> {id, file, width, height, duration}
_TIMEOUT = 30

def _carregar_index():
    if _INDEX.exists():
        try:
            return json.loads(_INDEX.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}

def _salvar_index(idx):
    _INDEX.write_text(json.dumps(idx, ensure_ascii=False, indent=2), encoding="utf-8")

def _hash_kw(kw):
    return hashlib.md5(kw.lower().encode("utf-8")).hexdigest()[:12]

def buscar_broll(keyword, orientacao="portrait", duracao_min=5):
    """Busca 1 clipe vertical (9:16) do Pexels por keyword. Retorna Path local
    ou None. orientacao='portrait' (9:16) ou 'landscape' (16:9). duracao_min
    em segundos (filtra clipes muito curtos)."""
    idx = _carregar_index()
    kw_norm = keyword.lower().strip()
    h = _hash_kw(kw_norm)

    # cache hit
    if h in idx:
        local = _CACHE_DIR / idx[h]["file"]
        if local.exists() and local.stat().st_size > 100_000:
            return local

    # API search
    try:
        r = requests.get(
            "https://api.pexels.com/videos/search",
            headers={"Authorization": _API_KEY},
            params={"query": kw_norm, "orientation": orientacao, "per_page": 15},
            timeout=_TIMEOUT
        )
        if r.status_code != 200:
            return None
        dados = r.json()
        videos = dados.get("videos", [])
        if not videos:
            return None

        # filtrar: duracao >= duracao_min, pegar o 1º HD/SD portrait
        for v in videos:
            dur = v.get("duration", 0)
            if dur < duracao_min:
                continue
            files = v.get("video_files", [])
            # procurar arquivo portrait/vertical (width < height)
            for f in files:
                w, h_v = f.get("width", 0), f.get("height", 0)
                if h_v > w and f.get("link"):  # vertical
                    url = f["link"]
                    vid_id = v["id"]
                    fname = f"{h}_{vid_id}.mp4"
                    local = _CACHE_DIR / fname

                    # baixar
                    try:
                        vid_r = requests.get(url, timeout=60, stream=True)
                        if vid_r.status_code == 200:
                            with open(local, "wb") as fp:
                                for chunk in vid_r.iter_content(chunk_size=512*1024):
                                    fp.write(chunk)
                            if local.stat().st_size > 100_000:
                                # gravar no index
                                idx[h] = {
                                    "keyword": kw_norm,
                                    "id": vid_id,
                                    "file": fname,
                                    "width": w,
                                    "height": h_v,
                                    "duration": dur,
                                    "ts": time.time(),
                                }
                                _salvar_index(idx)
                                return local
                    except Exception:
                        pass
    except Exception:
        pass
    return None
