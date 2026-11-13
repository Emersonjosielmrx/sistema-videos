# -*- coding: utf-8 -*-
"""auto_validate.py — Validação avançada de vídeos gerados.

Checa: duração, tamanho, desync áudio/vídeo, frames pretos, silêncio,
bitrate, resolução. Retorna lista de warnings + move pra quarentena se grave.
"""
import os
import subprocess
import shutil
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
from hp_common import QUARANTINE_DIR  # em hipercool-materiais (saida do projeto)
QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)


def _ffprobe(path, *args):
    try:
        cmd = ["ffprobe", "-v", "error"] + list(args) + [str(path)]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        return r.stdout.strip()
    except Exception:
        return ""


def _duration(path):
    v = _ffprobe(path, "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1")
    try:
        return float(v)
    except (ValueError, TypeError):
        return 0.0


def _audio_duration(path):
    v = _ffprobe(path, "-select_streams", "a", "-show_entries", "stream=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1")
    try:
        return float(v.splitlines()[0])
    except (ValueError, TypeError, IndexError):
        return 0.0


def _video_duration(path):
    v = _ffprobe(path, "-select_streams", "v", "-show_entries", "stream=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1")
    try:
        return float(v.splitlines()[0])
    except (ValueError, TypeError, IndexError):
        return _duration(path)


def _resolution(path):
    v = _ffprobe(path, "-select_streams", "v:0", "-show_entries", "stream=width,height",
                 "-of", "csv=p=0:s=x")
    return v


def _detect_silence(path, threshold=-40, min_duration=3.0):
    """Detecta trechos de silêncio > min_duration segundos."""
    try:
        cmd = [
            "ffmpeg", "-i", str(path), "-af",
            f"silencedetect=noise={threshold}dB:d={min_duration}",
            "-f", "null", "-"
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        import re
        silences = re.findall(r"silence_duration: ([\d.]+)", r.stderr)
        return [float(s) for s in silences]
    except Exception:
        return []


def _detect_black_frames(path, threshold=0.1, min_duration=1.0):
    """Detecta frames pretos > min_duration."""
    try:
        cmd = [
            "ffmpeg", "-i", str(path), "-vf",
            f"blackdetect=d={min_duration}:pix_th={threshold}",
            "-f", "null", "-"
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        import re
        blacks = re.findall(r"black_duration:([\d.]+)", r.stderr)
        return [float(b) for b in blacks]
    except Exception:
        return []


def validate(video_path, min_duration=15, max_desync=2.0):
    """Valida um vídeo. Retorna dict com status e warnings.

    Returns:
        {"valid": bool, "warnings": list[str], "fatal": list[str], "info": dict}
    """
    path = Path(video_path)
    if not path.exists():
        return {"valid": False, "warnings": [], "fatal": ["Arquivo não existe"], "info": {}}

    warnings = []
    fatal = []
    info = {}

    # Duração
    dur = _duration(video_path)
    info["duration"] = dur
    if dur < min_duration:
        fatal.append(f"Muito curto ({dur:.1f}s < {min_duration}s)")
    elif dur < 30:
        warnings.append(f"Curto ({dur:.1f}s)")

    # Tamanho
    size_mb = path.stat().st_size / (1024 * 1024)
    info["size_mb"] = round(size_mb, 1)
    if size_mb < 1:
        fatal.append(f"Arquivo minúsculo ({size_mb:.1f}MB)")
    elif size_mb < 3:
        warnings.append(f"Arquivo pequeno ({size_mb:.1f}MB)")

    # Desync áudio/vídeo
    a_dur = _audio_duration(video_path)
    v_dur = _video_duration(video_path)
    if a_dur > 0 and v_dur > 0:
        desync = abs(a_dur - v_dur)
        info["desync"] = round(desync, 2)
        if desync > max_desync:
            fatal.append(f"Desync áudio/vídeo ({desync:.1f}s)")
        elif desync > 1.0:
            warnings.append(f"Desync leve ({desync:.1f}s)")

    # Bitrate
    if dur > 0:
        bitrate_kbps = (size_mb * 8 * 1024) / dur
        info["bitrate_kbps"] = round(bitrate_kbps)
        if bitrate_kbps < 150:
            warnings.append(f"Bitrate muito baixo ({bitrate_kbps:.0f}kbps)")

    # Resolução
    res = _resolution(video_path)
    info["resolution"] = res
    if res and "x" in res:
        w, h = res.split("x")
        if int(w) < 640 or int(h) < 480:
            warnings.append(f"Resolução baixa ({res})")

    # Silêncio
    silences = _detect_silence(video_path)
    if silences:
        total_silence = sum(silences)
        info["silence_segments"] = len(silences)
        info["silence_total"] = round(total_silence, 1)
        if total_silence > dur * 0.3:
            warnings.append(f"Muito silêncio ({total_silence:.0f}s / {dur:.0f}s)")
        elif any(s > 10 for s in silences):
            warnings.append(f"Gap de silêncio longo ({max(silences):.0f}s)")

    # Frames pretos
    blacks = _detect_black_frames(video_path)
    if blacks:
        info["black_segments"] = len(blacks)
        if any(b > 2.0 for b in blacks):
            warnings.append(f"Frames pretos ({len(blacks)} trechos)")

    valid = len(fatal) == 0
    return {"valid": valid, "warnings": warnings, "fatal": fatal, "info": info}


def validate_and_quarantine(video_path):
    """Valida e move pra quarentena se fatal. Retorna resultado."""
    result = validate(video_path)
    if not result["valid"]:
        dest = QUARANTINE_DIR / Path(video_path).name
        try:
            shutil.copy2(str(video_path), str(dest))
            result["quarantined"] = str(dest)
        except Exception:
            pass
    return result
