"""edge_tts_engine.py — Drop-in replacement for gemini_tts using edge-tts (free, no API key).

Provides the same public API: speak(), voice_for_persona(), VOICES_*, etc.
Uses Webshare proxy as intelligent fallback when direct IP is blocked.
"""
import asyncio
import os
import subprocess
import sys
import time
import json
import argparse
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
SECRETS = PROJECT_DIR / "secrets"
PROXY_LIST_FILE = SECRETS / "proxies.txt"

# --- Voices ---
VOICES_FEMALE = ["pt-BR-FranciscaNeural", "pt-BR-ThalitaMultilingualNeural"]
VOICES_MALE = ["pt-BR-AntonioNeural"]
NARRATOR_VOICES = {"hipercool": "pt-BR-FranciscaNeural", "manhwa": "pt-BR-FranciscaNeural", "broll": "pt-BR-FranciscaNeural"}
VOICES_PREBUILT = VOICES_FEMALE + VOICES_MALE

SENSUAL_STYLE_PREFIX = ""

VOICES_REGISTRY = PROJECT_DIR / "workspace" / "voices-registry.json"

# --- Voice profiles (rate/pitch per role) ---
# --- Virtual voices registry (3 base voices × rate/pitch = many personas) ---
# O pipeline escolhe persona (Narrador, Mulher, Homem, etc.)
# Este registro mapeia automaticamente pra voz + parâmetros.
# Variedade: personas diferentes recebem perfis diferentes pra soar como vozes distintas.

VIRTUAL_VOICES = {
    # === FEMININAS (Francisca base) ===
    "francisca_normal":  {"voice": "pt-BR-FranciscaNeural", "rate": "+0%",  "pitch": "+0Hz"},
    "francisca_aguda":   {"voice": "pt-BR-FranciscaNeural", "rate": "+0%",  "pitch": "+8Hz"},
    "francisca_grave":   {"voice": "pt-BR-FranciscaNeural", "rate": "+0%",  "pitch": "-5Hz"},
    "francisca_rapida":  {"voice": "pt-BR-FranciscaNeural", "rate": "+15%", "pitch": "+3Hz"},
    "francisca_lenta":   {"voice": "pt-BR-FranciscaNeural", "rate": "-10%", "pitch": "-3Hz"},
    "francisca_sussurro":{"voice": "pt-BR-FranciscaNeural", "rate": "-5%",  "pitch": "+10Hz"},
    "francisca_animada": {"voice": "pt-BR-FranciscaNeural", "rate": "+20%", "pitch": "+6Hz"},
    # === FEMININAS (Thalita base) ===
    "thalita_normal":    {"voice": "pt-BR-ThalitaMultilingualNeural", "rate": "+0%",  "pitch": "+0Hz"},
    "thalita_aguda":     {"voice": "pt-BR-ThalitaMultilingualNeural", "rate": "+5%",  "pitch": "+8Hz"},
    "thalita_grave":     {"voice": "pt-BR-ThalitaMultilingualNeural", "rate": "+0%",  "pitch": "-5Hz"},
    "thalita_rapida":    {"voice": "pt-BR-ThalitaMultilingualNeural", "rate": "+15%", "pitch": "+0Hz"},
    "thalita_madura":    {"voice": "pt-BR-ThalitaMultilingualNeural", "rate": "-8%",  "pitch": "-8Hz"},
    "thalita_doce":      {"voice": "pt-BR-ThalitaMultilingualNeural", "rate": "-3%",  "pitch": "+12Hz"},
    # === MASCULINAS (Antonio base) ===
    "antonio_acelerado": {"voice": "pt-BR-AntonioNeural", "rate": "+20%", "pitch": "+3Hz"},
    "antonio_grave":     {"voice": "pt-BR-AntonioNeural", "rate": "+10%", "pitch": "-5Hz"},
    "antonio_agudo":     {"voice": "pt-BR-AntonioNeural", "rate": "+15%", "pitch": "+8Hz"},
    "antonio_jovem":     {"voice": "pt-BR-AntonioNeural", "rate": "+25%", "pitch": "+10Hz"},
    "antonio_meio":      {"voice": "pt-BR-AntonioNeural", "rate": "+15%", "pitch": "+0Hz"},
    "antonio_lento":     {"voice": "pt-BR-AntonioNeural", "rate": "-5%",  "pitch": "-8Hz"},
}

