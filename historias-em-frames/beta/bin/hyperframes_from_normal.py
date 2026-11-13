# -*- coding: utf-8 -*-
"""hyperframes_from_normal.py — Deriva variante HyperFrames do vídeo normal (ZERO IA).

Pega o vídeo normal já renderizado e aplica o tratamento HyperFrames (filtros
estilizados, overlays, color grading cinematográfico) sem regerar áudio/narração.
Reusa 100% do áudio original — só a camada visual muda.

Uso:
  python bin/hyperframes_from_normal.py --input workspace/videos/genero/story_id/v1_FINAL.mp4 \
      --output workspace/videos/genero/story_id/v1_HYPERFRAMES.mp4

O HyperFrames é mais "cinematográfico" — grading + overlay + vinheta pesada.
"""
import os
import sys
import argparse
import shutil
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hp_common import PROJECT_DIR, TMP_DIR, log

# HyperFrames visual presets (aplicados como filtros ffmpeg)
HYPERFRAMES_STYLES = {
    "cinematic": (
        "curves=preset=cross_process,"
        "eq=brightness=0.03:saturation=1.3:contrast=1.1,"
        "unsharp=5:5:0.8,"
        "vignette=PI/4"
    ),
    "noir": (
        "eq=brightness=-0.05:saturation=0.3:contrast=1.4,"
        "curves=preset=darker,"
        "vignette=PI/3.5"
    ),
    "warm": (
        "colorbalance=rs=0.1:gs=0.05:bs=-0.1:rm=0.05,"
        "eq=saturation=1.2:contrast=1.05,"
        "vignette=PI/5"
    ),
    "cool": (
        "colorbalance=rs=-0.08:gs=0.0:bs=0.12:rm=-0.05:bm=0.08,"
        "eq=saturation=1.1:contrast=1.1,"
        "vignette=PI/4.5"
    ),
    "vintage": (
        "curves=preset=vintage,"
        "noise=alls=8:allf=t,"
        "eq=saturation=0.8:contrast=1.15,"
        "vignette=PI/3"
    ),
}

DEFAULT_STYLE = os.environ.get("HYPERFRAMES_STYLE", "cinematic")


def derive_hyperframes(input_path, output_path=None, style=None):
    """Aplica tratamento HyperFrames ao vídeo normal.

    Args:
        input_path: path do vídeo normal
        output_path: path de saída (default: mesmo dir, sufixo _HYPERFRAMES)
        style: nome do estilo (cinematic, noir, warm, cool, vintage)

    Returns:
        Path do vídeo gerado ou None se falhou
    """
    input_path = Path(input_path)
    if not input_path.exists():
        log(f"Input nao existe: {input_path}")
        return None

    style = style or DEFAULT_STYLE
    vf = HYPERFRAMES_STYLES.get(style, HYPERFRAMES_STYLES["cinematic"])

    if output_path:
        out = Path(output_path)
    else:
        out = input_path.with_name(input_path.stem.replace("_FINAL", "") + "_HYPERFRAMES.mp4")

    out.parent.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    tmp_out = TMP_DIR / f"hf_{out.name}"

    log(f"HyperFrames: {input_path.name} → {out.name} (style={style})")

    cmd = [
        "ffmpeg", "-y", "-i", str(input_path),
        "-vf", vf,
        "-c:v", "libx264", "-crf", "20", "-preset", "medium",
        "-c:a", "copy",
        "-movflags", "+faststart",
        str(tmp_out),
    ]

    try:
        r = subprocess.run(cmd, capture_output=True, timeout=300)
        if tmp_out.exists() and tmp_out.stat().st_size > 10000:
            shutil.move(str(tmp_out), str(out))
            size_mb = out.stat().st_size / (1024 * 1024)
            log(f"  OK: {out.name} ({size_mb:.1f}MB)")
            return out
        else:
            log(f"  FAIL: output vazio ou muito pequeno")
            stderr = r.stderr.decode(errors="replace")[-200:]
            log(f"  stderr: {stderr}")
            return None
    except subprocess.TimeoutExpired:
        log("  FAIL: timeout (300s)")
        return None
    except Exception as e:
        log(f"  FAIL: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Derive HyperFrames from normal video")
    parser.add_argument("--input", "-i", required=True, help="Video normal de entrada")
    parser.add_argument("--output", "-o", default=None, help="Video de saida")
    parser.add_argument("--style", "-s", default=DEFAULT_STYLE,
                        choices=list(HYPERFRAMES_STYLES.keys()),
                        help=f"Estilo visual (default: {DEFAULT_STYLE})")
    args = parser.parse_args()

    result = derive_hyperframes(args.input, args.output, args.style)
    if result:
        print(f"OK: {result}")
    else:
        print("FALHOU")
        sys.exit(1)


if __name__ == "__main__":
    main()
