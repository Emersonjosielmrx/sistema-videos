# -*- coding: utf-8 -*-
"""tts_stage.py — GERAÇÃO DE VOZ (TTS) + cache de áudio. Split da -fix.

Transforma TEXTO em ÁUDIO (.wav). Motor por TTS_ENGINE (edge default/keyless ou gemini).
Tudo via cache (protege quota). TTS_CACHE_ONLY=1 → não chama motor em cache-miss.
Público: tts_panel, _infer_gender_by_name. Depende de tts_cache + hp_common.
"""
import os
import subprocess
import time
from pathlib import Path

# Mesmo motor condicional do pipeline (edge keyless por padrão; gemini gasta quota).
if os.environ.get("TTS_ENGINE", "edge") == "gemini":
    import gemini_tts as gemini_tts
else:
    import edge_tts_engine as gemini_tts
from _tts_filter import clean_for_tts
import tts_cache
from hp_common import PROJECT_DIR, log


# ─── TTS com cache (reaproveitamento de falas) ────────────────────────────────
TTS_CACHE_DIR = PROJECT_DIR / "material" / "tts_cache"


def _voice_context(persona, text):
    """Detecta contexto da fala pra efeito de áudio (Ponto L)."""
    blob = f"{persona or ''} {text or ''}".lower()
    if any(k in blob for k in ["(pensando)", "pensando", "pensamento", "internamente",
                               "na mente", "em pensamento", "voz interior", "pensa consigo"]):
        return "thought"
    if any(k in blob for k in ["(telefone)", "telefone", "celular", "ligação", "ligacao",
                               "no telefone", "pelo telefone", "(rádio)", "(radio)",
                               "walkie", "interfone"]):
        return "phone"
    return None


def _apply_voice_context(wav_path, persona, text):
    """Aplica filtro de áudio conforme o contexto: eco (pensamento) / banda (telefone)."""
    ctx = _voice_context(persona, text)
    if not ctx:
        return
    af = {
        # eco suave + brilho reduzido = pensamento/voz interior
        "thought": "aecho=0.8:0.88:55|95:0.35|0.2,lowpass=f=7500",
        # banda estreita estilo telefone/rádio
        "phone": "highpass=f=500,lowpass=f=2700,volume=1.35",
    }[ctx]
    wav_path = Path(wav_path)
    tmp = wav_path.with_suffix(".fx.wav")
    try:
        subprocess.run(["ffmpeg", "-y", "-i", str(wav_path), "-af", af, str(tmp)],
                       check=True, capture_output=True, timeout=30)
        tmp.replace(wav_path)
        log(f"  🎚️ voz [{ctx}] aplicada")
    except Exception:
        if tmp.exists():
            tmp.unlink()


_MALE_NAME_HINTS = (
    "homem", "rapaz", "garoto", "menino", "moço", "moco", "cara", "dono",
    "chef", "senhor", "sr.", "pai", "irmão", "irmao", "filho", "amigo",
    "colega", "tio", "avô", "avo", "rei", "príncipe", "principe", "bêbado",
    "bebado", "professor", "chefe", "patrão", "patrao", "guarda", "policial",
    "min-hyuk", "minhyuk", "tae-yong", "yong", "man", "boy", "guy", "mr",
)


_FEMALE_NAME_HINTS = (
    "mulher", "garota", "menina", "moça", "moca", "senhora", "sra.", "mãe",
    "mae", "irmã", "irma", "filha", "tia", "avó", "rainha", "princesa",
    "namorada", "esposa", "amiga", "professora", "chefa", "woman", "girl",
    "lady", "miss", "yeol-mae", "yeolmae", "na-yul", "nayul", "jovem",
)


def _infer_gender_by_name(persona):
    """Retorna 'M'/'F'/None inferido pelo nome da persona (sem rede).
    Match por palavra-chave; nomes próprios conhecidos da obra inclusos."""
    if not persona:
        return None
    p = persona.lower().strip()
    for h in _MALE_NAME_HINTS:
        if h in p:
            return "M"
    for h in _FEMALE_NAME_HINTS:
        if h in p:
            return "F"
    return None