# Pools por gênero pra atribuição automática
_FEMALE_POOL = [
    "francisca_normal", "francisca_aguda", "francisca_grave", "francisca_rapida",
    "francisca_sussurro", "francisca_animada",
    "thalita_normal", "thalita_aguda", "thalita_grave", "thalita_rapida",
    "thalita_madura", "thalita_doce",
]
_MALE_POOL = [
    "antonio_acelerado", "antonio_grave", "antonio_agudo",
    "antonio_jovem", "antonio_meio",
]
_NARRATOR_PROFILE = {"voice": "pt-BR-FranciscaNeural", "rate": "+5%", "pitch": "+0Hz"}

# Mapeamento antigo pra compatibilidade
VOICE_PROFILES = {
    "narrator": _NARRATOR_PROFILE,
    "female":   VIRTUAL_VOICES["thalita_normal"],
    "male":     VIRTUAL_VOICES["antonio_acelerado"],
}

# --- Portuguesify: substitute foreign words with PT-BR synonyms ---
_FOREIGN_WORDS = {
    "personal trainer": "treinador pessoal",
    "personal": "treinador",
    "trainer": "treinador",
    "shopping": "centro comercial",
    "delivery": "entrega",
    "design": "projeto",
    "designer": "projetista",
    "feedback": "retorno",
    "marketing": "divulgação",
    "smartphone": "celular",
    "software": "programa",
    "hardware": "equipamento",
    "online": "conectado",
    "offline": "desconectado",
    "stress": "estresse",
    "sexy": "sensual",
    "baby": "bebê",
    "boyfriend": "namorado",
    "girlfriend": "namorada",
    "drink": "drinque",
    "drinks": "drinques",
    "fitness": "academia",
    "workout": "treino",
    "outfit": "roupa",
    "selfie": "foto",
    "hacker": "invasor",
    "like": "curtida",
    "likes": "curtidas",
    "look": "visual",
    "crush": "paixonite",
    "date": "encontro",
    "stalkear": "perseguir",
    "stalker": "perseguidor",
}


def _portuguesify(text):
    """Replace common English words with PT-BR phonetic equivalents."""
    import re
    result = text
    for eng, ptbr in sorted(_FOREIGN_WORDS.items(), key=lambda x: -len(x[0])):
        result = re.sub(re.escape(eng), ptbr, result, flags=re.IGNORECASE)
    return result

# --- Proxy state ---
_direct_blocked = False
_direct_blocked_at = 0.0
_DIRECT_RETRY_INTERVAL = 300  # testa IP direto a cada 5 min
_webshare_consecutive_fails = 0
_MAX_WEBSHARE_FAILS = 3

# --- Logging ---
def log(msg):
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    try:
        print(f"[{ts}] {msg}", flush=True)
    except UnicodeEncodeError:
        print(f"[{ts}] {msg}".encode("ascii", "replace").decode("ascii"), flush=True)


def _load_proxy():
    if PROXY_LIST_FILE.exists():
        lines = PROXY_LIST_FILE.read_text().strip().splitlines()
        proxies = [l.strip() for l in lines if l.strip() and not l.startswith("#")]
        if proxies:
            return proxies[0]
    return None


def _is_female(voice):
    return voice in VOICES_FEMALE


def _persona_registry():
    if VOICES_REGISTRY.exists():
        try:
            data = json.loads(VOICES_REGISTRY.read_text(encoding="utf-8"))
            return data.get("personas", {})
        except Exception:
            pass
    return {}


