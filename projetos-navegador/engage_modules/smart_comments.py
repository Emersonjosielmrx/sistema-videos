"""
smart_comments.py — Comentários contextuais via Gemini Flash.

Gera comentários únicos baseados no título/canal do vídeo.
Usa cache pra não gastar token em vídeos já comentados.
Fallback: comentário genérico se Gemini falhar/quota.
"""
import json
import random
import time
import hashlib
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError

from .logger import log
from .personalities import get_personality_prompt
from .config import BASE_DIR

KEYS_FILE = BASE_DIR / "secrets" / "gemini_keys.json"
CACHE_FILE = BASE_DIR / "smart_comments_cache.json"
MODEL = "gemini-2.5-flash-lite"
API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

_keys = []
_key_idx = 0
_cache = {}
_cache_loaded = False


def _load_keys():
    global _keys
    if not _keys:
        try:
            _keys = json.loads(KEYS_FILE.read_text("utf-8"))
        except:
            _keys = []


def _load_cache():
    global _cache, _cache_loaded
    if _cache_loaded:
        return
    try:
        if CACHE_FILE.exists():
            _cache = json.loads(CACHE_FILE.read_text("utf-8"))
    except:
        _cache = {}
    _cache_loaded = True


def _save_cache():
    try:
        CACHE_FILE.write_text(
            json.dumps(_cache, ensure_ascii=False),
            encoding="utf-8"
        )
    except:
        pass


def _call_gemini(prompt, lang):
    """Chama Gemini Flash com rotação de chaves."""
    global _key_idx
    _load_keys()
    if not _keys:
        return None

    for _ in range(min(5, len(_keys))):
        key = _keys[_key_idx % len(_keys)]
        _key_idx += 1

        url = f"{API_BASE}/{MODEL}:generateContent?key={key}"
        body = json.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 1.2,
                "maxOutputTokens": 60,
            }
        }).encode()

        req = Request(url, data=body, headers={"Content-Type": "application/json"})
        try:
            resp = urlopen(req, timeout=10)
            data = json.loads(resp.read())
            text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            text = text.strip('"').strip("'").strip()
            if len(text) > 3 and len(text) < 200:
                return text
        except URLError:
            continue
        except (KeyError, IndexError):
            continue
        except Exception:
            continue

    return None


PROMPTS_BY_LANG = {
    "pt": "Escreva UM comentário curto (5-12 palavras) pra um vídeo do YouTube chamado \"{title}\" do canal @{channel}. Seja natural, entusiasta mas não exagerado. Só o comentário, sem aspas.",
    "en": "Write ONE short YouTube comment (5-12 words) for a video titled \"{title}\" by @{channel}. Be natural and enthusiastic. Just the comment, no quotes.",
    "es": "Escribe UN comentario corto (5-12 palabras) para un video de YouTube llamado \"{title}\" de @{channel}. Sé natural. Solo el comentario.",
    "fr": "Écris UN commentaire court (5-12 mots) pour une vidéo YouTube intitulée \"{title}\" de @{channel}. Sois naturel. Juste le commentaire.",
    "it": "Scrivi UN commento breve (5-12 parole) per un video YouTube intitolato \"{title}\" di @{channel}. Sii naturale. Solo il commento.",
    "th": "Write ONE short comment (5-12 words) in simple English for a YouTube video titled \"{title}\" by @{channel}. Just the comment.",
    "vi": "Write ONE short comment (5-12 words) in simple English for a YouTube video titled \"{title}\" by @{channel}. Just the comment.",
    "hi": "Write ONE short comment (5-12 words) in simple English for a YouTube video titled \"{title}\" by @{channel}. Just the comment.",
    "ru": "Write ONE short comment (5-12 words) in simple English for a YouTube video titled \"{title}\" by @{channel}. Just the comment.",
    "id": "Tulis SATU komentar singkat (5-12 kata) untuk video YouTube berjudul \"{title}\" dari @{channel}. Alami saja. Hanya komentarnya.",
}


def get_smart_comment(vid_key, title, channel, lang, account=None):
    """
    Gera comentário contextual via Gemini.
    Usa cache pra não regerar.
    Retorna None se falhar (caller deve usar fallback genérico).
    """
    _load_cache()

    cache_key = hashlib.md5(f"{vid_key}:{lang}:{account or ''}".encode()).hexdigest()[:12]
    if cache_key in _cache:
        return _cache[cache_key]

    if not title:
        return None

    prompt_template = PROMPTS_BY_LANG.get(lang, PROMPTS_BY_LANG["en"])
    prompt = prompt_template.format(title=title[:80], channel=channel[:30])

    if account:
        personality_hint = get_personality_prompt(account)
        prompt = f"{personality_hint}\n\n{prompt}"

    comment = _call_gemini(prompt, lang)
    if comment:
        _cache[cache_key] = comment
        if len(_cache) % 10 == 0:
            _save_cache()
        return comment

    return None


def flush_cache():
    """Salva cache pendente no disco."""
    _save_cache()
