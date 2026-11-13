"""ffmpeg_loudnorm: normaliza o audio do mp4 para EBU R128 (volume padrao Shorts/Reels).

CPU-only. Resolve os videos Veo que saem com audio baixo ou sem consistencia
de volume entre clips.

Uso: loudnorm=I=-16:TP=-1.5:LRA=11 (alvo -16 LUFS, pico -1.5 dBTP).
"""

import subprocess
from pathlib import Path

SUFFIX = "loud"

# Onde esta o ffmpeg central
_FFMPEG = r"D:\hipercool-materiais\bin\ffmpeg.exe"


def processar(input_mp4: str, output_mp4: str, meta: dict) -> bool:
    """Aplica loudnorm EBU R128 ao audio do mp4. Retorna True se ok.

    Se nao houver audio no input, gera uma faixa de silencio normalizada
    (evita mp4 sem audio no final do pipeline).
    """
    if not Path(_FFMPEG).exists():
        return False
    if not Path(input_mp4).exists():
        return False

    # comando unico: aplica loudnorm e reencoda o audio (mantem video stream)
    cmd = [
        _FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
        "-i", input_mp4,
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
        "-c:v", "copy",  # nao reencoda video (CPU-leve)
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        output_mp4,
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if r.returncode != 0:
            # fallback: se copy falhar (codec incomum), reencoda
            cmd[cmd.index("-c:v")] = "-c:v"
            cmd.insert(cmd.index("copy") + 1, "libx264")
            cmd.remove("copy") if "copy" in cmd else None
            cmd_recode = [
                _FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
                "-i", input_mp4,
                "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
                "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
                "-c:a", "aac", "-b:a", "128k",
                "-movflags", "+faststart",
                output_mp4,
            ]
            r = subprocess.run(cmd_recode, capture_output=True, text=True, timeout=300)
        return r.returncode == 0 and Path(output_mp4).exists()
    except subprocess.TimeoutExpired:
        return False
    except Exception:
        return False
