"""Gatilhos de som por palavra falada pelo criador (assets/gatilhos_palavras.json)."""
import json
import random
import re
import unicodedata
from pathlib import Path
from .common import log, ffprobe_json

_cache = {"table": None, "index": None}


def _norm(t):
    t = unicodedata.normalize("NFKD", str(t).lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9 ]+", "", t).strip()


def load_table(cfg):
    if _cache["table"] is None:
        p = Path(cfg["paths"]["assets"]) / "gatilhos_palavras.json"
        _cache["table"] = json.load(open(p, encoding="utf-8")) if p.exists() else {"gatilhos": []}
        for g in _cache["table"].get("gatilhos", []):
            g["_rx"] = re.compile(g["regex"])
            g["_next"] = re.compile(g["proxima"]) if g.get("proxima") else None
    return _cache["table"]


def _index(cfg):
    """Indice nome_normalizado -> caminho para sfx_memes, sfx e sfx_extras."""
    if _cache["index"] is None:
        idx = []
        for key in ("sfx_memes_library", "sfx_library", "sfx_extras_library"):
            lib = cfg["paths"].get(key)
            if lib and Path(lib).exists():
                for p in Path(lib).rglob("*"):
                    if p.suffix.lower() in (".mp3", ".wav", ".ogg", ".m4a"):
                        idx.append((_norm(p.stem), p))
        _cache["index"] = idx
    return _cache["index"]


def find_sound(cfg, fragments, block, max_s, rnd):
    """Acha um arquivo cujo nome contem um dos fragmentos (ordem = preferencia), curto e nao bloqueado."""
    idx = _index(cfg)
    for frag in fragments:
        f = _norm(frag)
        cands = [p for n, p in idx if f in n and not any(b in n for b in block)]
        rnd.shuffle(cands)
        for p in cands[:6]:
            try:
                d = float(ffprobe_json(cfg, p)["format"].get("duration", 99))
            except Exception:  # noqa: BLE001
                continue
            if d <= max_s:
                return p
    return None


def plan_word_triggers(cfg, words, timeline, duration, emoji_png, seed="x"):
    """words: palavras do criador no timeline ORIGINAL (com s/e). Retorna (sfx, overlays) no timeline cortado."""
    T = load_table(cfg)
    gat = T.get("gatilhos", [])
    if not gat:
        return [], []
    block = [_norm(b) for b in T.get("bloqueio_nomes", [])]
    cooldown = float(T.get("cooldown_s", 5.0))
    max_n = int(T.get("max_por_video", 6))
    gain = float(T.get("gain_db", -10))
    max_s = float(T.get("max_duracao_s", 2.6))
    rnd = random.Random(seed)
    sfx, overlays = [], []
    last_t = -99.0
    OW = cfg["output"]["width"]
    for i, w in enumerate(words):
        if len(sfx) >= max_n:
            break
        tok = _norm(w["w"])
        if not tok or not timeline.inside(w["s"]):
            continue
        for g in gat:
            if not g["_rx"].match(tok):
                continue
            if g["_next"] is not None:
                nxt = _norm(words[i + 1]["w"]) if i + 1 < len(words) else ""
                if not g["_next"].match(nxt):
                    continue
            t = timeline.map(w["s"])
            if t - last_t < cooldown or t >= duration - 0.8:
                break
            snd = find_sound(cfg, g.get("sons", []), block, max_s, rnd)
            if not snd:
                break
            sfx.append({"t": t, "file": snd, "gain_db": gain, "trigger": g.get("nome")})
            if g.get("emoji"):
                png = emoji_png(g["emoji"])
                if png:
                    overlays.append({"t": t, "file": png, "dur": 1.1, "png": True, "x": OW - 170, "y": 300, "w": 170})
            last_t = t
            break
    if sfx:
        log(f"gatilhos de palavra: {len(sfx)} ({', '.join(s['trigger'] for s in sfx)})")
    return sfx, overlays
