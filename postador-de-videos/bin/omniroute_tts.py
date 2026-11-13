"""omniroute_tts.py — TTS via OmniRoute GPT Audio (fallback para vozes masculinas).

Usa gpt-audio-mini (combo com fallback automático no proxy OmniRoute).
NÃO substitui edge-tts/ElevenLabs/Gemini — é o ÚLTIMO recurso antes do edge.

CLI: python bin/omniroute_tts.py --text "Teste" --out test.wav
"""
import json
import base64
import time
import subprocess
import urllib.request
import argparse
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent

OMNIROUTE_URL = "http://157.173.207.22:20128/v1/chat/completions"
from _segredos import omniroute_auth  # noqa: E402  (chave em secrets/omniroute_key.txt)
OMNIROUTE_KEY = omniroute_auth()

MODEL = "openrouter/openai/gpt-audio-mini"

_exhausted = False
_exhausted_at = 0.0
_RETRY_INTERVAL = 300


def log(msg):
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    print(f"[{ts}] {msg}", flush=True)


def speak(text, persona="Homem", out_wav=None):
    """Gera TTS via OmniRoute GPT Audio. Returns True/False."""
    global _exhausted, _exhausted_at

    text = (text or "").strip()
    if len(text) < 4:
        return False

    out_wav = Path(out_wav)

    if _exhausted and (time.time() - _exhausted_at) < _RETRY_INTERVAL:
        return False
    if _exhausted:
        _exhausted = False
        log("  🔄 re-tentando OmniRoute GPT Audio...")

    prompt = (
        f"Leia o texto abaixo em português brasileiro com voz masculina, "
        f"tom natural e expressivo, como narração de anime/manhwa:\n\n{text}"
    )

    try:
        body = json.dumps({
            "model": MODEL,
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

        log(f"  → omniroute-tts persona={persona} text={text[:50]!r}")
        resp = urllib.request.urlopen(req, timeout=60)
        data = json.loads(resp.read())

        audio_b64 = (data.get("choices", [{}])[0]
                     .get("message", {}).get("audio", {}).get("data"))
        if not audio_b64:
            log("  ⚠ OmniRoute: sem campo audio na resposta")
            _exhausted = True
            _exhausted_at = time.time()
            return False

        audio_bytes = base64.b64decode(audio_b64)
        if len(audio_bytes) < 500:
            log(f"  ⚠ OmniRoute: áudio muito pequeno ({len(audio_bytes)} bytes)")
            return False

        tmp = out_wav.with_suffix(".omniroute.tmp")
        tmp.write_bytes(audio_bytes)

        subprocess.run(
            ["ffmpeg", "-y", "-i", str(tmp), "-ar", "44100", "-ac", "2", str(out_wav)],
            check=True, capture_output=True, timeout=30,
        )
        tmp.unlink()

        if out_wav.exists() and out_wav.stat().st_size > 1000:
            log(f"  ✓ omniroute-tts wrote {out_wav.name} ({out_wav.stat().st_size // 1024} KB)")
            return True
        return False

    except Exception as e:
        log(f"  ⚠ OmniRoute TTS err: {e}")
        _exhausted = True
        _exhausted_at = time.time()
        return False


def main():
    p = argparse.ArgumentParser(description="OmniRoute GPT Audio TTS")
    p.add_argument("--text", required=True, help="Texto pra sintetizar")
    p.add_argument("--out", default="test_omniroute.wav", help="Arquivo de saída WAV")
    p.add_argument("--persona", default="Homem", help="Nome do personagem")
    args = p.parse_args()

    ok = speak(args.text, persona=args.persona, out_wav=args.out)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
