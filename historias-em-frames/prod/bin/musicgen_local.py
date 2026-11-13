# COMUM — fonte única: D:\hipercool-materiais\comum\musicgen_local.py. Mudou esta cópia? python D:\hipercool-materiais\bin\recursos.py subir musicgen_local.py --de <projeto>
"""musicgen_local.py — Gera trilhas instrumentais localmente via MusicGen (Meta).

100% offline, sem API, sem creditos. Usa GPU se disponivel, senao CPU.
Modelo small (~500MB) gera 15-30s de audio em ~2min na CPU.

CLI:
  python bin/musicgen_local.py --prompt "epic anime battle" --duration 15 --out workspace/trilha.wav
  python bin/musicgen_local.py --mood tense_dramatic --out workspace/trilha.wav

Como modulo:
  from musicgen_local import generate
  path = generate("dark orchestral tension", duration=20, out="workspace/test.wav")
"""
import argparse
import time
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = PROJECT_DIR / "workspace" / "assets" / "trilhas" / "_musicgen_cache"

MOOD_PROMPTS = {
    "tense_dramatic": "intense dramatic orchestral music, building tension, percussion, dark strings, cinematic",
    "sad_emotional": "melancholic piano and strings, emotional, bittersweet, slow tempo, cinematic sadness",
    "romantic_sexy": "smooth sensual R&B instrumental, warm bass, intimate atmosphere, slow groove",
    "funny_lighthearted": "playful comedic music, bouncy, quirky instruments, lighthearted cartoon style",
    "calm_chill": "ambient lo-fi beats, peaceful, soft synth pads, relaxing atmospheric",
    "neutral_chill": "neutral background music, lo-fi hip hop beats, unobtrusive, chill",
    "dark_seduction": "dark seductive music, slow bass, mysterious, sultry synth pads, midnight vibe",
    "epic_battle": "epic anime battle music, heavy orchestral, aggressive drums, electric guitar, heroic",
    "horror_tension": "horror ambient, ominous drones, creepy atmosphere, building dread, dissonant",
    "opening_epic": "anime opening theme instrumental, energetic rock with orchestral, rising crescendo, dramatic",
    "opening_dark": "dark anime opening instrumental, heavy drums, ominous strings, psychological thriller",
    "opening_emotional": "emotional anime opening instrumental, piano and strings, bittersweet, hopeful crescendo",
}


def log(msg):
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


_model = None
_processor = None


def _load_model():
    global _model, _processor
    if _model is not None:
        return

    log("Carregando MusicGen-small (primeira vez baixa ~500MB)...")
    from transformers import AutoProcessor, MusicgenForConditionalGeneration
    import torch

    _processor = AutoProcessor.from_pretrained("facebook/musicgen-small")
    _model = MusicgenForConditionalGeneration.from_pretrained("facebook/musicgen-small")

    if torch.cuda.is_available():
        _model = _model.to("cuda")
        log("  GPU detectada, usando CUDA")
    else:
        log("  CPU mode (leva ~2-3min por 15s de audio)")


def generate(prompt, duration=15, out=None, mood=None):
    """Gera audio instrumental. Retorna Path do arquivo ou None."""
    import hashlib

    if mood and mood in MOOD_PROMPTS:
        prompt = MOOD_PROMPTS[mood]

    if not prompt:
        return None

    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    if out:
        out_path = Path(out)
    else:
        h = hashlib.md5(f"{prompt}:{duration}".encode()).hexdigest()[:12]
        out_path = CACHE_DIR / f"{h}_{duration}s.wav"

    if out_path.exists() and out_path.stat().st_size > 5000:
        log(f"  Cache hit: {out_path.name}")
        return out_path

    out_path.parent.mkdir(parents=True, exist_ok=True)

    _load_model()

    import torch
    import scipy.io.wavfile

    log(f"  Gerando {duration}s: {prompt[:60]}...")
    t0 = time.time()

    inputs = _processor(text=[prompt], padding=True, return_tensors="pt")
    if torch.cuda.is_available():
        inputs = {k: v.to("cuda") for k, v in inputs.items()}

    max_tokens = int(duration * 50)

    with torch.no_grad():
        audio_values = _model.generate(**inputs, max_new_tokens=max_tokens)

    audio_data = audio_values[0, 0].cpu().numpy()
    sample_rate = _model.config.audio_encoder.sampling_rate

    scipy.io.wavfile.write(str(out_path), rate=sample_rate, data=audio_data)

    elapsed = time.time() - t0
    size_kb = out_path.stat().st_size // 1024
    log(f"  OK: {out_path.name} ({size_kb} KB, {elapsed:.0f}s)")

    return out_path


def main():
    p = argparse.ArgumentParser(description="MusicGen Local - Trilhas sem API")
    p.add_argument("--prompt", default=None, help="Prompt livre em ingles")
    p.add_argument("--mood", default=None, choices=list(MOOD_PROMPTS.keys()), help="Mood pre-definido")
    p.add_argument("--duration", type=int, default=15, help="Duracao em segundos (max ~30)")
    p.add_argument("--out", default=None, help="Caminho de saida (default: cache)")
    args = p.parse_args()

    if not args.prompt and not args.mood:
        print("Erro: passe --prompt ou --mood")
        sys.exit(1)

    prompt = args.prompt or MOOD_PROMPTS.get(args.mood, "")
    result = generate(prompt, duration=args.duration, out=args.out, mood=args.mood)

    if result and result.exists():
        print(f"\nOK: {result}")
        sys.exit(0)
    else:
        print("\nFALHOU")
        sys.exit(1)


if __name__ == "__main__":
    main()
