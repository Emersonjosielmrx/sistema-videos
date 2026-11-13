#!/usr/bin/env python3
"""TESTE ISOLADO de parallax 2.5D — NAO toca no pipeline nem nos renders ativos.
Roda standalone em _testes/parallax/. Mede tempo nesta CPU (i5-8365U, sem GPU).

Estrategia (3 niveis, do mais barato ao mais caro), todos LOCAIS:
  A) parallax "fake depth" por gradiente vertical — zero IA, instantaneo. Baseline.
  B) parallax com depth-map real (Depth-Anything via transformers) — SE instalado.
  C) so mede; nao gera IA pesada.

Gera um MP4 curto e cronometra cada etapa. Uso:
  python test_parallax.py painel.jpg saida.mp4
"""
import sys, time, subprocess
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter

W, H, FPS, DUR = 720, 1280, 24, 4.0   # alvo vertical Shorts


def log(m): print(f"[parallax] {m}", flush=True)


def make_fake_depth(img: Image.Image) -> Image.Image:
    """Depth aproximado SEM IA: combina luminancia + posicao vertical.
    Heuristica: parte de baixo/centro = mais perto (personagem geralmente ao centro).
    Borra forte pra virar um campo suave de profundidade. Instantaneo."""
    g = img.convert("L").resize((W // 4, H // 4))
    arr = np.asarray(g, dtype=np.float32) / 255.0
    h, w = arr.shape
    # gradiente vertical: centro mais "perto"
    yy = np.linspace(0, 1, h)[:, None]
    vert = 1.0 - np.abs(yy - 0.55) * 1.6
    vert = np.clip(vert, 0, 1)
    depth = 0.5 * arr + 0.5 * vert
    depth = (depth - depth.min()) / (np.ptp(depth) + 1e-6)
    d = Image.fromarray((depth * 255).astype(np.uint8)).resize((W, H))
    return d.filter(ImageFilter.GaussianBlur(25))


def try_real_depth(img: Image.Image):
    """Depth-Anything via transformers, se disponivel. Retorna PIL L ou None."""
    try:
        from transformers import pipeline
        t0 = time.time()
        pipe = pipeline("depth-estimation", model="depth-anything/Depth-Anything-V2-Small-hf")
        out = pipe(img.resize((W, H)))
        log(f"  depth real: {time.time()-t0:.1f}s")
        return out["depth"].convert("L")
    except Exception as e:
        log(f"  depth real indisponivel ({type(e).__name__}: {str(e)[:60]}) -> usando fake")
        return None


def render_parallax(panel_path, out_path, use_real=False):
    t_start = time.time()
    img = Image.open(panel_path).convert("RGB")
    # encaixa no canvas vertical preservando proporcao (cover)
    img = img.resize((W, int(W * img.height / img.width)))
    if img.height < H:
        img = img.resize((int(H * img.width / img.height), H))
    img = img.crop((0, 0, W, H)) if img.size != (W, H) else img

    t0 = time.time()
    depth = try_real_depth(img) if use_real else None
    if depth is None:
        depth = make_fake_depth(img)
    log(f"depth: {time.time()-t0:.2f}s ({'real' if use_real and depth else 'fake'})")

    # depth -> mapas de deslocamento X/Y animados via ffmpeg displace.
    # displace usa 2 mapas (xmap,ymap) onde 128=neutro. Deslocamento =
    # (valor-128). Modulamos a amplitude por frame no proprio filtro com sin().
    base = Path(out_path).with_suffix("")
    img.save(f"{base}_rgb.png")
    depth.save(f"{base}_depth.png")

    # constroi xmap/ymap a partir do depth: mais perto (depth alto) desloca mais.
    d = np.asarray(depth, dtype=np.float32) / 255.0  # 0..1
    amp = 18.0  # amplitude maxima de parallax em px
    # xmap neutro 128 + (depth-0.5)*amp ; o sin temporal entra via ffmpeg
    # Como displace nao aceita expr temporal nos mapas, fazemos N mapas? Nao:
    # usamos abordagem de camadas no ffmpeg (zoompan por faixa de depth).
    # -> Estrategia simples e robusta: 3 camadas por limiar de depth.
    layers = []
    for name, lo, hi in [("far", 0.0, 0.4), ("mid", 0.4, 0.7), ("near", 0.7, 1.01)]:
        mask = ((d >= lo) & (d < hi)).astype(np.uint8) * 255
        m = Image.fromarray(mask).filter(ImageFilter.GaussianBlur(6))
        rgba = img.convert("RGBA")
        rgba.putalpha(m)
        p = f"{base}_{name}.png"
        rgba.save(p)
        layers.append((name, p))
    log(f"camadas geradas: {[l[0] for l in layers]} ({time.time()-t0:.2f}s)")

    # ffmpeg: cada camada com zoompan/drift diferente -> parallax.
    # far: drift lento ; near: drift forte (sensacao de profundidade)
    frames = int(DUR * FPS)
    inputs, fc, last = [], [], None
    speed = {"far": 0.6, "mid": 1.3, "near": 2.4}
    for idx, (name, p) in enumerate(layers):
        inputs += ["-loop", "1", "-i", p]
        s = speed[name]
        z = 1.04 + 0.02 * (idx)
        # crop animado (drift) em vez de zoompan: mais leve e sem multiplicar frames.
        # escala a camada um pouco maior e desliza a janela de crop com sin().
        bw, bh = int(W * z), int(H * z)
        fc.append(
            f"[{idx}:v]scale={bw}:{bh},"
            f"crop={W}:{H}:"
            f"'(in_w-{W})/2+{s*7:.1f}*sin(2*PI*t/5)':"
            f"'(in_h-{H})/2+{s*4:.1f}*sin(2*PI*t/7)'[l{idx}]"
        )
    fc.append("[l0][l1]overlay=0:0[m1]")
    fc.append("[m1][l2]overlay=0:0[out]")
    filtergraph = ";".join(fc)
    cmd = ["ffmpeg", "-y", *inputs, "-filter_complex", filtergraph,
           "-map", "[out]", "-t", f"{DUR}", "-r", f"{FPS}",
           "-c:v", "libx264", "-pix_fmt", "yuv420p",
           "-crf", "20", "-preset", "veryfast", "-threads", "4", str(out_path)]
    t_ff = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        log(f"ffmpeg FALHOU: {r.stderr[-500:]}")
        return False
    log(f"ffmpeg render: {time.time()-t_ff:.2f}s")
    log(f"TOTAL: {time.time()-t_start:.2f}s -> {out_path}")
    return True


if __name__ == "__main__":
    panel = sys.argv[1] if len(sys.argv) > 1 else "painel.jpg"
    out = sys.argv[2] if len(sys.argv) > 2 else "saida_parallax.mp4"
    use_real = "--real" in sys.argv
    render_parallax(panel, out, use_real=use_real)
