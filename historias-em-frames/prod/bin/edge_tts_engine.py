# COMUM — fonte única: D:\hipercool-materiais\comum\edge_tts_engine.py. Mudou esta cópia? python D:\hipercool-materiais\bin\recursos.py subir edge_tts_engine.py --de <projeto>
"""edge_tts_engine.py — Drop-in replacement for gemini_tts using edge-tts (free, no API key).

Provides the same public API: speak(), voice_for_persona(), VOICES_*, etc.
Uses Webshare proxy as intelligent fallback when direct IP is blocked.
"""
import asyncio
import os
import subprocess
import sys
import time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")
import json
import argparse
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
SECRETS = PROJECT_DIR / "secrets"
PROXY_LIST_FILE = SECRETS / "proxies.txt"

# --- Voices ---
# PROIBIDAS (dono 15/10): pt-BR-AntonioNeural, pt-BR-FranciscaNeural, it-IT-IsabellaNeural
# Multilingual aprovadas: falam qualquer língua, qualidade aprovada pelo dono (mesma troca do historias-em-frames)
VOICES_FEMALE = ["pt-BR-ThalitaMultilingualNeural", "en-US-AvaMultilingualNeural", "en-US-EmmaMultilingualNeural"]
VOICES_MALE = ["en-US-AndrewMultilingualNeural", "en-US-BrianMultilingualNeural", "en-AU-WilliamMultilingualNeural"]
NARRATOR_VOICES = {"hipercool": "pt-BR-ThalitaMultilingualNeural", "manhwa": "pt-BR-ThalitaMultilingualNeural", "broll": "pt-BR-ThalitaMultilingualNeural"}
VOICES_PREBUILT = VOICES_FEMALE + VOICES_MALE
# Trava (postador, 16/10): se alguma config antiga ainda pedir uma proibida, _generate_edge_tts troca pela aprovada
# na hora da chamada — o edge-tts nunca fala com elas.
VOZES_PROIBIDAS = {"pt-BR-FranciscaNeural": "pt-BR-ThalitaMultilingualNeural",
                   "pt-BR-AntonioNeural": "en-US-AndrewMultilingualNeural",
                   "it-IT-IsabellaNeural": "pt-BR-ThalitaMultilingualNeural"}

SENSUAL_STYLE_PREFIX = ""

VOICES_REGISTRY = PROJECT_DIR / "workspace" / "voices-registry.json"

# --- Voice profiles (rate/pitch per role) ---
# --- Virtual voices registry (3 base voices × rate/pitch = many personas) ---
# O pipeline escolhe persona (Narrador, Mulher, Homem, etc.)
# Este registro mapeia automaticamente pra voz + parâmetros.
# Variedade: personas diferentes recebem perfis diferentes pra soar como vozes distintas.

