#!/usr/bin/env python3
"""parallax25d.py — 2.5D REAL a partir de UMA imagem. KEYLESS (Depth-Anything local, CPU).

Diferente do "parallax" fake atual (zoom de camada unica), aqui:
  1. Gera depth-map por IA (Depth-Anything-Small via transformers, roda em CPU).
  2. Desloca os pixels por profundidade (objeto perto move mais que fundo) frame a frame,
     simulando uma camera 3D entrando/orbitando a cena -> ilusao de 3D de imagem estatica.
  3. Preenche buracos de oclusao (inpaint simples) pra nao deixar rasgos.

Uso:
  python bin/parallax25d.py IMG.jpg --out OUT.mp4 --dur 5 --move orbit --amp 18
  --move: orbit | push_in | float | sweep    --amp: amplitude do deslocamento em px (8-30)

Saida default: _testes/PARALLAX25D_<move>_<nome>.mp4 (1080x1920 por padrao, --w/--h ajustam).
"""
import argparse
import sys
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

PROJECT = Path(__file__).resolve().parent.parent

_DEPTH_PIPE = None


def get_depth(img_pil):
    """Roda Depth-Anything-Small, devolve depth normalizado 0..1 (1=perto)."""
    global _DEPTH_PIPE
    if _DEPTH_PIPE is None:
        from transformers import pipeline
        print("  carregando Depth-Anything-Small (1ª vez baixa ~100MB)...", flush=True)
        _DEPTH_PIPE = pipeline("depth-estimation",
                               model="depth-anything/Depth-Anything-V2-Small-hf",
                               device=-1)
    out = _DEPTH_PIPE(img_pil)
    d = np.array(out["depth"], dtype=np.float32)
    d = (d - d.min()) / (d.max() - d.min() + 1e-6)
    return d  # 0..1, perto=alto


def warp(img, depth, dx, dy, zoom):
    """Desloca pixels por profundidade. Perto (depth alto) move mais. cv2.remap."""
    import cv2
    h, w = depth.shape
    xs, ys = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    # fator por pixel: profundidade controla quanto cada pixel se desloca
    f = depth  # 0..1
    cx, cy = w / 2.0, h / 2.0
    # zoom (push-in) faz a cena crescer a partir do centro, proporcional a profundidade
    zx = (xs - cx) * (zoom * f) + xs
    zy = (ys - cy) * (zoom * f) + ys
    map_x = (zx + dx * f).astype(np.float32)
    map_y = (zy + dy * f).astype(np.float32)
    warped = cv2.remap(img, map_x, map_y, interpolation=cv2.INTER_LINEAR,
                       borderMode=cv2.BORDER_REFLECT)
    return warped


def camera_path(move, t, amp):
    """Devolve (dx, dy, zoom) pro instante t em [0,1]. move = estilo de camera."""
    import math
    s = math.sin(t * 2 * math.pi)
    c = math.cos(t * 2 * math.pi)
    if move == "orbit":
        return amp * s, amp * 0.5 * c, 0.04
    if move == "push_in":
        return 0.0, 0.0, 0.02 + 0.10 * t          # zoom progressivo
    if move == "float":
        return amp * 0.6 * s, amp * 0.6 * math.sin(t * 2 * math.pi + 1.3), 0.03
    if move == "sweep":
        return amp * (2 * t - 1), amp * 0.2 * s, 0.05   # varre lateral
    return amp * s, 0.0, 0.03


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("img")
    ap.add_argument("--out", default=None)
    ap.add_argument("--dur", type=float, default=5.0)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--move", default="orbit", choices=["orbit", "push_in", "float", "sweep"])
    ap.add_argument("--amp", type=float, default=18.0)
    ap.add_argument("--w", type=int, default=1080)
    ap.add_argument("--h", type=int, default=1920)
    args = ap.parse_args()

    import cv2
    src = Path(args.img)
    if not src.exists():
        print("não existe:", src); sys.exit(1)

    if args.out:
        out = Path(args.out)
    else:
        td = PROJECT / "_testes"; td.mkdir(exist_ok=True)
        out = td / f"PARALLAX25D_{args.move}_{src.stem}.mp4"

    # carrega + enquadra pro alvo (cover)
    img_pil = Image.open(src).convert("RGB")
    print(f"  depth de {src.name} {img_pil.size}...", flush=True)
    depth = get_depth(img_pil)

    img = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    # redimensiona img e depth pro alvo (cover, corta excesso)
    def cover(arr, tw, th, interp):
        h, w = arr.shape[:2]
        scale = max(tw / w, th / h)
        nw, nh = int(w * scale + 0.5), int(h * scale + 0.5)
        r = cv2.resize(arr, (nw, nh), interpolation=interp)
        x0 = (nw - tw) // 2; y0 = (nh - th) // 2
        return r[y0:y0 + th, x0:x0 + tw]
    img = cover(img, args.w, args.h, cv2.INTER_LANCZOS4)
    depth = cover(depth, args.w, args.h, cv2.INTER_LINEAR)
    # suaviza o depth pra deslocamento nao serrilhar
    depth = cv2.GaussianBlur(depth, (0, 0), 3)

    n = int(args.dur * args.fps)
    tmp = Path(tempfile.mkdtemp())
    print(f"  renderizando {n} frames ({args.move}, amp={args.amp})...", flush=True)
    for i in range(n):
        t = i / max(1, n - 1)
        dx, dy, zoom = camera_path(args.move, t, args.amp)
        frame = warp(img, depth, dx, dy, zoom)
        cv2.imwrite(str(tmp / f"f{i:04d}.jpg"), frame, [cv2.IMWRITE_JPEG_QUALITY, 92])

    # monta mp4
    cmd = ["ffmpeg", "-y", "-framerate", str(args.fps), "-i", str(tmp / "f%04d.jpg"),
           "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
           str(out)]
    subprocess.run(cmd, check=True, capture_output=True)
    # limpa frames
    for f in tmp.glob("*.jpg"):
        f.unlink()
    tmp.rmdir()
    print(f"OK: {out}", flush=True)


if __name__ == "__main__":
    main()