def voice_for_persona(persona, gender=None, kind="hipercool"):
    """Map persona name to edge-tts voice."""
    if persona == "Narrador" or persona == "Narradora":
        return NARRATOR_VOICES.get(kind, "pt-BR-FranciscaNeural")

    registry = _persona_registry()
    if persona in registry:
        entry = registry[persona]
        g = entry.get("gender", gender or "F")
    else:
        g = gender or "F"

    if g == "M":
        return "pt-BR-AntonioNeural"
    else:
        return "pt-BR-ThalitaMultilingualNeural"


def _get_voice_profile(voice, persona=""):
    """Get rate/pitch profile based on voice and persona role.

    Assigns a unique virtual voice per persona name (deterministic via hash).
    Narrator always gets the narrator profile. Other personas get variety from pools.
    """
    if persona in ("Narrador", "Narradora"):
        return _NARRATOR_PROFILE

    if voice == "pt-BR-AntonioNeural":
        idx = hash(persona) % len(_MALE_POOL)
        return VIRTUAL_VOICES[_MALE_POOL[idx]]
    else:
        idx = hash(persona) % len(_FEMALE_POOL)
        return VIRTUAL_VOICES[_FEMALE_POOL[idx]]


async def _generate_edge_tts(text, voice, out_path, proxy=None, rate="+0%", pitch="+0Hz"):
    """Run edge-tts async to generate audio."""
    import edge_tts

    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch, proxy=proxy)
    await communicate.save(out_path)


def _try_generate(text, voice, out_mp3, use_proxy=False, rate="+0%", pitch="+0Hz"):
    """Attempt to generate audio. Returns True on success, False on failure."""
    proxy = _load_proxy() if use_proxy else None

    try:
        asyncio.run(_generate_edge_tts(text, voice, out_mp3, proxy=proxy, rate=rate, pitch=pitch))
        if Path(out_mp3).exists() and Path(out_mp3).stat().st_size > 500:
            return True
        return False
    except Exception as e:
        log(f"  edge-tts err (proxy={'yes' if use_proxy else 'no'}): {e}")
        return False


def _convert_mp3_to_wav(mp3_path, wav_path):
    """Convert MP3 to WAV 44.1k stereo via ffmpeg."""
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(mp3_path), "-ar", "44100", "-ac", "2", str(wav_path)],
            check=True, capture_output=True, timeout=30,
        )
        return True
    except Exception as e:
        log(f"  ffmpeg convert err: {e}")
        return False


# --- Gemini TTS for male voices (priority over edge-tts) ---
_gemini_male_exhausted = False
_gemini_male_exhausted_at = 0.0
_GEMINI_RETRY_INTERVAL = 300  # retry Gemini every 5 min after exhaustion

# Gemini male voice pool (rotates per persona)
_GEMINI_MALE_VOICES = ["Charon", "Puck", "Fenrir", "Orus", "Gacrux", "Iapetus"]