VIRTUAL_VOICES = {
    # === FEMININAS (Thalita base) ===
    "thalita_normal":    {"voice": "pt-BR-ThalitaMultilingualNeural", "rate": "+0%",  "pitch": "+0Hz"},
    "thalita_aguda":     {"voice": "pt-BR-ThalitaMultilingualNeural", "rate": "+5%",  "pitch": "+8Hz"},
    "thalita_grave":     {"voice": "pt-BR-ThalitaMultilingualNeural", "rate": "+0%",  "pitch": "-5Hz"},
    "thalita_rapida":    {"voice": "pt-BR-ThalitaMultilingualNeural", "rate": "+15%", "pitch": "+0Hz"},
    "thalita_madura":    {"voice": "pt-BR-ThalitaMultilingualNeural", "rate": "-8%",  "pitch": "-8Hz"},
    "thalita_doce":      {"voice": "pt-BR-ThalitaMultilingualNeural", "rate": "-3%",  "pitch": "+12Hz"},
    # === FEMININAS (Ava/Emma base) ===
    "ava_normal":        {"voice": "en-US-AvaMultilingualNeural", "rate": "+0%",  "pitch": "+0Hz"},
    "ava_aguda":         {"voice": "en-US-AvaMultilingualNeural", "rate": "+0%",  "pitch": "+8Hz"},
    "ava_grave":         {"voice": "en-US-AvaMultilingualNeural", "rate": "+0%",  "pitch": "-5Hz"},
    "ava_rapida":        {"voice": "en-US-AvaMultilingualNeural", "rate": "+15%", "pitch": "+3Hz"},
    "ava_sussurro":      {"voice": "en-US-AvaMultilingualNeural", "rate": "-5%",  "pitch": "+10Hz"},
    "ava_animada":       {"voice": "en-US-AvaMultilingualNeural", "rate": "+20%", "pitch": "+6Hz"},
    "emma_normal":       {"voice": "en-US-EmmaMultilingualNeural", "rate": "+0%",  "pitch": "+0Hz"},
    "emma_lenta":        {"voice": "en-US-EmmaMultilingualNeural", "rate": "-10%", "pitch": "-3Hz"},
    # === MASCULINAS (Andrew/Brian/William base) ===
    "andrew_normal":     {"voice": "en-US-AndrewMultilingualNeural", "rate": "+0%",  "pitch": "+0Hz"},
    "andrew_acelerado":  {"voice": "en-US-AndrewMultilingualNeural", "rate": "+20%", "pitch": "+3Hz"},
    "andrew_grave":      {"voice": "en-US-AndrewMultilingualNeural", "rate": "+10%", "pitch": "-5Hz"},
    "andrew_agudo":      {"voice": "en-US-AndrewMultilingualNeural", "rate": "+15%", "pitch": "+8Hz"},
    "brian_normal":      {"voice": "en-US-BrianMultilingualNeural", "rate": "+0%",  "pitch": "+0Hz"},
    "brian_jovem":       {"voice": "en-US-BrianMultilingualNeural", "rate": "+25%", "pitch": "+10Hz"},
    "brian_meio":        {"voice": "en-US-BrianMultilingualNeural", "rate": "+15%", "pitch": "+0Hz"},
    "william_normal":    {"voice": "en-AU-WilliamMultilingualNeural", "rate": "+0%",  "pitch": "+0Hz"},
    "william_lento":     {"voice": "en-AU-WilliamMultilingualNeural", "rate": "-5%",  "pitch": "-8Hz"},
}

# Pools por gênero pra atribuição automática
_FEMALE_POOL = [
    "thalita_normal", "thalita_aguda", "thalita_grave", "thalita_rapida",
    "thalita_madura", "thalita_doce",
    "ava_normal", "ava_aguda", "ava_grave", "ava_rapida",
    "ava_sussurro", "ava_animada",
    "emma_normal", "emma_lenta",
]
_MALE_POOL = [
    "andrew_normal", "andrew_acelerado", "andrew_grave", "andrew_agudo",
    "brian_normal", "brian_jovem", "brian_meio",
    "william_normal", "william_lento",
]
_NARRATOR_PROFILE = {"voice": "pt-BR-ThalitaMultilingualNeural", "rate": "+5%", "pitch": "+0Hz"}

