"""haiku_helpers.py — decisões do pipeline reforçadas por Claude Haiku (rápido/barato).

Cada função tenta usar o Haiku (via claude_client) para uma decisão que o código
hoje faz por heurística frágil (keywords/regex/altura). Se o Haiku estiver
indisponível ou falhar, RETORNA None e o caller usa o comportamento atual — o fluxo
NUNCA quebra. Resultados são cacheados em memória por chave de conteúdo.

Regra de ouro: Haiku é assistente, não dependência. Tudo degrada para o código.
"""
import json
import os
import re

import claude_client

# liga/desliga global (default ligado). HAIKU_HELPERS=0 desativa tudo.
ENABLED = os.environ.get("HAIKU_HELPERS", "1") != "0"

_MOODS = ["tense_dramatic", "sad_emotional", "romantic_sexy",
          "funny_lighthearted", "calm_chill", "neutral_chill", "action"]

_cache = {}


def _ck(kind, key):
    return f"{kind}::{key}"


def _ask_json(prompt, max_tokens=300):
    """Pergunta ao Haiku e extrai JSON. None se indisponível/falha."""
    if not (ENABLED and claude_client.is_available()):
        return None
    out = claude_client._post([{"role": "user", "content": prompt}],
                              max_tokens=max_tokens, temperature=0.0,
                              model=claude_client.fast_model())
    if not out:
        return None
    return claude_client._extract_json(out)


def _ask_image_json(image_bytes, prompt, max_tokens=400):
    if not (ENABLED and claude_client.is_available()):
        return None
    content = [claude_client._img_block(image_bytes),
               {"type": "text", "text": prompt}]
    out = claude_client._post([{"role": "user", "content": content}],
                              max_tokens=max_tokens, temperature=0.0,
                              model=claude_client.fast_model())
    if not out:
        return None
    return claude_client._extract_json(out)


# ── 1. MOOD do texto/cena ───────────────────────────────────────────────────
def detect_mood(text):
    """Retorna um dos _MOODS, ou None p/ cair no detect_mood_from_text por keyword."""
    text = (text or "").strip()
    if len(text) < 8:
        return None
    key = _ck("mood", text[:120])
    if key in _cache:
        return _cache[key]
    d = _ask_json(
        "Classifique o CLIMA dominante desta fala/cena de manhwa em UMA categoria.\n"
        f"Texto: \"{text[:300]}\"\n"
        f"Categorias válidas: {', '.join(_MOODS)}.\n"
        'Responda JSON: {"mood":"categoria"}. Só isso.')
    mood = (d or {}).get("mood")
    res = mood if mood in _MOODS else None
    _cache[key] = res
    return res


# ── 2. IMPACTO / TENSÃO da cena ─────────────────────────────────────────────
def classify_action(description):
    """Retorna 'impact' | 'tension' | 'calm' ou None (fallback p/ keyword)."""
    description = (description or "").strip()
    if len(description) < 6:
        return None
    key = _ck("action", description[:120])
    if key in _cache:
        return _cache[key]
    d = _ask_json(
        "Esta é a descrição de um painel de manhwa. A cena é de IMPACTO (ação forte, "
        "golpe, explosão, susto), de TENSÃO (suspense, perigo iminente, drama pesado) "
        "ou CALMA (diálogo, cotidiano)?\n"
        f"Descrição: \"{description[:300]}\"\n"
        '{"tipo":"impact|tension|calm"}')
    t = (d or {}).get("tipo")
    res = t if t in ("impact", "tension", "calm") else None
    _cache[key] = res
    return res


# ── 3. PERSONA + GÊNERO de quem fala (olhando o painel) ─────────────────────
def persona_gender(image_bytes, balloon_text=""):
    """Retorna (persona, gender) ou None. gender ∈ {M,F}. Para corrigir 'mulher
    com voz de homem'. Cacheado por texto do balão."""
    key = _ck("persona", (balloon_text or "")[:80])
    if balloon_text and key in _cache:
        return _cache[key]
    d = _ask_image_json(
        image_bytes,
        "Quem está falando este balão neste painel de manhwa e qual o gênero?\n"
        f"Balão: \"{balloon_text[:160]}\"\n"
        'Responda JSON: {"persona":"nome ou rótulo estável","gender":"M ou F"}. '
        "Se for narração sem personagem, persona='Narrador'.")
    if not d:
        return None
    persona = (d.get("persona") or "").strip()
    gender = (d.get("gender") or "").strip().upper()
    if gender not in ("M", "F"):
        gender = None
    res = (persona or None, gender)
    if balloon_text:
        _cache[key] = res
    return res


