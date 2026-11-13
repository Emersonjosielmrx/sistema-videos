"""Reacoes do criador (vindas do editorial) -> overlay do acervo + emoji + efeito sonoro de meme.

Tipos: laugh, shock, love, angry, question, hype, cringe.
"""
import json
import random
import re
import unicodedata
from pathlib import Path
from .common import log

# overlay do acervo (elemental), emoji e palavras-chave para achar o som de meme na categoria
MAP = {
    "laugh":    {"overlay": "fx_emojirain", "emoji": "😂", "sfx_keys": ["risada", "laugh", "riso", "kkk", "haha", "engra", "comedia"]},
    "shock":    {"overlay": "fx_exclaim",   "emoji": "😱", "sfx_keys": ["susto", "vine", "boom", "impacto", "choque", "shock", "dramatic", "bruh"]},
    "love":     {"overlay": "fx_hearts",    "emoji": "😍", "sfx_keys": ["fofo", "cute", "amor", "love", "uau", "aww", "romance"]},
    "angry":    {"overlay": "fx_anger",     "emoji": "😤", "sfx_keys": ["raiva", "angry", "grito", "bronca", "impacto"]},
    "question": {"overlay": "fx_question",  "emoji": "🤔", "sfx_keys": ["duvida", "misterio", "suspense", "question", "huh"]},
    "hype":     {"overlay": "fx_confetti", "emoji": "🔥", "sfx_keys": ["hype", "vitoria", "win", "epic", "aplauso", "tada", "goool", "impacto"]},
    "cringe":   {"overlay": "fx_sweatdrop", "emoji": "😬", "sfx_keys": ["vergonha", "cringe", "fail", "erro", "nope", "trombone", "tristeza", "comedia"]},
}


# variante anime (ManhwaReact): efeitos classicos de manga sobre o quadro
MAP_ANIME = {
    "laugh":    {"overlay": "fx_emojirain", "emoji": "😂"},
    "shock":    {"overlay": "fx_speedlines", "emoji": "😱"},
    "love":     {"overlay": "fx_blush",     "emoji": "😍"},
    "angry":    {"overlay": "fx_anger",     "emoji": "💢"},
    "question": {"overlay": "fx_question",  "emoji": "❓"},
    "hype":     {"overlay": "fx_powerup",   "emoji": "🔥"},
    "cringe":   {"overlay": "fx_sweatdrop", "emoji": "😅"},
}


def map_for(channel_slug):
    base = {k: dict(v) for k, v in MAP.items()}
    if channel_slug == "manhwareact":
        for k, v in MAP_ANIME.items():
            base[k].update(v)
    return base


def _norm(t):
    t = unicodedata.normalize("NFKD", str(t).lower())
    return "".join(c for c in t if not unicodedata.combining(c))


_catalog = None


def _load_catalog(cfg):
    global _catalog
    if _catalog is not None:
        return _catalog
    lib = Path(cfg["paths"].get("sfx_memes_library", "D:/hipercool-materiais/assets/sfx_memes"))
    idx = Path(cfg["paths"].get("sfx_memes_index", "D:/hipercool-materiais/assets/sfx_memes_categorized.json"))
    entries = []
    if idx.exists():
        try:
            d = json.load(open(idx, encoding="utf-8"))
            files = d.get("files", d)
            if isinstance(files, dict):
                for name, meta in files.items():
                    cat = meta.get("category") or meta.get("categoria") or "" if isinstance(meta, dict) else str(meta)
                    tags = " ".join(str(x) for x in (meta.get("tags", []) if isinstance(meta, dict) else []))
                    entries.append({"file": lib / name, "text": _norm(f"{name} {cat} {tags}")})
            elif isinstance(files, list):
                for meta in files:
                    name = meta.get("file") or meta.get("name") or ""
                    entries.append({"file": lib / name, "text": _norm(json.dumps(meta, ensure_ascii=False))})
        except Exception as e:  # noqa: BLE001
            log(f"memes: indice ilegivel ({e})")
    if not entries and lib.exists():
        entries = [{"file": p, "text": _norm(p.name)} for p in lib.glob("*.mp3")]
    _catalog = [e for e in entries if Path(e["file"]).exists()]
    return _catalog


def pick_meme_sfx(cfg, rtype, seed=None, max_seconds=3.0):
    """Escolhe um som de meme curto que combine com o tipo de reacao (ou None)."""
    cat = _load_catalog(cfg)
    keys = MAP.get(rtype, {}).get("sfx_keys", [])
    cands = [e for e in cat if any(k in e["text"] for k in keys)]
    if not cands:
        return None
    rnd = random.Random(seed)
    rnd.shuffle(cands)
    from .common import ffprobe_json
    for e in cands[:8]:
        try:
            d = float(ffprobe_json(cfg, e["file"])["format"]["duration"])
        except Exception:  # noqa: BLE001
            continue
        if d <= max_seconds:
            return e["file"]
    return None


def plan_reactions(cfg, reactions, timeline, asset_lookup, emoji_png, duration, seed="x", channel_slug=None):
    """Transforma as reacoes do editorial em overlays (acervo + emoji) e SFX no timeline cortado."""
    overlays, sfx = [], []
    MAPC = map_for(channel_slug)
    S = cfg["sfx"]
    gain = float(S.get("meme_gain_db", -8))
    for i, r in enumerate(reactions or []):
        t0 = float(r["t"])
        if not timeline.inside(t0):
            continue
        t = timeline.map(t0)
        if t >= duration - 1.0:
            continue
        m = MAPC.get(r["type"])
        if not m:
            continue
        ov = asset_lookup(m["overlay"])
        if ov:
            from .render import media_duration
            overlays.append({"t": max(0.0, t - 0.1), "file": ov, "dur": media_duration(cfg, ov)})
        png = emoji_png(m["emoji"])
        if png:
            overlays.append({"t": t, "file": png, "dur": 1.4, "png": True, "x": cfg["output"]["width"] - 170, "y": 300, "w": 200})
        if S.get("memes", True):
            sf = pick_meme_sfx(cfg, r["type"], seed=f"{seed}{i}")
            if sf:
                sfx.append({"t": t, "file": sf, "gain_db": gain})
    if overlays or sfx:
        log(f"reacoes: {len(overlays)} overlays, {len(sfx)} sons de meme")
    return overlays, sfx