# ─── ARQUÉTIPOS VOCAIS (historias, Feature #5) ──────────────────────────────
# Papel narrativo -> perfil vocal (o story_writer pode emitir 'arquetipo_vocal' por personagem).
VOCAL_ARCHETYPES = {
    "mentor": {"voice": "en-US-AndrewMultilingualNeural", "rate": "-10%", "pitch": "-8Hz"},
    "sabio": {"voice": "en-US-AndrewMultilingualNeural", "rate": "-10%", "pitch": "-8Hz"},
    "vilao": {"voice": "en-US-AndrewMultilingualNeural", "rate": "+10%", "pitch": "+5Hz"},
    "misterioso": {"voice": "en-US-AndrewMultilingualNeural", "rate": "-5%", "pitch": "-3Hz"},
    "jovem_heroi": {"voice": "en-US-BrianMultilingualNeural", "rate": "+5%", "pitch": "+3Hz"},
    "jovem_heroina": {"voice": "pt-BR-ThalitaMultilingualNeural", "rate": "+0%", "pitch": "+5Hz"},
    "comico": {"voice": "en-US-AvaMultilingualNeural", "rate": "+20%", "pitch": "+6Hz"},
    "crianca": {"voice": "pt-BR-ThalitaMultilingualNeural", "rate": "+10%", "pitch": "+15Hz"},
    "idoso": {"voice": "en-AU-WilliamMultilingualNeural", "rate": "-15%", "pitch": "-10Hz"},
    "idosa": {"voice": "en-US-AvaMultilingualNeural", "rate": "-12%", "pitch": "-6Hz"},
    "autoritario": {"voice": "en-US-AndrewMultilingualNeural", "rate": "+5%", "pitch": "-5Hz"},
    "sedutor": {"voice": "pt-BR-ThalitaMultilingualNeural", "rate": "-5%", "pitch": "-2Hz"},
    "assustado": {"voice": "pt-BR-ThalitaMultilingualNeural", "rate": "+15%", "pitch": "+8Hz"},
    "narrador_grave": {"voice": "pt-BR-ThalitaMultilingualNeural", "rate": "+0%", "pitch": "-4Hz"},
    "narrador_empolgado": {"voice": "pt-BR-ThalitaMultilingualNeural", "rate": "+15%", "pitch": "+4Hz"},
}

