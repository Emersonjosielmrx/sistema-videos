"""test_retry_failed.py — Re-tenta ElevenLabs + OmniRoute com as correcoes."""
import asyncio
import sys
import os
import json
import time
import base64
import subprocess
import urllib.request
import re
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = PROJECT_DIR / "workspace" / "_voice_tests"

TEXTO = (
    "Ele nunca imaginou que aquele seria seu ultimo dia. "
    "O sangue escorria pelo chao enquanto a escuridao tomava conta de tudo. "
    "Mas no fundo do seu coracao, uma chama ainda ardia."
)

ELEVENLABS_VOICES = [
    {"name": "Brian", "id": "nPczCjzI2devNBz1zQrb", "style": "deep resonant"},
    {"name": "Adam", "id": "pNInz6obpgDQGcFmaJgB", "style": "dominant firm"},
    {"name": "Eric", "id": "cjVigY5qzO86Huf0OWal", "style": "smooth trustworthy"},
    {"name": "Chris", "id": "iP95p4xoKVk53GoZ742B", "style": "charming"},
    {"name": "George", "id": "JBFqnCBsd6RMkjVDRZzb", "style": "warm storyteller"},
    {"name": "Charlie", "id": "IKne3meq5aSn9XLyUdCD", "style": "deep confident"},
    {"name": "Roger", "id": "CwhRBWXzGAHq8TQ4Fs17", "style": "laid-back casual"},
    {"name": "Daniel", "id": "onwK4e9ZLuTAKqWW03F9", "style": "steady broadcaster"},
    {"name": "Liam", "id": "TX3LPaxmHKxFdv7VOQHJ", "style": "energetic"},
    {"name": "Bill", "id": "pqHfZKP75CvOlQylNhV4", "style": "wise mature"},
    {"name": "Harry", "id": "SOYHLrjzK2X1ezoPC6cr", "style": "fierce warrior"},
    {"name": "Callum", "id": "N2lVS1w4EtoT3dr4eOWO", "style": "husky trickster"},
    {"name": "Will", "id": "bIHbv24MWmeRgasZH58o", "style": "relaxed optimist"},
]

OMNIROUTE_URL = "http://157.173.207.22:20128/v1/chat/completions"
from _segredos import omniroute_auth  # noqa: E402  (chave em secrets/omniroute_key.txt)
OMNIROUTE_KEY = omniroute_auth()

def log(msg):
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def gen_elevenlabs(voice_info, out_path, api_key):
    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_info['id']}"
        body = json.dumps({
            "text": TEXTO,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
        }).encode()

        req = urllib.request.Request(url, data=body, headers={
            "Content-Type": "application/json",
            "xi-api-key": api_key,
        })
        resp = urllib.request.urlopen(req, timeout=30)
        audio = resp.read()
        if len(audio) > 1000:
            out_path.write_bytes(audio)
            log(f"  OK eleven/{voice_info['name']} ({len(audio) // 1024} KB)")
            return True
        else:
            log(f"  FALHOU eleven/{voice_info['name']}: audio muito pequeno")
    except Exception as e:
        log(f"  FALHOU eleven/{voice_info['name']}: {e}")
    return False


def gen_omniroute_stream(out_path):
    """OmniRoute GPT Audio com stream=true (necessário pra modalities audio)."""
    try:
        import http.client
        import urllib.parse

        prompt = (
            "Leia o texto abaixo em portugues brasileiro com voz masculina, "
            "tom natural e expressivo, como narracao de anime:\n\n" + TEXTO
        )
        body = json.dumps({
            "model": "openrouter/openai/gpt-audio-mini",
            "messages": [{"role": "user", "content": prompt}],
            "modalities": ["audio"],
            "stream": True,
        }).encode()

        parsed = urllib.parse.urlparse(OMNIROUTE_URL)
        conn = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=90)
        conn.request("POST", parsed.path, body=body, headers={
            "Content-Type": "application/json",
            "Authorization": OMNIROUTE_KEY,
        })
        resp = conn.getresponse()
        log(f"  OmniRoute stream status={resp.status}")

        if resp.status != 200:
            err = resp.read().decode(errors="replace")
            log(f"  FALHOU omniroute stream: {err[:200]}")
            return False

        # Ler SSE e acumular audio chunks
        audio_chunks = []
        raw = resp.read().decode(errors="replace")

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

        conn.close()

        if not audio_chunks:
            log("  FALHOU omniroute: nenhum chunk de audio recebido")
            # Tentar extrair de formato nao-SSE
            try:
                data = json.loads(raw)
                b64 = data.get("choices", [{}])[0].get("message", {}).get("audio", {}).get("data")
                if b64:
                    audio_chunks = [b64]
            except:
                pass

        if not audio_chunks:
            log(f"  FALHOU omniroute: raw response snippet = {raw[:300]}")
            return False

        full_b64 = "".join(audio_chunks)
        audio_bytes = base64.b64decode(full_b64)
        log(f"  OmniRoute audio: {len(audio_bytes)} bytes brutos")

        if len(audio_bytes) < 500:
            return False

        tmp = out_path.with_suffix(".tmp")
        tmp.write_bytes(audio_bytes)
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(tmp), "-ar", "44100", "-ac", "2", str(out_path)],
            check=True, capture_output=True, timeout=30,
        )
        tmp.unlink(missing_ok=True)

        if out_path.exists() and out_path.stat().st_size > 1000:
            log(f"  OK omniroute/gpt-audio ({out_path.stat().st_size // 1024} KB)")
            return True
    except Exception as e:
        log(f"  FALHOU omniroute: {e}")
    return False


def main():
    log("=== RE-TESTE: ElevenLabs + OmniRoute ===")
    log(f"Texto: {TEXTO[:60]}...")

    # ElevenLabs com campo correto (token)
    log("")
    log("--- ElevenLabs (campo 'token') ---")
    eleven_dir = OUT_DIR / "02_elevenlabs"
    eleven_dir.mkdir(parents=True, exist_ok=True)

    keys_file = PROJECT_DIR / "secrets" / "elevenlabs_keys.json"
    keys_data = json.loads(keys_file.read_text(encoding="utf-8"))
    api_keys = keys_data.get("keys", [])

    # Encontrar primeira key disponível
    api_key = None
    for k in api_keys:
        if isinstance(k, dict) and k.get("status") == "available":
            api_key = k.get("token")
            log(f"  Usando key: {k.get('name', '?')} ({api_key[:10]}...)")
            break
    if not api_key:
        log("  NENHUMA key 'available'!")
        return

    eleven_ok = 0
    for i, v in enumerate(ELEVENLABS_VOICES):
        out = eleven_dir / f"{i+1:02d}_{v['name'].lower()}.mp3"
        ok = gen_elevenlabs(v, out, api_key)
        if ok:
            eleven_ok += 1
        time.sleep(1.5)  # rate limit

    log(f"  ElevenLabs: {eleven_ok}/{len(ELEVENLABS_VOICES)} OK")

    # OmniRoute com stream=true
    log("")
    log("--- OmniRoute GPT Audio (stream=true) ---")
    omni_dir = OUT_DIR / "03_omniroute"
    omni_dir.mkdir(parents=True, exist_ok=True)
    out = omni_dir / "01_gpt_audio_mini.wav"
    gen_omniroute_stream(out)

    log("")
    log("Pronto! Confira os arquivos em:")
    log(f"  {OUT_DIR}")


if __name__ == "__main__":
    main()
