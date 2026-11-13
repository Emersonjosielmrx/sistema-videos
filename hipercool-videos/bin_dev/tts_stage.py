# -*- coding: utf-8 -*-
"""tts_stage.py — GERAÇÃO DE VOZ (TTS) + cache de áudio.

════════════════════════════════════════════════════════════════════════════
MAPA (feito pra manutenção rápida / modelo grátis)
════════════════════════════════════════════════════════════════════════════
Este módulo transforma TEXTO de narração em ÁUDIO (.wav). É a etapa que mais
esbarra em quota do Gemini (HTTP 429), então TUDO passa por cache: mesma
voz + mesmo texto = reusa o wav do disco, não gasta chamada.

Função principal (a porta que o pipeline usa):
  tts_panel(text, wav_path, persona, gender, sensual, force_tts) -> gera (ou
        reusa do cache) o áudio de UMA fala. Retorna True/False.
        REGRA FIXA: narrador sempre voz Kore (gender=None); ninguém sussurra
        (sensual sempre False no pipeline). Ver CLAUDE.md.

Helpers internos (prefixo _):
  _tts_cache_key(text, voice)      chave do cache (hash do texto+voz).
  _voice_context(persona, text)    deriva tom/contexto da fala.
  _apply_voice_context(...)        aplica ajuste fino no wav gerado.

TTS_CACHE_DIR: pasta do cache de voz (workspace/tts_cache). NÃO apagar —
é o que segura a quota. Re-rodar um cap reaproveita tudo.

Depende de: gemini_tts (motor de voz + rotação de chave em 429), tts_cache
(cache por similaridade), _tts_filter (limpa texto p/ fala), hp_common.
NÃO importa o pipeline -> sem import circular.
════════════════════════════════════════════════════════════════════════════
"""
import subprocess
import os
import hashlib
import time
from pathlib import Path

import gemini_tts
import tts_cache
from _tts_filter import clean_for_tts
from hp_common import PROJECT_DIR, log


# ─── TTS com cache (reaproveitamento de falas) ────────────────────────────────
TTS_CACHE_DIR = PROJECT_DIR / "workspace" / "tts_cache"


def _tts_cache_key(text, voice):
    """Gera hash único pra texto+voz."""
    import hashlib
    key = f"{voice}:{text.strip().lower()}"
    return hashlib.sha256(key.encode()).hexdigest()[:16]


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


def tts_panel(text, wav_path, persona="Narrador", gender=None, sensual=False, force_tts=False):
    """Gera áudio TTS pra um painel. Usa cache pra reusar falas já geradas.

    sensual=True prefixa uma instrução de estilo sedutora/sussurrada (obra +18).
    O texto enviado (com ou sem prefixo) é o que define a chave de cache, então
    as versões sensual e normal são cacheadas separadamente.

    Inclui retry com rotação de voz: se a voz de personagem falha, tenta Kore (neutro).
    Se as duas falham (cota/429), espera com a pausa dinâmica do limitador e tenta de novo.
    """
    cleaned = clean_for_tts(text)
    # fala curta de verdade ("Sim.", "Não!", "Hã?") é fala: só pula o que não tem nem 2 letras
    if not cleaned or sum(ch.isalpha() for ch in cleaned) < 2:
        log(f"  [!] Texto muito curto após limpeza, pulando TTS: {text[:40]}")
        return False

    # MODO CACHE-ONLY (env TTS_CACHE_ONLY=1): usado pela FÁBRICA DE VÍDEO.
    # Na fase de vídeo NÃO se pode chamar o Gemini — se uma fala não está no
    # cache, a gente NÃO gera ao vivo (isso travava o render na quota 429).
    # Retorna False no cache-miss -> o pipeline faz o clip rápido de fallback.
    # A geração de voz de verdade é responsabilidade da fábrica de áudio (serial).
    cache_only = os.environ.get("TTS_CACHE_ONLY", "").strip().lower() in ("1", "true", "yes", "on")

    # Vozes do personagem e narrador (fallback)
    voice = gemini_tts.voice_for_persona(persona, gender=gender, kind="hipercool")
    fallback_voice = "Kore"  # Voz padrão do narrador como fallback

    # Momentos sensuais: prefixar diretiva de estilo
    tts_text = (gemini_tts.SENSUAL_STYLE_PREFIX + cleaned) if sensual else cleaned

    import limitador
    for rodada in range(5):  # falhou nas 2 vozes -> espera (pausa dinâmica do limitador) e tenta de novo
        if rodada:
            pausa = limitador.falhou("tts", f"TTS falhou: {cleaned[:40]}")
            if pausa:
                limitador.esperar("tts")
            else:
                time.sleep(30)
        elif not cache_only:  # só cache (vídeo longo/fábrica de vídeo): não espera pausa de cota
            limitador.esperar("tts")
        r = _tts_rodada(cleaned, tts_text, wav_path, persona, voice, fallback_voice, sensual,
                        force_tts, cache_only, text)
        if r is not None:
            if r:
                limitador.ok("tts")
            return r
    log(f"  [!] TTS falhou EM AMBAS as vozes ({voice} e {fallback_voice}) depois de 5 rodadas")
    return False


def _tts_rodada(cleaned, tts_text, wav_path, persona, voice, fallback_voice, sensual, force_tts,
                cache_only, text):
    """Uma rodada (voz do personagem -> voz neutra). True/False = resolvido; None = as duas falharam."""
    import shutil
    for attempt, (current_persona, current_voice) in enumerate([
        (persona, voice),
        ("Narrador", fallback_voice) # Segunda tentativa: voz neutra
    ]):
        # Cache híbrido por similaridade (bin/tts_cache.py): mesma voz reusa o texto
        # normalizado; frases curtas/comuns reusam por gênero (nunca cruza gênero).
        # O gênero vem da PRÓPRIA voz (consistência); lookup tenta chave nova -> antiga (compat).
        vgender = "F" if gemini_tts._is_female(current_voice) else "M"
        found = tts_cache.lookup(TTS_CACHE_DIR, tts_text, current_voice, vgender)
        if found and not force_tts:
            shutil.copy2(found, wav_path)
            log(f"  TTS: {current_persona} ({current_voice}){' [SENSUAL]' if sensual else ''} — [CACHE] {cleaned[:50]}...")
            _apply_voice_context(wav_path, persona, text)
            return True

        if cache_only:
            # cache-miss no modo vídeo: NÃO chama Gemini. Tenta o fallback de voz
            # (que pode estar em cache) e, se nada, desiste -> clip rápido.
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
            log(f"  [!] TTS falhou com voz '{current_voice}', tentando fallback '{fallback_voice}'...")
            time.sleep(1)  # Pequena pausa antes do retry

    return None

