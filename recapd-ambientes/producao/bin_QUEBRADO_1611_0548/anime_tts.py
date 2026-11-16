"""anime_tts.py — narração TTS pro anime-pipeline.

Módulo pequeno e isolado. Só faz uma coisa: pegar uma frase e gerar o .wav
da narração (voz narradora Francisca, keyless via edge-tts). Usa cache: se o
.wav já existe, não regera (protege quota/tempo).

DUAS CAMADAS DE PROTECAO ANTI-BAN:
  1. anime_script.py — suaviza termos de strike ANTES de salvar o roteiro.
  2. anime_tts.py  — SEGUNDA camada: anti-ban TAMBÉM aqui (proteção dupla).
     Se por algum motivo o roteiro gravado contiver termos de risco, o TTS
     não os lê. Gírias virais disponiveis via VIRAL_SLANG=1.
"""
import logging
import os
import sys
from pathlib import Path

# viralizador.py vive no mesmo diretório
sys.path.insert(0, str(Path(__file__).resolve().parent))

import edge_tts_engine
import viralizador

NARRATOR_VOICE = "pt-BR-FranciscaNeural"


def narrate(text, out_wav):
    """Gera (ou reusa) a narração de uma frase.

    Retorna o Path do .wav em caso de sucesso, ou None se o TTS falhar.
    Cache: se out_wav já existe, retorna direto sem chamar o TTS.

    Duas camadas anti-ban: o texto ja passa por anime_script.anti_ban() antes
    de chegar aqui, mas esta funcao aplica mais uma vez por seguranca.
    """
    out_wav = Path(out_wav)

    if out_wav.exists() and out_wav.stat().st_size > 500:
        return out_wav

    # ── SEGUNDA CAMADA anti-ban: garante que nenhum termo de risco chegue ao TTS ──
    safe_text = viralizador.anti_ban(text)
    if os.environ.get("VIRAL_SLANG") == "1":
        safe_text = viralizador.viralizar(safe_text)

    ok = edge_tts_engine.speak(safe_text, voice=NARRATOR_VOICE,
                               out_wav=str(out_wav), persona="Narrador")
    if not ok:
        logging.error(f"[anime_tts] TTS falhou: {text[:60]!r}")
        return None

    return out_wav