def _try_gemini_male(text, persona, out_wav):
    """Try Gemini TTS for male voice. Returns True on success, False if exhausted.

    IMPORTANT: Gemini TTS requires Webshare proxy. If proxy fails or is unavailable,
    logs a clear warning and falls back immediately.
    """
    global _gemini_male_exhausted, _gemini_male_exhausted_at

    # If recently exhausted, skip
    if _gemini_male_exhausted and (time.time() - _gemini_male_exhausted_at) < _GEMINI_RETRY_INTERVAL:
        return False

    # Reset if retry interval passed
    if _gemini_male_exhausted:
        _gemini_male_exhausted = False
        log("  [*] re-tentando Gemini TTS masculino...")

    try:
        import gemini_tts

        # Check proxy availability BEFORE trying
        if not gemini_tts.PROXY_ENABLED:
            log("  [!][!][!] PROXY DESLIGADO — Gemini TTS masculino DESATIVADO (precisa de proxy Webshare)")
            log("  [!][!][!] Verifique: GEMINI_TTS_PROXY_ENABLED=1 e secrets/proxies.txt")
            _gemini_male_exhausted = True
            _gemini_male_exhausted_at = time.time()
            return False

        proxy = _load_proxy()
        if not proxy:
            log("  [!][!][!] PROXY NÃO CONFIGURADO — sem proxies.txt ou arquivo vazio")
            log("  [!][!][!] Gemini TTS masculino DESATIVADO, usando edge-tts fallback")
            _gemini_male_exhausted = True
            _gemini_male_exhausted_at = time.time()
            return False

        if gemini_tts._proxy_dead:
            log("  [!][!][!] PROXY MORTO — Webshare caiu ou expirou!")
            log("  [!][!][!] Verifique se a assinatura Webshare ainda está ativa")
            log("  [!][!][!] Gemini TTS masculino DESATIVADO, usando edge-tts fallback")
            _gemini_male_exhausted = True
            _gemini_male_exhausted_at = time.time()
            return False

        # Pick voice based on persona (deterministic)
        idx = hash(persona) % len(_GEMINI_MALE_VOICES)
        gemini_voice = _GEMINI_MALE_VOICES[idx]

        log(f"  -> gemini-tts voice={gemini_voice} persona={persona} text={text[:50]!r}")
        ok = gemini_tts.speak(text, voice=gemini_voice, out_wav=str(out_wav), max_attempts=3)

        if ok and out_wav.exists() and out_wav.stat().st_size > 1000:
            log(f"  [OK] gemini-tts wrote {out_wav.name} ({out_wav.stat().st_size // 1024} KB)")
            return True

        # Failed — mark as exhausted
        _gemini_male_exhausted = True
        _gemini_male_exhausted_at = time.time()
        log("  [!] Gemini TTS quota esgotada — fallback edge-tts por 5 min")
        return False

    except Exception as e:
        log(f"  [!][!][!] ERRO Gemini TTS: {e}")
        log(f"  [!][!][!] Se for erro de proxy/conexão, verifique Webshare (pode ter expirado)")
        _gemini_male_exhausted = True
        _gemini_male_exhausted_at = time.time()
        return False