# Mapeamento antigo pra compatibilidade
VOICE_PROFILES = {
    "narrator": _NARRATOR_PROFILE,
    "female":   VIRTUAL_VOICES["thalita_normal"],
    "male":     VIRTUAL_VOICES["andrew_normal"],
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
_webshare_exhausted_at = 0.0      # quando o pool inteiro falhou (0 = nunca)
_WEBSHARE_COOLDOWN = 120          # após esgotar o pool, espera isto antes de re-tentar (s)

# --- Roteador de proxy (rotaciona pro próximo quando um falha) ---
_proxy_pool = None       # lista de proxies carregada do proxies.txt
_proxy_idx = 0           # índice do proxy atual no pool
_proxy_pool_mtime = 0.0  # mtime do arquivo (recarrega se mudar)

# --- Logging ---
def log(msg):
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    print(f"[{ts}] {msg}", flush=True)


def _load_proxy_pool():
    """Carrega a lista completa de proxies do proxies.txt (recarrega se o arquivo mudar)."""
    global _proxy_pool, _proxy_pool_mtime
    if not PROXY_LIST_FILE.exists():
        _proxy_pool = []
        return _proxy_pool
    mtime = PROXY_LIST_FILE.stat().st_mtime
    if _proxy_pool is None or mtime != _proxy_pool_mtime:
        lines = PROXY_LIST_FILE.read_text().strip().splitlines()
        _proxy_pool = [l.strip() for l in lines if l.strip() and not l.startswith("#")]
        _proxy_pool_mtime = mtime
    return _proxy_pool


def _load_proxy():
    """Retorna o proxy ATUAL do pool (o roteador troca via _rotate_proxy)."""
    pool = _load_proxy_pool()
    if not pool:
        return None
    return pool[_proxy_idx % len(pool)]


def _rotate_proxy():
    """Avança pro próximo proxy do pool (chamado quando o atual falha)."""
    global _proxy_idx
    pool = _load_proxy_pool()
    if not pool:
        return None
    _proxy_idx = (_proxy_idx + 1) % len(pool)
    nxt = pool[_proxy_idx]
    # Loga só o usuário do proxy (sem senha) pra não vazar credencial no log
    _tag = nxt.split("//", 1)[-1].split(":", 1)[0]
    log(f"  [rotaciona] proxy -> {_tag} ({_proxy_idx + 1}/{len(pool)})")
    return nxt


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


def _infer_gender(persona):
    """Infere M/F pelo RÓTULO da persona (o ensemble às vezes manda gender=None p/
    'Rapaz'/'Vice-General' → sem isso caía no default 'F' e todo homem falava com voz feminina)."""
    pl = (persona or "").lower()
    MASC = ("rapaz", "homem", "garoto", "menino", "senhor", "general", "cavaleiro",
            "rei", "príncipe", "principe", "guerreiro", "soldado", "mestre", "lorde",
            "pai", "irmão", "irmao", "tio", "capitão", "capitao", "velho", "cara", "moço", "moco")
    FEM = ("garota", "moça", "moca", "mulher", "menina", "senhora", "dama", "cavaleira",
           "rainha", "princesa", "guerreira", "irmã", "irma", "mãe", "mae", "tia", "velha")
    if any(w in pl for w in MASC):
        return "M"
    if any(w in pl for w in FEM):
        return "F"
    return None


def voice_for_persona(persona, gender=None, kind="hipercool"):
    """Map persona name to edge-tts voice."""
    if persona == "Narrador" or persona == "Narradora":
        return NARRATOR_VOICES.get(kind, "pt-BR-ThalitaMultilingualNeural")

    registry = _persona_registry()
    if persona in registry:
        entry = registry[persona]
        g = entry.get("gender") or gender or _infer_gender(persona) or "F"
    else:
        g = gender or _infer_gender(persona) or "F"
    ROLE_GENDER_MAP = {  # historias: papel do roteiro quando o nome não diz o gênero
        "Protagonista": None,
        "Antagonista": "M",
        "Mentor": "M",
        "Aliado": None,
        "Coadjuvante": None,
    }
    if g is None and persona in ROLE_GENDER_MAP:
        g = ROLE_GENDER_MAP[persona] or "F"

    if g == "M":
        return "en-US-AndrewMultilingualNeural"
    else:
        return "pt-BR-ThalitaMultilingualNeural"


def _get_voice_profile(voice, persona="", archetype=None):
    """Get rate/pitch profile based on voice and persona role.

    Assigns a unique virtual voice per persona name (deterministic via hash).
    Narrator always gets the narrator profile. Other personas get variety from pools.
    Archetype override: if the story_writer provides 'arquetipo_vocal', uses that directly.
    """
    if persona in ("Narrador", "Narradora"):
        return _NARRATOR_PROFILE
    if archetype and archetype in VOCAL_ARCHETYPES:
        return VOCAL_ARCHETYPES[archetype]

    # md5 em vez de hash(): o hash() do Python muda a cada execução e o personagem trocava de voz
    import hashlib
    persona_hash = int(hashlib.md5(persona.encode("utf-8")).hexdigest(), 16)
    if voice in VOICES_MALE:
        idx = persona_hash % len(_MALE_POOL)
        return VIRTUAL_VOICES[_MALE_POOL[idx]]
    else:
        idx = persona_hash % len(_FEMALE_POOL)
        return VIRTUAL_VOICES[_FEMALE_POOL[idx]]


async def _generate_edge_tts(text, voice, out_path, proxy=None, rate="+0%", pitch="+0Hz", contour=None):
    """Run edge-tts async to generate audio.

    MELHORIA (WordBoundary, MoneyPrinterTurbo): em vez de .save() (que descarta o timing),
    consome o stream, escreve o áudio E captura o offset/duração REAL de cada palavra num
    sidecar `<out>.words.json` (usado pra sincronizar a legenda na raiz, sem estimativa).
    Fallback total: se o stream falhar, cai no .save() de sempre (não quebra nada).
    contour: SSML pitch contour string, ex "(0%,+20Hz)(25%,+10Hz)(75%,-5Hz)(100%,-10Hz)".
    """
    import edge_tts
    import json as _json

    if not os.environ.get("VOZ_CLONADA"):  # base da voz clonada: Francisca + clone = pronúncia perfeita (dono 19/10)
        voice = VOZES_PROIBIDAS.get(voice, voice)
    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch, proxy=proxy,
                                        boundary="WordBoundary")
    if contour:
        orig_mkssml = edge_tts.communicate.mkssml
        def _mkssml_contour(tc, escaped_text):
            ssml = orig_mkssml(tc, escaped_text)
            return ssml.replace("<prosody ", f"<prosody contour='{contour}' ", 1)
        edge_tts.communicate.mkssml = _mkssml_contour
    words = []
    try:
        with open(out_path, "wb") as f:
            async for chunk in communicate.stream():
                t = chunk.get("type")
                if t == "audio":
                    f.write(chunk["data"])
                elif t in ("WordBoundary", "SentenceBoundary"):
                    # offset/duration em unidades de 100ns → segundos
                    start = chunk.get("offset", 0) / 1e7
                    dur = chunk.get("duration", 0) / 1e7
                    words.append([round(start, 3), round(start + dur, 3), chunk.get("text", "")])
        # sidecar de timings ao lado do áudio (só se veio algo)
        if words:
            try:
                Path(str(out_path) + ".words.json").write_text(
                    _json.dumps(words, ensure_ascii=False), encoding="utf-8")
            except Exception:
                pass
    except Exception:
        # fallback: método antigo, garante o áudio mesmo sem timings.
        # IMPORTANTE: criar um Communicate NOVO — reusar o que já teve .stream()
        # chamado dispara "stream can only be called once" e mascara o erro real.
        communicate2 = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch, proxy=proxy)
        await communicate2.save(out_path)
    finally:
        if contour:
            edge_tts.communicate.mkssml = orig_mkssml


