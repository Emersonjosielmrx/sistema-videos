"""elevenlabs_tts.py — ElevenLabs TTS engine for male voices (fallback after Gemini).

Rotates keys monthly. Marks keys as exhausted when credits run out.
Multiple voices per persona (deterministic hash).
"""
import json
import os
import sys
import time
import urllib.request
import urllib.error
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # garante achar proxy_router
import proxy_router  # roteador de proxy compartilhado (regra: nunca chamar sem proxy)


def _open_via_proxy(req, timeout=30, max_proxy_tries=4):
    """Abre a requisição SEMPRE via proxy (proxy_router). Em falha de CONEXÃO,
    rotaciona pro próximo proxy. HTTPError (401/429/quota) SOBE — é problema da
    key/API, não do proxy. Se o pool está vazio, proxy_router.current() levanta
    RuntimeError → a chamada falha (NUNCA vai direto)."""
    last = None
    for _ in range(max_proxy_tries):
        proxy = proxy_router.current()          # RAISE se pool vazio → nunca direto
        try:
            return proxy_router.build_opener(proxy).open(req, timeout=timeout)
        except urllib.error.HTTPError:
            raise                                # key/quota — não é o proxy
        except Exception as e:                   # conexão/timeout → troca proxy
            last = e
            proxy_router.rotate()
    raise last if last else RuntimeError("elevenlabs: todos os proxies falharam")


PROJECT_DIR = Path(__file__).resolve().parent.parent
SECRETS = PROJECT_DIR / "secrets"
KEYS_FILE = SECRETS / "elevenlabs_keys.json"

# Male voices pool (multilingual - ElevenLabs handles pt-BR automatically)
MALE_VOICES = [
    # Hugo (library voice "NEiOFjKQRRitVnzQNwhS") removido: free plan bloqueia
    # library voices via API (HTTP 402). As demais são premade e funcionam no free.
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

_keys_data = None
_current_key_idx = 0


def log(msg):
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    print(f"[{ts}] {msg}".encode("utf-8", errors="replace").decode("utf-8", errors="replace"), flush=True)


def _load_keys():
    global _keys_data
    if _keys_data is None:
        if KEYS_FILE.exists():
            _keys_data = json.loads(KEYS_FILE.read_text(encoding="utf-8"))
        else:
            _keys_data = {"keys": []}
    return _keys_data


def _save_keys():
    if _keys_data:
        KEYS_FILE.write_text(json.dumps(_keys_data, indent=2, ensure_ascii=False), encoding="utf-8")


def _get_available_key():
    """Get next available key (not exhausted this month)."""
    global _current_key_idx
    data = _load_keys()
    keys = data.get("keys", [])

    for _ in range(len(keys)):
        key_entry = keys[_current_key_idx % len(keys)]
        _current_key_idx += 1

        if key_entry.get("status") == "available":
            return key_entry

    return None


def _mark_key_exhausted(key_entry):
    """Mark key as used for this month."""
    key_entry["status"] = "exhausted"
    key_entry["used_at"] = time.strftime("%Y-%m-%d")
    _save_keys()
    log(f"  ⚠ ElevenLabs key '{key_entry.get('name')}' esgotou créditos do mês")


def _voice_for_persona(persona):
    """Pick a voice deterministically based on persona name."""
    idx = hash(persona) % len(MALE_VOICES)
    return MALE_VOICES[idx]


def speak(text, persona="Homem", out_wav=None):
    """Generate TTS via ElevenLabs. Returns True on success, False if all keys exhausted.

    Rotates through available keys. Each persona gets a unique voice (deterministic).
    """
    text = (text or "").strip()
    if len(text) < 4:
        return False

    out_wav = Path(out_wav)
    voice = _voice_for_persona(persona)

    # Try each available key
    attempts = 0
    max_attempts = 6  # max keys

    while attempts < max_attempts:
        key_entry = _get_available_key()
        if not key_entry:
            log("  ✗ ElevenLabs: todas as chaves esgotadas este mês")
            return False

        token = key_entry["token"]
        attempts += 1

        log(f"  → elevenlabs voice={voice['name']} persona={persona} key={key_entry['name']} text={text[:50]!r}")

        try:
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice['id']}"
            body = json.dumps({
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                    "style": 0.3,
                }
            }).encode()

            req = urllib.request.Request(
                url,
                data=body,
                headers={
                    "xi-api-key": token,
                    "Content-Type": "application/json",
                    "Accept": "audio/mpeg",
                },
                method="POST",
            )

            tmp_mp3 = out_wav.with_suffix(".tmp.mp3")
            with _open_via_proxy(req, timeout=30) as resp:   # SEMPRE via proxy
                mp3_data = resp.read()
                if len(mp3_data) < 500:
                    log(f"  ⚠ ElevenLabs: resposta muito pequena ({len(mp3_data)} bytes)")
                    continue
                tmp_mp3.write_bytes(mp3_data)

            # Convert MP3 to WAV
            subprocess.run(
                ["ffmpeg", "-y", "-i", str(tmp_mp3), "-ar", "44100", "-ac", "2", str(out_wav)],
                check=True, capture_output=True, timeout=30,
            )
            tmp_mp3.unlink()

            if out_wav.exists() and out_wav.stat().st_size > 1000:
                log(f"  ✓ elevenlabs wrote {out_wav.name} ({out_wav.stat().st_size // 1024} KB) [voice={voice['name']}]")
                return True

        except urllib.error.HTTPError as e:
            msg = e.read().decode("utf-8", errors="replace")[:150]
            if e.code == 401:
                log(f"  ⚠ ElevenLabs key inválida: {key_entry['name']}")
                _mark_key_exhausted(key_entry)
            elif e.code == 429 or "quota" in msg.lower() or "limit" in msg.lower():
                _mark_key_exhausted(key_entry)
            else:
                log(f"  ElevenLabs HTTP {e.code}: {msg}")
                return False
        except Exception as e:
            log(f"  ElevenLabs err: {e}")
            if tmp_mp3.exists():
                tmp_mp3.unlink()
            return False

    return False
