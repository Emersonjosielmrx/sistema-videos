"""omniroute_music.py — Geração de trilhas via OmniRoute Lyria (FREE).

Gera música sob demanda pra:
- Trilha de abertura (estilo anime opening, 15-20s)
- Trilhas por mood quando não há local disponível
Sempre com cache local pra não regerar.

CLI: python bin/omniroute_music.py --type opening --style epic --obra test
     python bin/omniroute_music.py --type mood --mood tense_dramatic --obra test
"""
import json
import base64
import hashlib
import time
import subprocess
import urllib.request
import argparse
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = PROJECT_DIR / "workspace" / "assets" / "trilhas" / "_generated"

OMNIROUTE_URL = "http://157.173.207.22:20128/v1/chat/completions"
from _segredos import omniroute_auth  # noqa: E402  (chave em secrets/omniroute_key.txt)
OMNIROUTE_KEY = omniroute_auth()

MODEL_PRO = "openrouter/google/lyria-3-pro-preview"
MODEL_CLIP = "openrouter/google/lyria-3-clip-preview"

_exhausted = False
_exhausted_at = 0.0
_RETRY_INTERVAL = 600

OPENING_PROMPTS = {
    "epic": "Compose an epic anime opening theme, 20 seconds, rising orchestral with electric guitar, building to a dramatic climax, Japanese animation style",
    "dark": "Compose a dark, intense anime opening, 20 seconds, heavy drums, ominous strings, building tension, like a psychological thriller anime",
    "emotional": "Compose an emotional anime opening, 20 seconds, piano and strings, bittersweet melody, building to a hopeful crescendo",
    "action": "Compose a high-energy anime opening, 20 seconds, fast-paced drums and synth, aggressive and exciting, battle shounen style",
    "mystery": "Compose a mysterious anime opening, 20 seconds, eerie piano, subtle electronic beats, building suspense",
}

MOOD_PROMPTS = {
    "tense_dramatic": "Intense dramatic background music for a manhwa scene, building tension, orchestral with percussion, 30 seconds",
    "sad_emotional": "Melancholic emotional background music, soft piano and strings, 30 seconds, bittersweet and moving",
    "romantic_sexy": "Romantic atmospheric background music, gentle and warm, subtle sensuality, 30 seconds",
    "funny_lighthearted": "Light playful background music, comedic timing, quirky instruments, 30 seconds",
    "calm_chill": "Calm serene background music, ambient and peaceful, soft synth pads, 30 seconds",
    "neutral_chill": "Neutral chill background music, lofi beats, relaxed and unobtrusive, 30 seconds",
}


def log(msg):
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    print(f"[{ts}] {msg}", flush=True)


def _cache_path(prompt_key, obra="default"):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    h = hashlib.md5(f"{obra}:{prompt_key}".encode()).hexdigest()[:12]
    return CACHE_DIR / f"{prompt_key}_{h}.mp3"


def _generate(prompt, model, out_path):
    global _exhausted, _exhausted_at

    if _exhausted and (time.time() - _exhausted_at) < _RETRY_INTERVAL:
        return False
    if _exhausted:
        _exhausted = False

    try:
        body = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "modalities": ["audio"],
        }).encode()

        req = urllib.request.Request(
            OMNIROUTE_URL, data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": OMNIROUTE_KEY,
            },
        )

        log(f"  -> lyria model={model.split('/')[-1]} prompt={prompt[:60]!r}")
        resp = urllib.request.urlopen(req, timeout=180)
        data = json.loads(resp.read())

        audio_b64 = (data.get("choices", [{}])[0]
                     .get("message", {}).get("audio", {}).get("data"))
        if not audio_b64:
            log("  ! Lyria: sem campo audio na resposta")
            _exhausted = True
            _exhausted_at = time.time()
            return False

        audio_bytes = base64.b64decode(audio_b64)
        if len(audio_bytes) < 2000:
            log(f"  ! Lyria: audio muito pequeno ({len(audio_bytes)} bytes)")
            return False

        tmp = out_path.with_suffix(".lyria.tmp")
        tmp.write_bytes(audio_bytes)

        subprocess.run(
            ["ffmpeg", "-y", "-i", str(tmp), "-ar", "44100", "-ac", "2",
             "-b:a", "192k", str(out_path)],
            check=True, capture_output=True, timeout=60,
        )
        tmp.unlink()

        if out_path.exists() and out_path.stat().st_size > 5000:
            log(f"  ok lyria wrote {out_path.name} ({out_path.stat().st_size // 1024} KB)")
            return True
        return False

    except Exception as e:
        log(f"  ! Lyria err: {e}")
        _exhausted = True
        _exhausted_at = time.time()
        return False


def generate_opening(obra="default", style="epic"):
    """Gera trilha de abertura estilo anime. Retorna Path ou None."""
    cached = _cache_path(f"opening_{style}", obra)
    if cached.exists() and cached.stat().st_size > 5000:
        log(f"  ok lyria opening cached: {cached.name}")
        return cached

    prompt = OPENING_PROMPTS.get(style, OPENING_PROMPTS["epic"])
    ok = _generate(prompt, MODEL_CLIP, cached)
    return cached if ok else None


def generate_mood_track(mood, obra="default"):
    """Gera trilha por mood. Retorna Path ou None."""
    cached = _cache_path(f"mood_{mood}", obra)
    if cached.exists() and cached.stat().st_size > 5000:
        log(f"  ok lyria mood cached: {cached.name}")
        return cached

    prompt = MOOD_PROMPTS.get(mood)
    if not prompt:
        return None

    ok = _generate(prompt, MODEL_PRO, cached)
    return cached if ok else None


def main():
    p = argparse.ArgumentParser(description="OmniRoute Lyria Music Generator")
    p.add_argument("--type", choices=["opening", "mood"], required=True,
                   help="Tipo de trilha: opening ou mood")
    p.add_argument("--style", default="epic",
                   choices=list(OPENING_PROMPTS.keys()),
                   help="Estilo da opening (só pra --type opening)")
    p.add_argument("--mood", default="tense_dramatic",
                   choices=list(MOOD_PROMPTS.keys()),
                   help="Mood da trilha (só pra --type mood)")
    p.add_argument("--obra", default="test", help="Slug da obra")
    args = p.parse_args()

    if args.type == "opening":
        result = generate_opening(obra=args.obra, style=args.style)
    else:
        result = generate_mood_track(mood=args.mood, obra=args.obra)

    if result:
        print(f"OK: {result}")
        sys.exit(0)
    else:
        print("FALHOU")
        sys.exit(1)


if __name__ == "__main__":
    main()
