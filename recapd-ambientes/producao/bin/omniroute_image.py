"""omniroute_image.py — Geração de imagens via OmniRoute Image Gen combo (FREE).

Usa chain de 9 modelos (Gemini Flash Lite -> ... -> GPT-5) com failover automatico.
- Thumbnails de capitulo
- Imagens de transicao entre moods
- Assets visuais sob demanda
Sempre com cache local.

CLI: python bin/omniroute_image.py --type thumb --titulo "Teste" --obra test --cap 1
     python bin/omniroute_image.py --type transition --mood-from tense_dramatic --mood-to sad_emotional
"""
import json
import base64
import hashlib
import time
import urllib.request
import argparse
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = PROJECT_DIR / "workspace" / "assets" / "_generated_images"

OMNIROUTE_URL = "http://157.173.207.22:20128/v1/images/generations"
OMNIROUTE_KEY = "Bearer <SEGREDO_REMOVIDO>"
MODELS = [
    "together/google/flash-image-3.1-lite",
    "together/black-forest-labs/FLUX.1-schnell",
    "antigravity/gemini-3.1-flash-image",
]

_exhausted = False
_exhausted_at = 0.0
_RETRY_INTERVAL = 300


def log(msg):
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    print(f"[{ts}] {msg}", flush=True)


def _cache_path(key):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    h = hashlib.md5(key.encode()).hexdigest()[:12]
    return CACHE_DIR / f"{h}.png"


def _generate(prompt, out_path):
    global _exhausted, _exhausted_at

    if _exhausted and (time.time() - _exhausted_at) < _RETRY_INTERVAL:
        return False
    if _exhausted:
        _exhausted = False

    for model in MODELS:
        try:
            body = json.dumps({
                "model": model,
                "prompt": prompt,
                "n": 1,
                "response_format": "b64_json",
            }).encode()

            req = urllib.request.Request(
                OMNIROUTE_URL, data=body,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": OMNIROUTE_KEY,
                },
            )

            log(f"  -> image-gen model={model.split('/')[-1]} prompt={prompt[:50]!r}")
            resp = urllib.request.urlopen(req, timeout=120)
            data = json.loads(resp.read())

            img_list = data.get("data", [])
            img_b64 = None
            if img_list:
                img_b64 = img_list[0].get("b64_json")

            if not img_b64:
                log(f"  ! {model}: sem imagem na resposta, tentando próximo...")
                continue

            img_bytes = base64.b64decode(img_b64)
            if len(img_bytes) < 1000:
                log(f"  ! {model}: imagem muito pequena, tentando próximo...")
                continue

            out_path.write_bytes(img_bytes)
            log(f"  ok image-gen wrote {out_path.name} ({len(img_bytes) // 1024} KB) [{model.split('/')[-1]}]")
            return True

        except Exception as e:
            log(f"  ! {model} err: {e}")
            continue

    _exhausted = True
    _exhausted_at = time.time()
    return False


def generate_thumbnail(titulo, obra, cap_num, style="anime"):
    """Gera thumbnail 1280x720 pro YouTube. Retorna Path ou None."""
    key = f"thumb_{obra}_{cap_num}_{style}"
    cached = _cache_path(key)
    if cached.exists() and cached.stat().st_size > 1000:
        return cached

    prompt = (
        f"Create a dramatic YouTube thumbnail for a manhwa/anime recap video, "
        f"1280x720 pixels, vibrant colors, dramatic lighting. "
        f"Title: '{titulo}'. Style: {style} art with impact text. "
        f"No text overlay needed, just the visual scene. "
        f"Manhwa/anime style illustration, cinematic composition."
    )

    ok = _generate(prompt, cached)
    return cached if ok else None


def generate_transition_image(mood_from, mood_to, obra="default"):
    """Gera imagem de transicao entre moods. Retorna Path ou None."""
    key = f"trans_{obra}_{mood_from}_{mood_to}"
    cached = _cache_path(key)
    if cached.exists() and cached.stat().st_size > 1000:
        return cached

    mood_desc = {
        "tense_dramatic": "tense dramatic battlefield",
        "sad_emotional": "melancholic rainy scene",
        "romantic_sexy": "warm romantic sunset",
        "funny_lighthearted": "bright comedic scene",
        "calm_chill": "peaceful serene landscape",
        "neutral_chill": "neutral atmospheric scene",
    }

    desc_from = mood_desc.get(mood_from, mood_from)
    desc_to = mood_desc.get(mood_to, mood_to)

    prompt = (
        f"Create an atmospheric transition illustration, anime/manhwa style, "
        f"1080x1920 vertical, blending from {desc_from} to {desc_to}. "
        f"Abstract, cinematic, suitable as a brief scene separator. "
        f"No text, no characters, just mood and atmosphere."
    )

    ok = _generate(prompt, cached)
    return cached if ok else None


def generate_filler_panel(context, obra="default"):
    """Gera painel de preenchimento quando faltam paineis. Retorna Path ou None."""
    key = f"filler_{obra}_{hashlib.md5(context.encode()).hexdigest()[:8]}"
    cached = _cache_path(key)
    if cached.exists() and cached.stat().st_size > 1000:
        return cached

    prompt = (
        f"Create a manhwa/anime style illustration panel, 1080x1920 vertical, "
        f"dramatic and atmospheric. Scene context: {context}. "
        f"High quality manga art style, detailed, cinematic."
    )

    ok = _generate(prompt, cached)
    return cached if ok else None


def main():
    p = argparse.ArgumentParser(description="OmniRoute Image Generator")
    p.add_argument("--type", choices=["thumb", "transition", "filler"], required=True)
    p.add_argument("--titulo", default="Teste", help="Titulo do cap (thumb)")
    p.add_argument("--obra", default="test", help="Slug da obra")
    p.add_argument("--cap", type=int, default=1, help="Numero do cap (thumb)")
    p.add_argument("--mood-from", default="tense_dramatic", help="Mood origem (transition)")
    p.add_argument("--mood-to", default="sad_emotional", help="Mood destino (transition)")
    p.add_argument("--context", default="dramatic scene", help="Contexto (filler)")
    args = p.parse_args()

    if args.type == "thumb":
        result = generate_thumbnail(args.titulo, args.obra, args.cap)
    elif args.type == "transition":
        result = generate_transition_image(args.mood_from, args.mood_to, args.obra)
    else:
        result = generate_filler_panel(args.context, args.obra)

    if result:
        print(f"OK: {result}")
        sys.exit(0)
    else:
        print("FALHOU")
        sys.exit(1)


if __name__ == "__main__":
    main()
