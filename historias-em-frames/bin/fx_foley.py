# -*- coding: utf-8 -*-
"""fx_foley.py — áudio de cena (foley gap) + enhance da narração.
prepare_foley_gap_audio (FOLEY_GAP_MODE), enhance_narration_audio.

Parte do motor de efeitos — mapa completo na fachada effects_engine.py.
Split mecânico verbatim do _PRE_SPLIT_effects_engine.py.bak (2026-07-04).
"""
import random
import subprocess
import os
import re
from pathlib import Path
from fx_detect import _valid_audio




# ── Toggle GAP do foley (env HIPER_FOLEY_GAP) ────────────────────────────────
# LIGADO (1): o foley contextual (campainha/porta/passos...) PAUSA a voz —
#   atrasa a fala, o som toca limpo nesse início, depois a voz continua. Igual
#   à "pausa" das transições, não atropela a fala.
# DESLIGADO (0): o foley toca JUNTO com a voz desde t=0 (de fundo).
FOLEY_GAP_MODE = os.environ.get("HIPER_FOLEY_GAP", "0").strip().lower() in ("1", "true", "yes", "on")
FOLEY_GAP_S = 0.7  # atraso aplicado à voz no modo gap


def prepare_foley_gap_audio(voice_audio, foley_file, out_audio, vol=0.9):
    """Modo GAP: gera um novo wav onde a VOZ é atrasada FOLEY_GAP_S e o foley
    toca limpo nesse início (volume cheio), depois entra a fala. O clip fica
    ~FOLEY_GAP_S mais longo (build_clip deriva a duração do áudio). Retorna o
    caminho do áudio gerado, ou o áudio original se falhar."""
    if not _valid_audio(foley_file) or not Path(voice_audio).exists():
        return str(voice_audio)
    delay_ms = int(FOLEY_GAP_S * 1000)
    norm = "loudnorm=I=-16:TP=-1.5," if os.environ.get("SFX_LOUDNORM", "1") != "0" else ""
    fc = (
        f"[0:a]adelay={delay_ms}|{delay_ms},apad=pad_dur=0.1[v];"
        f"[1:a]{norm}volume={vol}[f];"
        f"[f][v]amix=inputs=2:duration=longest:dropout_transition=0:normalize=0[a]"
    )
    cmd = [
        "ffmpeg", "-y", "-i", str(voice_audio), "-i", str(foley_file),
        "-filter_complex", fc, "-map", "[a]",
        "-c:a", "pcm_s16le", "-ar", "44100", "-ac", "2", str(out_audio),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=60)
        return str(out_audio) if Path(out_audio).exists() else str(voice_audio)
    except Exception:
        return str(voice_audio)


def enhance_narration_audio(wav_in, wav_out=None):
    """Pós-processamento de áudio profissional na narração TTS.

    Aplica (portado do n8n V5.1 GLOBAL_CONFIG.audio):
    - Loudness normalization (LUFS -16, true peak -1.5)
    - Compression leve (threshold -18dB, ratio 3:1)
    - Noise reduction sutil (afftdn)
    - De-esser (highshelf eq sutil)

    Se wav_out não fornecido, sobrescreve o arquivo original.
    """
    if wav_out is None:
        wav_out = wav_in
    tmp_out = Path(str(wav_in) + "_enhanced.wav")

    af_chain = ",".join([
        "afftdn=nf=-20",
        "acompressor=threshold=-18dB:ratio=3:attack=5:release=50",
        "equalizer=f=7000:t=h:w=2000:g=-2",
        "loudnorm=I=-16:TP=-1.5:LRA=11"
    ])

    cmd = [
        "ffmpeg", "-y", "-i", str(wav_in),
        "-af", af_chain,
        "-ar", "44100", "-ac", "1",
        str(tmp_out),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=15)
        if tmp_out.exists() and tmp_out.stat().st_size > 100:
            tmp_out.replace(wav_out)
            return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        if tmp_out.exists():
            tmp_out.unlink(missing_ok=True)
    return False