def _try_generate(text, voice, out_mp3, use_proxy=False, rate="+0%", pitch="+0Hz", contour=None):
    """Attempt to generate audio. Returns True on success, False on failure."""
    # FORCE_DIRECT_TTS=1 força sem proxy (bypass quando proxies estão pagos/quebrados)
    if os.environ.get("FORCE_DIRECT_TTS", "0") == "1":
        use_proxy = False
    proxy = _load_proxy() if use_proxy else None

    try:
        asyncio.run(_generate_edge_tts(text, voice, out_mp3, proxy=proxy, rate=rate, pitch=pitch, contour=contour))
        if Path(out_mp3).exists() and Path(out_mp3).stat().st_size > 500:
            return True
        return False
    except Exception as e:
        log(f"  edge-tts err (proxy={'yes' if use_proxy else 'no'}): {e}")
        return False


def _wav_valido(out_wav, tmp_mp3):
    """historias (17/10): áudio de 0 KB (ffmpeg sem stream, proxy devolvendo lixo) não conta como pronto — apaga e
    deixa o laço tentar de novo."""
    try:
        if out_wav.exists() and out_wav.stat().st_size > 500:
            return True
        for p in (Path(out_wav), Path(str(tmp_mp3) + ".words.json")):
            if p.exists():
                p.unlink()
    except OSError:
        pass
    log("  [WARN] conversão inválida (áudio vazio) — removido e retentando")
    return False


