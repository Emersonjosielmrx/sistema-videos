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

import gateway_cfg  # noqa: E402
OMNIROUTE_URL = gateway_cfg.url("/v1/images/generations")
OMNIROUTE_KEY = gateway_cfg.bearer()  # secrets/omniroute.json
# (together/* saiu: o gateway responde 400 "No credentials for image provider: together"
#  em toda chamada — eram 2 requisicoes perdidas por imagem)
MODELS = [
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


# Segundos ate a cota de imagem voltar, lido do ultimo 429 do gateway (0 = sem info).
# O image_generator usa isto pra PARAR o video e agendar a retomada na hora certa, em vez
# de ir falhando imagem por imagem.
ULTIMO_RESET_S = 0
ESPERA_CURTA_MAX_S = 90      # 429 com reset curto ("reset after 5s"): espera e repete


def _segundos_reset(msg):
    """'...reset after 1h11m28s' / 'reset after 5s' / 'reset after 4m' -> segundos (ou None)."""
    import re
    m = re.search(r"reset after\s*([0-9hms ]+)", msg or "", re.I)
    if not m:
        return None
    total = 0
    for n, u in re.findall(r"(\d+)\s*([hms])", m.group(1)):
        total += int(n) * {"h": 3600, "m": 60, "s": 1}[u]
    return total or None


def _generate(prompt, out_path):
    global _exhausted, _exhausted_at, ULTIMO_RESET_S
    import os
    import urllib.error

    ULTIMO_RESET_S = 0
    if _exhausted and (time.time() - _exhausted_at) < _RETRY_INTERVAL:
        return False
    if _exhausted:
        _exhausted = False

    # Flow / Nano Banana 2.1 — PRIMÁRIO (dono 25/10: "as imagens tb estamos usando o flow imagens que é melhor").
    # Mesma familia do gemini-3.1-flash-image do gateway, estilo não quebra. ~1-2 min por imagem.
    # FLOW_IMAGEM=0 desliga; Flow pausado ou ausente cai direto no gateway.
    try:
        sys.path.insert(0, r"D:\flow-imagens")
        import cliente as _flow
        if _flow.disponivel() and _flow.gerar(prompt, out_path, formato="9:16", log=log):
            ULTIMO_RESET_S = 0
            return True
    except Exception as e:  # noqa: BLE001
        log(f"  ! flow err: {e}")

    # Fallback: gateway OmniRoute
    cota_longa = False
    for model in MODELS:
        if cota_longa:
            break
        for _tentativa in range(4):
            try:
                body = json.dumps({
                    "model": model,
                    "prompt": prompt,
                    "n": 1,
                    "response_format": "b64_json",
                    "size": "1024x1792",
                    "aspect_ratio": "9:16",
                }).encode()
                req = urllib.request.Request(
                    OMNIROUTE_URL, data=body,
                    headers={"Content-Type": "application/json", "Authorization": OMNIROUTE_KEY},
                )
                log(f"  -> image-gen model={model.split('/')[-1]} prompt={prompt[:50]!r}")
                resp = urllib.request.urlopen(req, timeout=120)
                data = json.loads(resp.read())
                img_list = data.get("data", [])
                img_b64 = img_list[0].get("b64_json") if img_list else None
                if not img_b64:
                    log(f"  ! {model}: sem imagem na resposta")
                    break
                img_bytes = base64.b64decode(img_b64)
                if len(img_bytes) < 1000:
                    log(f"  ! {model}: imagem muito pequena")
                    break
                out_path.write_bytes(img_bytes)
                log(f"  ok image-gen wrote {out_path.name} ({len(img_bytes) // 1024} KB) [{model.split('/')[-1]}]")
                return True
            except urllib.error.HTTPError as e:
                try:
                    msg = e.read().decode("utf-8", "replace")
                except Exception:
                    msg = str(e)
                if e.code != 429:
                    log(f"  ! {model} HTTP {e.code}: {msg[:160]}")
                    break
                espera = _segundos_reset(msg)
                if espera is not None and espera <= ESPERA_CURTA_MAX_S:
                    log(f"  ~ {model}: 429 (volta em {espera}s) — esperando e repetindo")
                    time.sleep(espera + 2)
                    continue
                ULTIMO_RESET_S = espera or 3600
                cota_longa = True
                log(f"  ! {model}: cota de imagem esgotada — volta em {ULTIMO_RESET_S // 60}min")
                break
            except Exception as e:
                log(f"  ! {model} err: {e}")
                break

    # Fallback Pollinations: SO com POLLINATIONS_FALLBACK=1.
    if not cota_longa and os.environ.get("POLLINATIONS_FALLBACK", "0") == "1":
        try:
            encoded = urllib.request.quote(prompt[:500])
            poll_url = f"https://image.pollinations.ai/prompt/{encoded}?width=1080&height=1920&nologo=true"
            log("  -> pollinations fallback...")
            poll_req = urllib.request.Request(poll_url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            resp = urllib.request.urlopen(poll_req, timeout=90)
            img_bytes = resp.read()
            if len(img_bytes) > 5000:
                out_path.write_bytes(img_bytes)
                log(f"  ok pollinations wrote {out_path.name} ({len(img_bytes) // 1024} KB)")
                return True
        except Exception as e:
            log(f"  ! pollinations err: {e}")

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
