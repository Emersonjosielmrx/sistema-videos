# -*- coding: utf-8 -*-
"""ambient_sound.py — Sound design ambiente por genero.

Mapeia generos a SFX ambientais de fundo (loops sutis a -30 LUFS).
Separado da trilha dinamica (fx_music) — e uma camada atmosferica extra.
"""
import os
import random
import subprocess
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
AMBIENT_DIR = PROJECT_DIR / "workspace" / "assets" / "ambient"
AMBIENT_DIR.mkdir(parents=True, exist_ok=True)

# Mapeamento genero -> keywords de busca nos assets existentes
GENRE_AMBIENT = {
    "terror": ["wind", "creaking", "heartbeat", "drone", "horror_ambient"],
    "romance": ["rain", "piano_ambient", "soft_pad", "gentle"],
    "misterio": ["clock", "drone", "low_hum", "tension_ambient"],
    "superacao": ["uplifting_pad", "ambient_warm", "inspiration"],
    "motivacional": ["uplifting_pad", "ambient_warm", "inspiration"],
    "drama": ["strings_ambient", "emotional_pad", "rain"],
    "comedia": ["light_ambient", "cheerful_bg", "birds"],
    "fantasia": ["magical_ambient", "ethereal", "forest"],
    "religioso": ["choir_ambient", "sacred_pad", "bells_distant"],
    "curiosidades": ["neutral_pad", "tech_ambient", "subtle_beat"],
    "acao": ["tension_ambient", "pulse", "engine_hum"],
}

# Volume alvo muito baixo — e background sutil, nao concorre com narracao/trilha
TARGET_LUFS = float(os.environ.get("AMBIENT_LUFS", "-30"))


def _find_ambient_file(genero):
    """Busca um arquivo de ambient na pasta de assets. Fallback pra qualquer .mp3/.wav."""
    keywords = GENRE_AMBIENT.get(genero, ["ambient", "pad"])

    # Busca em ambient/ primeiro
    candidates = []
    for ext in ("*.mp3", "*.wav", "*.ogg"):
        candidates.extend(AMBIENT_DIR.glob(ext))

    if not candidates:
        # Fallback: buscar na pasta de trilhas por algo ambient
        trilhas_dir = PROJECT_DIR / "workspace" / "assets" / "trilhas"
        if trilhas_dir.exists():
            for ext in ("*.mp3", "*.wav", "*.ogg"):
                candidates.extend(trilhas_dir.glob(ext))

    if not candidates:
        return None

    # Tentar match por keyword
    for kw in keywords:
        matches = [c for c in candidates if kw.lower() in c.stem.lower()]
        if matches:
            return random.choice(matches)

    # Fallback: qualquer arquivo ambient
    return random.choice(candidates) if candidates else None


def get_ambient_track(genero, duration_s, out_path=None):
    """Seleciona e loopa um ambient pro genero, ajustado pra duration_s.

    Retorna path do arquivo gerado (ambient loopado + normalizado a -30 LUFS).
    Retorna None se nao encontrar assets ou ENV AMBIENT_ENABLED=0.
    """
    if os.environ.get("AMBIENT_ENABLED", "0") != "1":
        return None

    ambient_file = _find_ambient_file(genero)
    if not ambient_file:
        return None

    if out_path is None:
        from hp_common import TMP_DIR
        out_path = str(TMP_DIR / f"ambient_{genero}_{int(duration_s)}s.wav")

    out_path = str(out_path)

    # Loop o arquivo pra cobrir a duracao completa + normaliza volume
    try:
        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", "-1", "-i", str(ambient_file),
            "-t", f"{duration_s:.2f}",
            "-af", (
                f"loudnorm=I={TARGET_LUFS}:TP=-3:LRA=7,"
                f"afade=t=in:d=2.0,"
                f"afade=t=out:st={max(0, duration_s - 3.0):.2f}:d=3.0"
            ),
            "-ar", "44100", "-ac", "2",
            out_path
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=120)
        if result.returncode == 0 and Path(out_path).exists():
            return out_path
    except Exception:
        pass

    return None


def mix_ambient_into_video(video_path, ambient_path, out_path):
    """Mixa o ambient track no video existente como camada extra (baixo volume)."""
    if not ambient_path or not Path(ambient_path).exists():
        return False

    try:
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-i", str(ambient_path),
            "-filter_complex",
            "[1:a]volume=0.15[amb];[0:a][amb]amix=inputs=2:duration=first:dropout_transition=2[aout]",
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            str(out_path)
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=300)
        return result.returncode == 0 and Path(out_path).exists()
    except Exception:
        return False