def _move_words_sidecar(tmp_mp3, out_wav):
    """Move o sidecar de timing (WordBoundary) do tmp_mp3 pro out_wav, no formato que o
    pipeline espera: '<out_wav>.words.json'. O sidecar nasce em '<tmp_mp3>.words.json'
    (dentro de _generate_edge_tts) e o tmp_mp3 é deletado logo depois — sem isto o
    timing REAL se perde e a legenda cai na estimativa (drift).

    Se TRIM_SILENCE=1, o WAV teve o silêncio de cabeça aparado, então os offsets do
    WordBoundary (relativos ao MP3 original) ficam adiantados. Normaliza ancorando a 1ª
    palavra ao buffer de silêncio preservado (~0.08s), preservando o espaçamento relativo."""
    import json as _json
    src = Path(str(tmp_mp3) + ".words.json")
    if not src.exists():
        return
    dst = Path(str(out_wav) + ".words.json")
    try:
        wt = _json.loads(src.read_text(encoding="utf-8"))
        if wt and os.environ.get("TRIM_SILENCE", "0") == "1":
            shift = wt[0][0] - 0.08  # tira o silêncio de cabeça aparado, mantém 0.08 de buffer
            if shift > 0:
                wt = [[max(0.0, w[0] - shift), max(0.0, w[1] - shift), w[2]] for w in wt]
        dst.write_text(_json.dumps(wt, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass
    finally:
        try:
            src.unlink()
        except Exception:
            pass


def _convert_mp3_to_wav(mp3_path, wav_path):
    """Convert MP3 to WAV 44.1k stereo via ffmpeg.

    MELHORIA (auto-editor, #5): TRIM_SILENCE=1 apara o silêncio das PONTAS (leading+trailing)
    da locução, preservando pausas internas — narração menos "esperando" voz que não vem.
    Threshold conservador (-40dB) pra não comer voz baixa. Default OFF (comportamento igual)."""
    af = []
    if os.environ.get("TRIM_SILENCE", "0") == "1":
        # silenceremove nas 2 pontas: início (start_) e fim (stop_, via reverse+silenceremove+reverse)
        af = ["-af",
              "silenceremove=start_periods=1:start_silence=0.08:start_threshold=-40dB:detection=peak,"
              "areverse,"
              "silenceremove=start_periods=1:start_silence=0.08:start_threshold=-40dB:detection=peak,"
              "areverse"]
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(mp3_path), *af, "-ar", "44100", "-ac", "2", str(wav_path)],
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
        log("  [retry] re-tentando Gemini TTS masculino...")

    try:
        import gemini_tts

        # Check proxy availability BEFORE trying
        if not gemini_tts.PROXY_ENABLED:
            log("  [WARN] PROXY DESLIGADO — Gemini TTS masculino DESATIVADO")
            log("  [WARN] Verifique: GEMINI_TTS_PROXY_ENABLED=1 e secrets/proxies.txt")
            _gemini_male_exhausted = True
            _gemini_male_exhausted_at = time.time()
            return False

        proxy = _load_proxy()
        if not proxy:
            log("  [WARN] PROXY NÃO CONFIGURADO — sem proxies.txt ou arquivo vazio")
            log("  [WARN] Gemini TTS masculino DESATIVADO, usando edge-tts fallback")
            _gemini_male_exhausted = True
            _gemini_male_exhausted_at = time.time()
            return False

        if gemini_tts._proxy_dead:
            log("  [WARN] PROXY MORTO — Webshare caiu ou expirou!")
            log("  [WARN] Verifique se a assinatura Webshare ainda está ativa")
            log("  [WARN] Gemini TTS masculino DESATIVADO, usando edge-tts fallback")
            _gemini_male_exhausted = True
            _gemini_male_exhausted_at = time.time()
            return False

        # Pick voice based on persona (deterministic)
        idx = int(__import__("hashlib").md5(persona.encode("utf-8")).hexdigest(), 16) % len(_GEMINI_MALE_VOICES)
        gemini_voice = _GEMINI_MALE_VOICES[idx]

        log(f"  -> gemini-tts voice={gemini_voice} persona={persona} text={text[:50]!r}")
        ok = gemini_tts.speak(text, voice=gemini_voice, out_wav=str(out_wav), max_attempts=3)

        if ok and out_wav.exists() and out_wav.stat().st_size > 1000:
            log(f"  [OK] gemini-tts wrote {out_wav.name} ({out_wav.stat().st_size // 1024} KB)")
            return True

        # Failed — mark as exhausted
        _gemini_male_exhausted = True
        _gemini_male_exhausted_at = time.time()
        log("  [WARN] Gemini TTS quota esgotada — fallback edge-tts por 5 min")
        return False

    except Exception as e:
        log(f"  [WARN] ERRO Gemini TTS: {e}")
        log(f"  [WARN] Se for erro de proxy/conexão, verifique Webshare (pode ter expirado)")
        _gemini_male_exhausted = True
        _gemini_male_exhausted_at = time.time()
        return False


def speak(text, voice="pt-BR-ThalitaMultilingualNeural", out_wav=None, max_attempts=3, persona="",
          rate=None, pitch=None, contour=None):
    """Generate TTS audio. Drop-in replacement for gemini_tts.speak().

    Returns True on success, False on failure.
    rate/pitch ("+N%", "+NHz"): por frase, no lugar do perfil da persona (narracao_curva, 17/10).
    contour: SSML pitch contour string, ex "(0%,+20Hz)(50%,+0Hz)(100%,-10Hz)".

    For MALE voices: tries Gemini TTS first (better quality), falls back to edge-tts
    if all Gemini models/keys are exhausted.
    For FEMALE voices: edge-tts directly (already excellent quality).
    """
    global _direct_blocked, _direct_blocked_at, _webshare_consecutive_fails, _webshare_exhausted_at

    text = (text or "").strip()
    if len(text) < 2:
        return False

    # Pre-process: fix foreign words pronunciation
    text = _portuguesify(text)

    out_wav = Path(out_wav)

    # --- MALE voice routing based on TTS_ENGINE ---
    if voice in VOICES_MALE and persona not in ("Narrador", "Narradora"):
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
            # OmniRoute GPT Audio fallback (ultimo antes de parar)
            try:
                import omniroute_tts
                omni_ok = omniroute_tts.speak(text, persona=persona, out_wav=str(out_wav))
                if omni_ok:
                    return True
            except Exception as e:
                log(f"  OmniRoute TTS indisponivel: {e}")
            log(f"  X Gemini+ElevenLabs+OmniRoute falharam - PARANDO (modo gemini)")
            return False

        elif engine_mode == "eleven":
            # Modo Eleven PURO: ElevenLabs only (NÃO toca nas chaves Gemini —
            # usado quando outro agente está consumindo o Gemini). Fallback edge.
            try:
                import elevenlabs_tts
                el_ok = elevenlabs_tts.speak(text, persona=persona, out_wav=str(out_wav))
                if el_ok:
                    return True
                log(f"  ElevenLabs sem resultado (persona={persona}) -> fallback edge")
            except Exception as e:
                log(f"  ElevenLabs indisponivel: {e} -> fallback OmniRoute/edge")
            # OmniRoute GPT Audio antes do edge
            try:
                import omniroute_tts
                omni_ok = omniroute_tts.speak(text, persona=persona, out_wav=str(out_wav))
                if omni_ok:
                    return True
            except Exception as e:
                log(f"  OmniRoute TTS indisponivel: {e}")
            # cai pro edge-tts abaixo

        else:
            # Modo Edge: SÓ edge-tts (sem Gemini, sem ElevenLabs)
            pass  # cai pro edge-tts abaixo

    # --- Edge-TTS (primary for female, fallback for male) ---
    profile = _get_voice_profile(voice, persona)
    rate = rate or profile["rate"]
    pitch = pitch or profile["pitch"]

    tmp_mp3 = out_wav.with_suffix(".tmp.mp3")

    try:
        # edge-tts é keyless: tenta IP DIRETO primeiro e só cai pro Webshare se
        # o direto for bloqueado. EDGE_TTS_FORCE_PROXY=1 volta ao comportamento
        # antigo (tudo via proxy) caso o IP local esteja na blacklist da MS.
        if os.environ.get("EDGE_TTS_FORCE_PROXY", "0") == "1":
            _direct_blocked = True

        # Tentativas: se o IP direto está bloqueado, dá pra percorrer o pool inteiro
        # de proxies (1 tentativa por proxy) em vez de parar em max_attempts.
        _pool_sz = len(_load_proxy_pool())
        _n_attempts = max(max_attempts, _pool_sz + 1) if _pool_sz else max_attempts
        for attempt in range(_n_attempts):
            if not _direct_blocked:
                # Try direct
                log(f"  -> edge-tts direct voice={voice} text={text[:60]!r}")
                ok = _try_generate(text, voice, str(tmp_mp3), use_proxy=False, rate=rate, pitch=pitch, contour=contour)
                if ok:
                    _webshare_consecutive_fails = 0
                    if _convert_mp3_to_wav(str(tmp_mp3), str(out_wav)):
                        if _wav_valido(out_wav, tmp_mp3):  # historias: rejeita áudio 0 KB (ffmpeg sem stream)
                            _move_words_sidecar(tmp_mp3, out_wav)
                            log(f"  [OK] wrote {out_wav.name} ({out_wav.stat().st_size // 1024} KB)")
                            return True
                else:
                    # Direct failed → block it
                    _direct_blocked = True
                    _direct_blocked_at = time.time()
                    log("  [WARN] IP direto bloqueado, mudando pra Webshare")

            # Try with Webshare proxy — ROTEADOR: percorre o pool inteiro antes de desistir.
            _pool = _load_proxy_pool()
            if not _pool:
                log("  [ERR] sem proxy configurado e IP direto bloqueado")
                return False
            # Limite = tamanho do pool (dá pra tentar cada proxy uma vez antes de parar).
            _fail_cap = max(_MAX_WEBSHARE_FAILS, len(_pool))
            if _webshare_consecutive_fails >= _fail_cap:
                # Pool esgotou. NÃO desiste pra sempre (era o bug que fazia o
                # pipeline pular centenas de frases numa queda transitória de
                # rede): marca o instante, espera o cooldown e ZERA o contador
                # pra dar nova chance aos proxies (que costumam voltar sozinhos).
                now = time.time()
                if _webshare_exhausted_at == 0.0:
                    _webshare_exhausted_at = now
                waited = now - _webshare_exhausted_at
                if waited < _WEBSHARE_COOLDOWN:
                    restante = _WEBSHARE_COOLDOWN - waited
                    log(f"  [WARN] pool de proxies esgotado — cooldown {restante:.0f}s "
                        f"antes de re-tentar (rede pode voltar)")
                    time.sleep(min(restante, 15))
                    # continua o loop: na volta, se o cooldown já passou, reseta abaixo
                    continue
                # Cooldown cumprido: reseta e tenta o pool de novo.
                log(f"  [INFO] cooldown de {_WEBSHARE_COOLDOWN}s cumprido — re-tentando proxies")
                _webshare_consecutive_fails = 0
                _webshare_exhausted_at = 0.0

            proxy = _load_proxy()
            log(f"  -> edge-tts proxy voice={voice} text={text[:60]!r}")
            ok = _try_generate(text, voice, str(tmp_mp3), use_proxy=True, rate=rate, pitch=pitch, contour=contour)
            if ok:
                _webshare_consecutive_fails = 0
                if _convert_mp3_to_wav(str(tmp_mp3), str(out_wav)) and _wav_valido(out_wav, tmp_mp3):
                    _move_words_sidecar(tmp_mp3, out_wav)
                    log(f"  [OK] wrote {out_wav.name} ({out_wav.stat().st_size // 1024} KB) [via proxy]")
                    return True
            else:
                _webshare_consecutive_fails += 1
                log(f"  [WARN] Proxy falhou ({_webshare_consecutive_fails}/{_fail_cap})")
                _rotate_proxy()  # troca pro próximo proxy do pool e tenta de novo
                if _webshare_consecutive_fails >= _fail_cap:
                    log("  [ERR] PARANDO — pool de proxies esgotado")
                    return False
                time.sleep(1)

        # Ultimo recurso pra vozes masculinas: OmniRoute GPT Audio
        if voice in VOICES_MALE and persona not in ("Narrador", "Narradora"):
            try:
                import omniroute_tts
                omni_ok = omniroute_tts.speak(text, persona=persona, out_wav=str(out_wav))
                if omni_ok:
                    return True
            except Exception:
                pass

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
    p.add_argument("--voice", default="pt-BR-ThalitaMultilingualNeural", help=f"Voice. Options: {', '.join(VOICES_PREBUILT)}")
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
