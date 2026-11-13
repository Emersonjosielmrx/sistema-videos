# -*- coding: utf-8 -*-
"""multilingual.py - Traducao automatica de roteiros + TTS multi-idioma.

Reutiliza mesmas imagens, traduz texto via Gemini, gera TTS em outro idioma.
Idiomas: es (espanhol), en (ingles), fr (frances), de (alemao), it (italiano).
"""
import json
import hashlib
import urllib.request
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hp_common import PROJECT_DIR, STORIES_DIR, log

import gateway_cfg  # noqa: E402
OMNIROUTE_URL = gateway_cfg.url("/v1/chat/completions")
OMNIROUTE_KEY = gateway_cfg.bearer()  # secrets/omniroute.json
MODEL = "antigravity/gemini-2.5-flash-lite"

TRANSLATION_CACHE = STORIES_DIR / "_translations"
TRANSLATION_CACHE.mkdir(parents=True, exist_ok=True)

LANG_NAMES = {
    "es": "Spanish (Latin America)",
    "en": "English (US)",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "ja": "Japanese",
    "ko": "Korean",
}

LANG_VOICES = {
    "es": {"narrator_f": "es-MX-DaliaNeural", "narrator_m": "es-MX-JorgeNeural",
            "female": "es-MX-DaliaNeural", "male": "es-MX-JorgeNeural"},
    "en": {"narrator_f": "en-US-JennyNeural", "narrator_m": "en-US-GuyNeural",
            "female": "en-US-AriaNeural", "male": "en-US-GuyNeural"},
    "fr": {"narrator_f": "fr-FR-DeniseNeural", "narrator_m": "fr-FR-HenriNeural",
            "female": "fr-FR-DeniseNeural", "male": "fr-FR-HenriNeural"},
    "de": {"narrator_f": "de-DE-KatjaNeural", "narrator_m": "de-DE-ConradNeural",
            "female": "de-DE-KatjaNeural", "male": "de-DE-ConradNeural"},
    "it": {"narrator_f": "it-IT-ElsaNeural", "narrator_m": "it-IT-DiegoNeural",
            "female": "it-IT-ElsaNeural", "male": "it-IT-DiegoNeural"},
    "ja": {"narrator_f": "ja-JP-NanamiNeural", "narrator_m": "ja-JP-KeitaNeural",
            "female": "ja-JP-NanamiNeural", "male": "ja-JP-KeitaNeural"},
    "ko": {"narrator_f": "ko-KR-SunHiNeural", "narrator_m": "ko-KR-InJoonNeural",
            "female": "ko-KR-SunHiNeural", "male": "ko-KR-InJoonNeural"},
}


def _cache_path(story_id, lang):
    return TRANSLATION_CACHE / f"{story_id}_{lang}.json"


def voice_for_lang(lang, persona, gender=None):
    """Retorna a voz edge-tts correta pro idioma e persona."""
    voices = LANG_VOICES.get(lang, LANG_VOICES["en"])
    if persona in ("Narrador", "Narradora"):
        return voices["narrator_f"]
    if gender == "M":
        return voices["male"]
    return voices["female"]


def translate_story(story, target_lang, story_id=None):
    """Traduz um roteiro completo pra outro idioma.

    Args:
        story: dict original (com cenas em PT-BR)
        target_lang: codigo do idioma (es, en, fr, de, it)
        story_id: id pra cache

    Returns:
        dict traduzido (mesma estrutura, textos no idioma alvo) ou None
    """
    if not story_id:
        story_id = f"{story.get('genero', 'misc')}_{hashlib.md5(story.get('titulo', '').encode()).hexdigest()[:10]}"

    cached = _cache_path(story_id, target_lang)
    if cached.exists():
        log(f"  multilingual: cache hit ({target_lang}) {cached.name}")
        return json.loads(cached.read_text(encoding="utf-8"))

    lang_name = LANG_NAMES.get(target_lang, target_lang)

    texts_to_translate = []
    texts_to_translate.append(story.get("titulo", ""))
    for cena in story.get("cenas", []):
        texts_to_translate.append(cena.get("texto", ""))

    numbered = "\n".join(f"{i+1}. {t}" for i, t in enumerate(texts_to_translate))

    prompt = f"""Translate the following numbered texts from Brazilian Portuguese to {lang_name}.
Keep the same numbered format. Maintain the emotional tone, colloquial style, and impact.
Do NOT translate proper names. Do NOT add explanations.

{numbered}"""

    try:
        body = json.dumps({
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 4096,
        }).encode()

        req = urllib.request.Request(
            OMNIROUTE_URL, data=body,
            headers={"Content-Type": "application/json", "Authorization": OMNIROUTE_KEY})

        log(f"  multilingual: traduzindo pra {target_lang} ({len(texts_to_translate)} textos)...")
        resp = urllib.request.urlopen(req, timeout=120)
        data = json.loads(resp.read())
        content = data["choices"][0]["message"]["content"]

        translated_lines = []
        for line in content.strip().split("\n"):
            line = line.strip()
            if line and line[0].isdigit():
                parts = line.split(".", 1)
                if len(parts) == 2:
                    translated_lines.append(parts[1].strip())

        if len(translated_lines) < len(texts_to_translate):
            log(f"  multilingual: traducao incompleta ({len(translated_lines)}/{len(texts_to_translate)})")
            return None

        translated_story = json.loads(json.dumps(story))
        translated_story["titulo"] = translated_lines[0]
        translated_story["lang"] = target_lang
        translated_story["_original_titulo"] = story.get("titulo", "")

        for i, cena in enumerate(translated_story.get("cenas", [])):
            if i + 1 < len(translated_lines):
                cena["texto"] = translated_lines[i + 1]

        cached.write_text(json.dumps(translated_story, indent=2, ensure_ascii=False), encoding="utf-8")
        log(f"  multilingual: OK ({target_lang})")
        return translated_story

    except Exception as e:
        log(f"  multilingual: ERRO - {e}")
        return None


def translate_metadata(titulo, descricao, tags, target_lang):
    """Traduz metadados (titulo, descricao, tags) pra outro idioma."""
    lang_name = LANG_NAMES.get(target_lang, target_lang)
    prompt = f"Translate to {lang_name}. Return JSON with keys: titulo, descricao, tags (array).\ntitulo: {titulo}\ndescricao: {descricao}\ntags: {json.dumps(tags)}"

    try:
        body = json.dumps({
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3, "max_tokens": 1024,
        }).encode()
        req = urllib.request.Request(
            OMNIROUTE_URL, data=body,
            headers={"Content-Type": "application/json", "Authorization": OMNIROUTE_KEY})
        resp = urllib.request.urlopen(req, timeout=60)
        data = json.loads(resp.read())
        content = data["choices"][0]["message"]["content"]
        if "```" in content:
            content = content.split("```")[1].split("```")[0]
            if content.startswith("json"):
                content = content[4:]
        return json.loads(content.strip())
    except Exception as e:
        log(f"  multilingual: metadata translation failed - {e}")
        return {"titulo": titulo, "descricao": descricao, "tags": tags}
