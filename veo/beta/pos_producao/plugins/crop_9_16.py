"""crop_9_16: garante que o mp4 final esta em 9:16 sem tarja preta.

CPU-only. Veo as vezes retorna clips com letterbox horizontal; este plugin
faz pad + crop inteligente para encher 1080x1920 sem distorcer.

Estrategia:
  - Se w/h ja eh ~9:16: pula.
  - Se muito largo: crop central para 9:16.
  - Se alto estreito: pad lateral preto para 9:16.
"""

import subprocess
from pathlib import Path

SUFFIX = "crop9x16"
_FFMPEG = r"D:\hipercool-materiais\bin\ffmpeg.exe"
_W, _H = 1080, 1920


def processar(input_mp4: str, output_mp4: str, meta: dict) -> bool:
    if not Path(_FFMPEG).exists() or not Path(input_mp4).exists():
        return False
    w, h = meta.get("w"), meta.get("h")
    if not w or not h:
        return False
    ratio = w / h
    target = _W / _H  # 0.5625
    if abs(ratio - target) < 0.02:
        # Ja esta em 9:16 (todo clipe do Veo: 720x1280): so redimensiona.
        # BUG ate 15/10/2026: fazia "pad=1080:1920,scale=1080:1920" — o pad
        # criava uma moldura preta em volta do quadro 720x1280 e o scale esticava
        # a moldura inteira, deixando o video num quadrinho com ~45% da tela
        # perdida em preto (conferido em quadros). Em 9:16 nao ha o que preencher.
        vf = f"scale={_W}:{_H}:flags=lanczos"
    elif ratio > target:
        # muito largo: crop central para 9:16
        new_w = int(h * target)
        vf = f"crop={new_w}:{h}:(iw-{new_w})/2:0,scale={_W}:{_H}"
    else:
        # muito alto: pad lateral
        new_w = int(h * target)
        vf = f"pad={new_w}:{h}:(iw-{new_w})/2:0,scale={_W}:{_H}"

    cmd = [
        _FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
        "-i", input_mp4,
        "-vf", vf,
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
        "-c:a", "copy",
        "-movflags", "+faststart",
        output_mp4,
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=240)
        return r.returncode == 0 and Path(output_mp4).exists()
    except Exception:
        return False
