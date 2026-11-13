#!/usr/bin/env python3
"""parallax_engine.py — movimento real (parallax 2.5D) nos painéis do hipercool.

Substitui o Ken Burns por parallax baseado em DEPTH MAP real (Depth-Anything V2, CPU).
Separa o painel em 3 camadas por profundidade e move cada uma em velocidade diferente
→ sensação de câmera entrando numa cena 3D.

CACHE: reusa o MESMO cache que o MotionFrames (D:\\hipercool-motionframes\\cache\\depth)
já popula em background. O depth (etapa cara ~20s) é cacheado por md5 do CONTEÚDO da
imagem → painel idêntico = 1 depth só, compartilhado entre cópias/máquinas.

FALLBACK TOTAL: qualquer falha (modelo, depth, ffmpeg) → retorna False e o caller usa
o build_clip (Ken Burns) de sempre. NUNCA trava o pipeline.

A duração do clip casa EXATO com a do áudio (o concat força durs_eff; drift = ruído).
"""
import hashlib
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

# Cache de depth COMPARTILHADO com o MotionFrames (não duplicar trabalho do cron).
_MF_CACHE = Path(os.environ.get(
    "MOTIONFRAMES_DEPTH_CACHE",
    r"D:\hipercool-motionframes\cache\depth"))
_MODEL = "depth-anything/Depth-Anything-V2-Small-hf"
ALGO_VER = 1  # bump invalida lógica (não o depth, que é estável)

_pipe = None


def log(m):
    print(f"[parallax] {m}", file=sys.stderr, flush=True)


def _md5_file(p, chunk=1 << 20):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def _get_pipe():
    global _pipe
    if _pipe is None:
        from transformers import pipeline
        t0 = time.time()
        _pipe = pipeline("depth-estimation", model=_MODEL)
        log(f"modelo carregado {time.time()-t0:.1f}s")
    return _pipe


def get_depth(img_path, target_wh):
    """Retorna PIL.Image L do depth, do cache se houver, senão calcula e cacheia.
    target_wh = (W,H) do vídeo final. O depth é salvo na resolução do vídeo."""
    W, H = target_wh
    try:
        md5 = _md5_file(img_path)
    except Exception:
        md5 = None
    cache_png = (_MF_CACHE / f"{md5}.png") if md5 else None
    if cache_png and cache_png.exists() and cache_png.stat().st_size > 0:
        try:
            d = Image.open(cache_png).convert("L")
            if d.size != (W, H):
                d = d.resize((W, H))
            return d
        except Exception:
            pass  # cache corrompido → recalcula
    # calcula
    img = Image.open(img_path).convert("RGB").resize((W, H))
    d = _get_pipe()(img)["depth"].convert("L")
    if cache_png:
        try:
            _MF_CACHE.mkdir(parents=True, exist_ok=True)
            d.save(cache_png)
        except Exception:
            pass
    return d


def _fit(img_path, W, H):
    img = Image.open(img_path).convert("RGB")
    img = img.resize((W, int(W * img.height / img.width)))
    if img.height < H:
        img = img.resize((int(H * img.width / img.height), H))
    return img.crop((0, 0, W, H)) if img.size != (W, H) else img


def build_parallax_clip(img_path, audio_path, out_path, duration=None,
                        W=720, H=1280, fps=30, terror=False):
    """Gera o clip de parallax 2.5D. duration: se None, lê do áudio.
    terror=True adiciona atmosfera (vinheta/grão/tom frio). Retorna True/False."""
    t0 = time.time()
    try:
        if duration is None:
            r = subprocess.run(
                ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                 "-of", "csv=p=0", str(audio_path)],
                capture_output=True, text=True, timeout=10)
            duration = float(r.stdout.strip())
        duration = max(duration, 1.2)

        img = _fit(img_path, W, H)
        depth = get_depth(img_path, (W, H))
        d = np.asarray(depth, dtype=np.float32) / 255.0

        base = Path(out_path).with_suffix("")
        layers = []
        for name, lo, hi in [("far", 0.0, 0.4), ("mid", 0.4, 0.7), ("near", 0.7, 1.01)]:
            mask = ((d >= lo) & (d < hi)).astype(np.uint8) * 255
            m = Image.fromarray(mask).filter(ImageFilter.GaussianBlur(6))
            rgba = img.convert("RGBA")
            rgba.putalpha(m)
            p = f"{base}_pl_{name}.png"
            rgba.save(p)
            layers.append(p)

        speed = [0.5, 1.1, 2.0]
        inputs, fc = [], []
        for i, p in enumerate(layers):
            inputs += ["-loop", "1", "-i", p]
            s = speed[i]
            z = 1.05 + 0.015 * i
            bw, bh = int(W * z * 1.1), int(H * z * 1.1)
            fc.append(
                f"[{i}:v]scale={bw}:{bh},crop={W}:{H}:"
                f"'(in_w-{W})/2+{s*6:.1f}*sin(2*PI*t/8)':"
                f"'(in_h-{H})/2+{s*3.5:.1f}*sin(2*PI*t/11)'[l{i}]")
        fc.append("[l0][l1]overlay=0:0[m1]")
        fc.append("[m1][l2]overlay=0:0[stk]")
        if terror:
            fc.append(
                "[stk]eq=saturation=0.55:contrast=1.12:brightness=-0.04,"
                "colorbalance=rs=-0.03:gs=0:bs=0.06,vignette=PI/4.5,"
                "noise=alls=11:allf=t[vout]")
        else:
            fc.append("[stk]null[vout]")

        cmd = ["ffmpeg", "-y", *inputs, "-i", str(audio_path),
               "-filter_complex", ";".join(fc),
               "-map", "[vout]", "-map", f"{len(layers)}:a",
               "-t", f"{duration:.3f}", "-r", str(fps),
               "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
               "-preset", "veryfast", "-threads", "4",
               "-c:a", "aac", "-b:a", "128k", "-shortest", str(out_path)]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        for p in layers:
            try:
                Path(p).unlink()
            except Exception:
                pass
        if r.returncode != 0:
            log(f"ffmpeg falhou: {r.stderr[-400:]}")
            return False
        ok = Path(out_path).exists() and Path(out_path).stat().st_size > 0
        if ok:
            log(f"clip {Path(img_path).name} {time.time()-t0:.1f}s (dur {duration:.2f}s)")
        return ok
    except Exception as e:
        log(f"erro ({type(e).__name__}: {str(e)[:80]}) → fallback Ken Burns")
        return False
