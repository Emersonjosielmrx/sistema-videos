"""test_lyria_vocal_only.py — Testa Lyria gerando SO VOZ (a cappella, sem instrumentos)."""
import json
import base64
import time
import subprocess
import http.client
import urllib.parse
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = PROJECT_DIR / "workspace" / "_voice_tests" / "09_vozes_puras"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OMNIROUTE_URL = "http://157.173.207.22:20128/v1/chat/completions"
OMNIROUTE_KEY = "Bearer <SEGREDO_REMOVIDO>"

TESTES_VOZ_PURA = [
    ("01_fem_jpop_acappella_pro", "openrouter/google/lyria-3-pro-preview",
     "A cappella female vocal performance, no instruments, no music, just a beautiful female voice singing in Japanese, pop style melody, clear and emotional. 30 seconds."),
    ("02_fem_jpop_acappella_clip", "openrouter/google/lyria-3-clip-preview",
     "A cappella female vocal performance, no instruments, no music, just a beautiful female voice singing in Japanese, pop style melody, clear and emotional. 15 seconds."),
    ("03_masc_ptbr_acappella_pro", "openrouter/google/lyria-3-pro-preview",
     "A cappella male vocal solo, no instruments, no background music, just a male voice singing in Brazilian Portuguese, emotional ballad style. 30 seconds."),
    ("04_masc_ptbr_acappella_clip", "openrouter/google/lyria-3-clip-preview",
     "A cappella male vocal solo, no instruments, no background music, just a male voice singing in Brazilian Portuguese, emotional ballad style. 15 seconds."),
    ("05_choir_acappella_pro", "openrouter/google/lyria-3-pro-preview",
     "A cappella choir, no instruments whatsoever, only human voices harmonizing in a dramatic choral arrangement, cathedral style, powerful and epic. 30 seconds."),
    ("06_choir_acappella_clip", "openrouter/google/lyria-3-clip-preview",
     "A cappella choir, no instruments whatsoever, only human voices harmonizing in a dramatic choral arrangement, cathedral style, powerful and epic. 15 seconds."),
    ("07_fem_humming_pro", "openrouter/google/lyria-3-pro-preview",
     "Solo female humming, no instruments, no music, just a soft female voice humming a gentle lullaby melody, intimate and calming. 30 seconds."),
    ("08_rap_acappella_pro", "openrouter/google/lyria-3-pro-preview",
     "A cappella rap, no beat, no instruments, no music, just a male voice rapping aggressively in Portuguese, pure vocal performance. 30 seconds."),
    ("09_fem_opera_acappella_pro", "openrouter/google/lyria-3-pro-preview",
     "A cappella female opera singer, no orchestra, no instruments, just a powerful soprano voice singing dramatically, classical opera style. 30 seconds."),
    ("10_beatbox_pro", "openrouter/google/lyria-3-pro-preview",
     "Human beatboxing, no instruments, only mouth sounds creating drums, bass and melody, skilled beatbox performance. 30 seconds."),
]


def log(msg):
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def call_omniroute(prompt, model, out_path, timeout=300):
    try:
        body = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "modalities": ["audio"],
            "stream": True,
        }).encode()

        parsed = urllib.parse.urlparse(OMNIROUTE_URL)
        conn = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=timeout)
        conn.request("POST", parsed.path, body=body, headers={
            "Content-Type": "application/json",
            "Authorization": OMNIROUTE_KEY,
        })
        resp = conn.getresponse()

        if resp.status != 200:
            err = resp.read().decode(errors="replace")
            log(f"    HTTP {resp.status}: {err[:200]}")
            conn.close()
            return False

        raw = resp.read().decode(errors="replace")
        conn.close()

        audio_chunks = []
        for line in raw.split("\n"):
            line = line.strip()
            if not line.startswith("data: "):
                continue
            payload = line[6:]
            if payload == "[DONE]":
                break
            try:
                chunk = json.loads(payload)
                delta = chunk.get("choices", [{}])[0].get("delta", {})
                audio_data = delta.get("audio", {})
                if isinstance(audio_data, dict) and audio_data.get("data"):
                    audio_chunks.append(audio_data["data"])
            except json.JSONDecodeError:
                pass

        if not audio_chunks:
            try:
                data = json.loads(raw)
                b64 = data.get("choices", [{}])[0].get("message", {}).get("audio", {}).get("data")
                if b64:
                    audio_chunks = [b64]
            except:
                pass

        if not audio_chunks:
            log(f"    Sem audio (resp: {raw[:150]})")
            return False

        full_b64 = "".join(audio_chunks)
        audio_bytes = base64.b64decode(full_b64)

        if len(audio_bytes) < 500:
            log(f"    Audio muito pequeno ({len(audio_bytes)} bytes)")
            return False

        tmp = out_path.with_suffix(".tmp")
        tmp.write_bytes(audio_bytes)

        subprocess.run(
            ["ffmpeg", "-y", "-i", str(tmp), "-ar", "44100", "-ac", "2", "-b:a", "192k", str(out_path)],
            check=True, capture_output=True, timeout=30,
        )
        tmp.unlink(missing_ok=True)

        if out_path.exists() and out_path.stat().st_size > 1000:
            return True
    except Exception as e:
        log(f"    Erro: {e}")
    return False


def main():
    log("=" * 60)
    log("LYRIA — TESTE DE VOZ PURA (a cappella, sem instrumentos)")
    log("=" * 60)
    log("")

    ok_count = 0
    for nome, model, prompt in TESTES_VOZ_PURA:
        tag = "PRO" if "pro" in model else "CLIP"
        log(f"  [{nome}] ({tag})")
        log(f"    prompt: {prompt[:80]}...")
        out = OUT_DIR / f"{nome}.mp3"
        ok = call_omniroute(prompt, model, out, timeout=300)
        if ok:
            kb = out.stat().st_size // 1024
            log(f"    OK ({kb} KB)")
            ok_count += 1
        else:
            log(f"    FALHOU")
        time.sleep(3)

    log("")
    log(f"=== {ok_count}/{len(TESTES_VOZ_PURA)} geradas ===")
    log(f"Pasta: {OUT_DIR}")


if __name__ == "__main__":
    main()