def tts_panel(text, wav_path, persona="Narrador", gender=None, sensual=False, force_tts=False):
    """Gera áudio TTS pra um painel. Usa cache pra reusar falas já geradas.

    sensual=True prefixa uma instrução de estilo sedutora/sussurrada (obra +18).
    O texto enviado (com ou sem prefixo) é o que define a chave de cache, então
    as versões sensual e normal são cacheadas separadamente.

    Inclui retry com rotação de voz: se a voz de personagem falha, tenta Kore (neutro).
    """
    import shutil
    cleaned = clean_for_tts(text)
    if not cleaned or len(cleaned) < 2:
        log(f"  ⚠ Texto muito curto após limpeza, pulando TTS: {text[:40]}")
        return False

    # Texto final pro TTS (define a chave de cache). Sensual prefixa diretiva de estilo.
    tts_text = (gemini_tts.SENSUAL_STYLE_PREFIX + cleaned) if sensual else cleaned

    # MODO CACHE-ONLY (env TTS_CACHE_ONLY=1): usado pela FÁBRICA DE VÍDEO. Na fase
    # de vídeo NÃO se pode chamar o Gemini — fala sem cache NÃO é gerada ao vivo
    # (travava o render na quota 429). Cache-miss → return False → clip rápido.
    # A voz de verdade é responsabilidade da fábrica de áudio (serial).
    cache_only = os.environ.get("TTS_CACHE_ONLY", "").strip().lower() in ("1", "true", "yes", "on")

    # MODO GEMINI_MALE_ONLY (env GEMINI_MALE_ONLY=1): a FASE 2 do fluxo. Roda com
    # base edge (TTS_ENGINE=edge), então narrador (Francisca PT nativa) e personagens
    # FEMININAS reusam o cache da fase 1 SEM regenerar (0 quota). Só as vozes
    # MASCULINAS — que no edge são o Antonio robótico — são trocadas pela voz
    # premium do Gemini. Fallback: se o Gemini falhar na fala masculina, mantém a edge.
    male_only = os.environ.get("GEMINI_MALE_ONLY", "").strip().lower() in ("1", "true", "yes", "on")
    is_male = (gender or "").upper() == "M"
    if male_only:
        if is_male:
            try:
                import gemini_tts as _greal   # módulo premium real (independe do base engine)
                mvoice = _greal.voice_for_persona(persona, gender="M", kind="hipercool")
                found_m = tts_cache.lookup_premium_first(TTS_CACHE_DIR, tts_text, mvoice, "M")
                if found_m and not force_tts:
                    shutil.copy2(found_m, wav_path)
                    log(f"  TTS: {persona} ({mvoice}) [MALE->premium] — [CACHE] {cleaned[:45]}...")
                    _apply_voice_context(wav_path, persona, text)
                    return True
                log(f"  TTS: {persona} ({mvoice}) [MALE->premium Gemini] — {cleaned[:45]}...")
                ok_m = _greal.speak(tts_text, voice=mvoice, out_wav=wav_path)
                if ok_m and Path(wav_path).exists():
                    shutil.copy2(wav_path, tts_cache.store_path(TTS_CACHE_DIR, tts_text, mvoice, "M"))
                    _apply_voice_context(wav_path, persona, text)
                    return True
                log("  ⚠ Gemini falhou na voz masculina -> fallback edge (Antonio)")
            except Exception as _e:
                log(f"  ⚠ GEMINI_MALE_ONLY erro ({_e}) -> fallback edge")
            # se chegou aqui, cai no fluxo normal (edge) abaixo
        else:
            # narrador/feminina: NÃO regenera — reusa o cache da fase edge (equivale a cache-only)
            cache_only = True

    # Vozes do personagem e narrador (fallback)
    voice = gemini_tts.voice_for_persona(persona, gender=gender, kind="hipercool")
    fallback_voice = "Kore"  # Voz padrão do narrador como fallback

    for attempt, (current_persona, current_voice) in enumerate([
        (persona, voice),
        ("Narrador", fallback_voice) # Segunda tentativa: voz neutra
    ]):
        # Cache híbrido por similaridade (bin/tts_cache.py): mesma voz reusa o texto
        # normalizado; frases curtas/comuns reusam por gênero (nunca cruza gênero).
        # O gênero vem da PRÓPRIA voz (consistência); lookup tenta chave nova → antiga (compat).
        vgender = "F" if gemini_tts._is_female(current_voice) else "M"
        # Lookup PREMIUM-FIRST: se a mesma fala (mesmo gênero) já existe gravada
        # em voz premium (Gemini/ElevenLabs), reusa ela mesmo no modo edge — voz
        # melhor de graça. Senão, usa o cache da própria voz. Gênero nunca cruza.
        found = tts_cache.lookup_premium_first(TTS_CACHE_DIR, tts_text, current_voice, vgender)
        if found and not force_tts:
            shutil.copy2(found, wav_path)
            log(f"  TTS: {current_persona} ({current_voice}){' [SENSUAL]' if sensual else ''} — [CACHE] {cleaned[:50]}...")
            _apply_voice_context(wav_path, persona, text)
            return True

        if cache_only:
            # cache-miss no modo vídeo: NÃO chama Gemini. Tenta o fallback de voz
            # (que pode estar em cache) e, se nada, desiste → clip rápido.
            if attempt == 0:
                continue
            log(f"  ⏭️ [CACHE-ONLY] fala sem cache, pulando TTS (sem gastar Gemini): {cleaned[:40]}...")
            return False

        log(f"  TTS: {current_persona} ({current_voice}){' [SENSUAL]' if sensual else ''} — {cleaned[:50]}...")
        ok = gemini_tts.speak(tts_text, voice=current_voice, out_wav=wav_path)

        if ok and Path(wav_path).exists():
            shutil.copy2(wav_path, tts_cache.store_path(TTS_CACHE_DIR, tts_text, current_voice, vgender))
            _apply_voice_context(wav_path, persona, text)
            return True

        if attempt == 0:
            log(f"  ⚠ TTS falhou com voz '{current_voice}', tentando fallback '{fallback_voice}'...")
            time.sleep(1)  # Pequena pausa antes do retry

    log(f"  ⚠ TTS falhou EM AMBAS as vozes ({voice} e {fallback_voice})")
    return False