# ── 4. Painel é CAPA/CRÉDITO ou CONTEÚDO? ───────────────────────────────────
def is_cover_or_credit(image_bytes):
    """True se o painel é capa/título/crédito/anúncio (deve ser pulado), False se é
    conteúdo da história, None se indeciso/indisponível."""
    d = _ask_image_json(
        image_bytes,
        "Este painel de manhwa é CONTEÚDO da história, ou é capa/título/página de "
        "créditos/aviso/anúncio (que deve ser pulada num recap)?\n"
        '{"tipo":"conteudo|capa"}')
    if not d:
        return None
    return d.get("tipo") == "capa"


# ── 5. SFX contextual: o som combina com a cena? ────────────────────────────
def sfx_fits(description, sfx_name):
    """True/False se o SFX sugerido pela keyword realmente cabe na cena; None=fallback."""
    description = (description or "").strip()
    if not description or not sfx_name:
        return None
    key = _ck("sfxfit", (description[:80] + "|" + sfx_name))
    if key in _cache:
        return _cache[key]
    d = _ask_json(
        f"Numa cena de manhwa descrita como: \"{description[:200]}\", "
        f"faz sentido tocar o efeito sonoro '{sfx_name}'? "
        '{"cabe":true|false}')
    res = None if not d else bool(d.get("cabe"))
    _cache[key] = res
    return res


# ── 6. TÍTULO + tags virais ─────────────────────────────────────────────────
def viral_title(resumo, default_titulo):
    """Gera título viral curto + tags a partir de um resumo das locuções. Fallback
    para default_titulo."""
    resumo = (resumo or "").strip()
    if len(resumo) < 20:
        return None
    d = _ask_json(
        "Gere um título viral curto (máx 70 caracteres) e 5 tags para um vídeo de "
        f"recap de manhwa cujo conteúdo é:\n\"{resumo[:600]}\"\n"
        '{"titulo":"...","tags":["..."]}', max_tokens=300)
    if not d or not d.get("titulo"):
        return None
    return {"titulo": d["titulo"][:80], "tags": d.get("tags", [])[:8]}


# ── 7. Onomatopeia: este token é ruído ou fala? ─────────────────────────────
def is_onomatopoeia(token):
    """True se o token é onomatopeia/ruído (não deve ser narrado), None=fallback regex."""
    token = (token or "").strip()
    if not token or len(token) > 30:
        return None
    key = _ck("onoma", token.lower())
    if key in _cache:
        return _cache[key]
    d = _ask_json(
        f"Em português, '{token}' é uma ONOMATOPEIA/efeito sonoro (ruído escrito tipo "
        "DING DONG, POP, BAAARF) ou uma palavra/fala real?\n"
        '{"onomatopeia":true|false}')
    res = None if not d else bool(d.get("onomatopeia"))
    _cache[key] = res
    return res


# ── 8. Painel é +18 (NUDEZ / SEXO) — olhando a IMAGEM ───────────────────────
import hashlib
from pathlib import Path

_NSFW_CACHE_FILE = Path(__file__).resolve().parent.parent / "workspace" / "nsfw_image_cache.json"
_nsfw_cache = None


def _load_nsfw_cache():
    global _nsfw_cache
    if _nsfw_cache is None:
        try:
            _nsfw_cache = json.loads(_NSFW_CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            _nsfw_cache = {}
    return _nsfw_cache


def _save_nsfw_cache():
    try:
        _NSFW_CACHE_FILE.write_text(json.dumps(_nsfw_cache, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def is_nsfw_image(image_bytes):
    """True se o painel mostra NUDEZ explícita ou ato sexual (deve ser censurado p/ Shorts),
    False se não, None se Haiku indisponível (caller usa só a keyword então).

    Detecção VISUAL (não depende da descrição sanitizada). Cache em disco por hash da imagem
    → re-render não re-pergunta (ZERO custo no reuso). NÃO usa Gemini."""
    if not (ENABLED and claude_client.is_available()) or not image_bytes:
        return None
    h = hashlib.md5(image_bytes).hexdigest()
    cache = _load_nsfw_cache()
    if h in cache:
        return cache[h]
    d = _ask_image_json(
        image_bytes,
        "Este painel de manhwa mostra NUDEZ explícita (genitália, seios, nádegas à mostra), "
        "ato sexual, ou personagem nu(a) de corpo visível (ex. cena de banho/chuveiro com "
        "corpo exposto)? Considere +18 se houver nudez frontal/traseira clara ou ato sexual. "
        "NÃO marque cena vestida, beijo leve, ou abraço.\n"
        '{"nsfw":true|false}', max_tokens=60)
    if d is None or "nsfw" not in d:
        return None
    res = bool(d.get("nsfw"))
    cache[h] = res
    _save_nsfw_cache()
    return res