def speak(text, voice="pt-BR-FranciscaNeural", out_wav=None, max_attempts=3, persona=""):
    """Generate TTS audio. Drop-in replacement for gemini_tts.speak().

    Returns True on success, False on failure.

    For MALE voices: tries Gemini TTS first (better quality), falls back to edge-tts
    if all Gemini models/keys are exhausted.
    For FEMALE voices: edge-tts directly (already excellent quality).
    """
    global _direct_blocked, _direct_blocked_at, _webshare_consecutive_fails

    text = (text or "").strip()
    if len(text) < 2:
        return False

    # Pre-process: fix foreign words pronunciation
    text = _portuguesify(text)

    out_wav = Path(out_wav)

    # --- MALE voice routing based on TTS_ENGINE ---
    if voice == "pt-BR-AntonioNeural" and persona not in ("Narrador", "Narradora"):
        engine_mode = os.environ.get("TTS_ENGINE", "edge")

        if engine_mode == "gemini":
            # Modo Gemini: Gemini -> ElevenLabs -> PARA (zero edge-tts)
            gemini_ok = _try_gemini_male(text, persona, out_wav)
            if gemini_ok:
                return True
            # ElevenLabs fallback
            try:
                import elevenlabs_tts
                el_ok = elevenlabs_tts.speak(text, persona=persona, out_wav=str(out_wav))
                if el_ok:
                    return True
            except Exception as e:
                log(f"  ElevenLabs indisponivel: {e}")
            log(f"  X Gemini+ElevenLabs falharam - PARANDO (modo gemini, sem edge)")
            return False

        else:
            # Modo Edge: SÓ edge-tts (sem Gemini, sem ElevenLabs)
            pass  # cai pro edge-tts abaixo

    # --- Edge-TTS (primary for female, fallback for male) ---
    profile = _get_voice_profile(voice, persona)
    rate = profile["rate"]
    pitch = profile["pitch"]

    tmp_mp3 = out_wav.with_suffix(".tmp.mp3")

    try:
        # Should we retry direct?
        if _direct_blocked and (time.time() - _direct_blocked_at) > _DIRECT_RETRY_INTERVAL:
            log("  [*] testando IP direto novamente...")
            _direct_blocked = False

        for attempt in range(max_attempts):
            if not _direct_blocked:
                # Try direct
                log(f"  -> edge-tts direct voice={voice} text={text[:60]!r}")
                ok = _try_generate(text, voice, str(tmp_mp3), use_proxy=False, rate=rate, pitch=pitch)
                if ok:
                    _webshare_consecutive_fails = 0
                    if _convert_mp3_to_wav(str(tmp_mp3), str(out_wav)):
                        log(f"  [OK] wrote {out_wav.name} ({out_wav.stat().st_size // 1024} KB)")
                        return True
                else:
                    # Direct failed -> block it
                    _direct_blocked = True
                    _direct_blocked_at = time.time()
                    log("  [!] IP direto bloqueado, mudando pra Webshare")

            # Try with Webshare proxy
            if _webshare_consecutive_fails >= _MAX_WEBSHARE_FAILS:
                log("  [X] Webshare falhou demais — PARANDO pra proteger IP")
                return False

            proxy = _load_proxy()
            if not proxy:
                log("  [X] sem proxy configurado e IP direto bloqueado")
                return False

            log(f"  -> edge-tts proxy voice={voice} text={text[:60]!r}")
            ok = _try_generate(text, voice, str(tmp_mp3), use_proxy=True, rate=rate, pitch=pitch)
            if ok:
                _webshare_consecutive_fails = 0
                if _convert_mp3_to_wav(str(tmp_mp3), str(out_wav)):
                    log(f"  [OK] wrote {out_wav.name} ({out_wav.stat().st_size // 1024} KB) [via proxy]")
                    return True
            else:
                _webshare_consecutive_fails += 1
                log(f"  [!] Webshare falhou ({_webshare_consecutive_fails}/{_MAX_WEBSHARE_FAILS})")
                if _webshare_consecutive_fails >= _MAX_WEBSHARE_FAILS:
                    log("  [X] PARANDO — Webshare atingiu limite de falhas")
                    return False
                time.sleep(2)

        return False
    finally:
        if tmp_mp3.exists():
            tmp_mp3.unlink()


def list_voices():
    return VOICES_PREBUILT


# Compatibility with gemini_tts interface
def mark_key_error(kid): pass
def mark_key_ok(kid): pass
def bump_key_fila(kid): pass
def pick_gemini_key(): return (0, "edge-tts")


# --- CLI ---
def main():
    p = argparse.ArgumentParser(description="edge-tts engine (drop-in replacement for gemini_tts)")
    p.add_argument("--text", help="Text to synthesize")
    p.add_argument("--voice", default="pt-BR-FranciscaNeural", help=f"Voice. Options: {', '.join(VOICES_PREBUILT)}")
    p.add_argument("--out", help="Output .wav file")
    p.add_argument("--persona", help="Persona name (maps to voice automatically)")
    p.add_argument("--gender", choices=["M", "F"])
    p.add_argument("--list-voices", action="store_true")
    args = p.parse_args()

    if args.list_voices:
        for v in VOICES_PREBUILT:
            print(v)
        return

    if not args.text:
        print("--text required")
        sys.exit(1)

    voice = args.voice
    if args.persona:
        voice = voice_for_persona(args.persona, gender=args.gender)

    out = args.out or "output.wav"
    ok = speak(args.text, voice=voice, out_wav=out)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
