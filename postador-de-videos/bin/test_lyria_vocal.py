"""test_lyria_vocal.py — Testa se Lyria gera musica COM VOZ/CANTO."""
import json
import base64
import time
import subprocess
import http.client
import urllib.parse
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = PROJECT_DIR / "workspace" / "_voice_tests" / "08_lyria_vocal"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OMNIROUTE_URL = "http://157.173.207.22:20128/v1/chat/completions"
from _segredos import omniroute_auth  # noqa: E402  (chave em secrets/omniroute_key.txt)
OMNIROUTE_KEY = omniroute_auth()

TESTES_VOCAL = [
    ("01_anime_opening_vocal_pro", "openrouter/google/lyria-3-pro-preview",
     "Compose an anime opening song with female Japanese vocals singing energetically, upbeat J-pop style with electric guitar and drums. 30 seconds."),
    ("02_anime_opening_vocal_clip", "openrouter/google/lyria-3-clip-preview",
     "Compose an anime opening song with female Japanese vocals singing energetically, upbeat J-pop style with electric guitar and drums. 15 seconds."),
    ("03_ballad_masc_vocal_pro", "openrouter/google/lyria-3-pro-preview",
     "Compose a dramatic ballad with a male vocalist singing in Portuguese, emotional and powerful, like an anime ending theme. 30 seconds."),
    ("04_ballad_masc_vocal_clip", "openrouter/google/lyria-3-clip-preview",
     "Compose a dramatic ballad with a male vocalist singing in Portuguese, emotional and powerful, like an anime ending theme. 15 seconds."),
    ("05_rap_ptbr_pro", "openrouter/google/lyria-3-pro-preview",
     "Create a rap song in Brazilian Portuguese with aggressive male vocals, trap beat, dark mood, about power and revenge. 30 seconds."),
    ("06_rap_ptbr_clip", "openrouter/google/lyria-3-clip-preview",
     "Create a rap song in Brazilian Portuguese with aggressive male vocals, trap beat, dark mood, about power and revenge. 15 seconds."),
    ("07_choir_epic_pro", "openrouter/google/lyria-3-pro-preview",
     "Compose epic orchestral music with a dramatic choir singing 'O Fortuna' style, Latin chanting, massive and cinematic. 30 seconds."),
    ("08_choir_epic_clip", "openrouter/google/lyria-3-clip-preview",
     "Compose epic orchestral music with a dramatic choir singing 'O Fortuna' style, Latin chanting, massive and cinematic. 15 seconds."),
    ("09_lofi_hum_pro", "openrouter/google/lyria-3-pro-preview",
     "Create a lofi hip-hop track with soft female humming vocals, chill and dreamy, like a late night study session. 30 seconds."),
    ("10_rock_scream_pro", "openrouter/google/lyria-3-pro-preview",
     "Create intense rock music with male screaming vocals, heavy guitars, aggressive drumming, metal/hardcore style. 30 seconds."),
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
    log("LYRIA — TESTE DE MUSICA COM VOZ/CANTO")
    log("=" * 60)
    log("Testando se Lyria Pro/Clip geram vocal, coro, rap, etc.")
    log("")

    ok_count = 0
    for nome, model, prompt in TESTES_VOCAL:
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
    log(f"=== {ok_count}/{len(TESTES_VOCAL)} geradas ===")
    log(f"Pasta: {OUT_DIR}")
    log("Escuta e ve se tem voz humana cantando ou so instrumental!")


if __name__ == "__main__":
    main()
