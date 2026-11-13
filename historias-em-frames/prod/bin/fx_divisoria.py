"""fx_divisoria.py — transicao "rasgo" entre cenas com a divisoria animada do manhwa-react.

Um rasgo irregular desce pela tela trocando a cena atual pela PROXIMA imagem, e uma faixa
animada (raio / fogo / glitch, mesmos desenhos do mr/divider.py do manhwa-react) acompanha
a emenda. Aplicado no FIM do clip da cena (ultimos TRANS s): a duracao do clip e o audio
nao mudam, entao legenda/concat nao se mexem. A cena seguinte comeca na mesma imagem.

Flag: DIVISORIA=1 (default ligado). Estilo/cor por genero em ESTILO_GENERO.
Faixas geradas por codigo e cacheadas em workspace/assets/_divisorias/ (MOV rgba).
"""
import math
import os
import random
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

PROJECT_DIR = Path(__file__).resolve().parent.parent
CACHE = PROJECT_DIR / "workspace" / "assets" / "_divisorias"
FPS = 30
STRIP = 150          # altura da faixa animada (px, em 720p; escala com a largura)
TRANS = 0.9          # duracao do rasgo (s)

# genero -> (estilo, cor). Fogo pra tensao, raio pra virada/energia, glitch pra misterio.
ESTILO_GENERO = {
    "terror": ("fire", "#FF2A1A"),
    "drama": ("fire", "#FF6A1A"),
    "misterio": ("glitch", "#B455FF"),
    "fantasia": ("electric", "#7DF9FF"),
    "superacao": ("electric", "#FFC83D"),
    "motivacional": ("electric", "#FFC83D"),
    "curiosidades": ("glitch", "#00E5FF"),
    "comedia": ("glitch", "#FF3EA5"),
    "romance": ("electric", "#FF6FAE"),
    "religioso": ("electric", "#FFF1B8"),
}

# Borda rasgada: soma de senoides em X (deterministica, sem ruido por quadro).
EDGE = "(14*sin(X/9.7)+9*sin(X/4.3+1.3)+22*sin(X/53+0.7)+6*sin(X/2.1))"


def ativo():
    return os.environ.get("DIVISORIA", "1") == "1"


def estilo_do_genero(genero):
    return ESTILO_GENERO.get((genero or "").lower(), ("electric", "#FFC83D"))


# ----------------------------------------------------------------------------- desenho
# (porte direto de manhwa-react/mr/divider.py)
def _hex(h, default=(0, 215, 255)):
    try:
        h = h.lstrip("#")
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    except Exception:
        return default


def _glow(img, radius, strength=1.0):
    blur = img.filter(ImageFilter.GaussianBlur(radius))
    a = np.asarray(img).astype(np.float32)
    b = np.asarray(blur).astype(np.float32) * strength
    return Image.fromarray(np.clip(a + b, 0, 255).astype(np.uint8), "RGBA")


def _bolt(width, y0, amp, seg, rnd):
    pts = [(0, y0 + rnd.uniform(-amp, amp))]
    x = 0
    while x < width:
        x += rnd.uniform(seg * 0.5, seg * 1.5)
        pts.append((min(width, x), y0 + rnd.uniform(-amp, amp)))
    return pts


def _frame_electric(W, H, color, t, rnd, bolts=3):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cy = H / 2
    c1 = color + (255,)
    for b in range(bolts):
        amp = H * (0.12 + 0.1 * b)
        pts = _bolt(W, cy, amp, 28 + 14 * b, rnd)
        d.line(pts, fill=c1, width=6 - b)
        for _ in range(rnd.randint(2, 5)):
            i = rnd.randrange(1, len(pts) - 1)
            px, py = pts[i]
            br = [(px, py)]
            for k in range(rnd.randint(2, 5)):
                br.append((px + rnd.uniform(-40, 40) * (k + 1) * 0.5, py + rnd.uniform(-amp, amp)))
            d.line(br, fill=c1, width=2)
    d.line(_bolt(W, cy, H * 0.08, 30, rnd), fill=(255, 255, 255, 255), width=3)
    img = _glow(img, 6, 0.9)
    img = _glow(img, 18, 0.7)
    flick = 0.75 + 0.25 * math.sin(t * 23.0) * rnd.uniform(0.6, 1.0)
    a = np.asarray(img).astype(np.float32)
    a[..., 3] *= flick
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


def _fire_noise(W, H, rnd):
    big = np.random.RandomState(rnd.randint(0, 99999)).rand(H * 3, max(8, W // 10)).astype(np.float32)
    im = Image.fromarray((big * 255).astype(np.uint8)).resize((W, H * 3), Image.BICUBIC).filter(ImageFilter.GaussianBlur(3))
    return np.asarray(im).astype(np.float32) / 255.0


def _frame_fire(W, H, color, t, noise):
    base = int(H * 0.56)
    xs = np.arange(W, dtype=np.float32)[None, :]
    ys = np.arange(H, dtype=np.float32)[:, None]
    st = np.random.RandomState(1234)
    K = 30
    cx0, wd = st.uniform(0, W, K), st.uniform(28, 80, K)
    h0, f = st.uniform(50, 125, K), st.uniform(2.5, 6.0, K)
    ph, drift = st.uniform(0, 6.28, K), st.uniform(-14, 14, K)
    inten = np.zeros((H, W), np.float32)
    for k in range(K):
        cx = cx0[k] + drift[k] * math.sin(t * 1.7 + ph[k])
        h = h0[k] * (0.72 + 0.28 * math.sin(t * f[k] + ph[k])) * (0.85 + 0.15 * math.sin(t * 11 + k))
        w = wd[k] * (0.9 + 0.1 * math.cos(t * 3 + k))
        up = (base - ys) / max(h, 1)
        lat = (xs - cx) / (w / 2 * np.clip(1 - up * 0.8, 0.15, 1))
        inten += (np.clip(1 - lat * lat, 0, 1) * np.clip(1 - up, 0, 1) * (up >= 0)) ** 1.4
    ember = np.clip(1 - np.abs(ys - base) / 10.0, 0, 1) * (0.55 + 0.45 * np.sin(xs / 23.0 + t * 9))
    sh = int(t * 240) % noise.shape[0]
    nz = np.roll(noise, -sh, axis=0)[:H]
    k = np.clip(np.clip(inten * (0.65 + 0.7 * nz) + ember * 0.9, 0, 1.6), 0, 1)
    R = np.clip(k * 2.6, 0, 1) * 255
    G = np.clip((k - 0.22) * 2.0, 0, 1) * 235
    B = np.clip((k - 0.72) * 3.2, 0, 1) * 190
    r, g, b = color
    cold = np.clip(1 - k * 3, 0, 1) * (k > 0.03)
    R = R * (1 - 0.3 * cold) + r * 0.3 * cold
    G = G * (1 - 0.3 * cold) + g * 0.3 * cold
    B = B * (1 - 0.3 * cold) + b * 0.3 * cold
    out = np.dstack([R, G, B, np.clip(k * 2.2, 0, 1) * 255]).astype(np.uint8)
    return _glow(Image.fromarray(out, "RGBA").filter(ImageFilter.GaussianBlur(0.8)), 10, 0.55)


def _frame_glitch(W, H, color, t, rnd):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cy = H // 2
    c = color + (255,)
    x = 0
    while x < W:
        seg = rnd.randint(40, 220)
        if rnd.random() >= 0.18:
            off = rnd.choice([0, 0, 0, -6, 6, -12, 12])
            d.rectangle([x, cy - 3 + off, x + seg, cy + 3 + off], fill=c)
        x += seg + rnd.randint(0, 24)
    for _ in range(rnd.randint(4, 9)):
        bx, bw = rnd.randint(0, W - 80), rnd.randint(40, 260)
        by = cy + rnd.randint(-H // 3, H // 3)
        col = rnd.choice([c, (255, 255, 255, 220), (255, 0, 90, 200), (0, 255, 230, 200)])
        d.rectangle([bx, by, bx + bw, by + rnd.randint(3, 12)], fill=col)
    for yy in range(0, H, 4):
        d.line([(0, yy), (W, yy)], fill=(0, 0, 0, 40))
    return _glow(img, 8, 0.8)


def faixa(estilo, cor, W):
    """MOV rgba (W x STRIP*W/720) com a animacao, em cache por estilo+cor+largura."""
    H = int(STRIP * W / 720) // 2 * 2
    CACHE.mkdir(parents=True, exist_ok=True)
    out = CACHE / f"{estilo}_{cor.lstrip('#').lower()}_{W}x{H}.mov"
    if out.exists() and out.stat().st_size > 1000:
        return out, H
    rgb = _hex(cor)
    rnd = random.Random(estilo)
    noise = _fire_noise(W, H, rnd) if estilo == "fire" else None
    fdir = CACHE / f"_frames_{out.stem}"
    fdir.mkdir(exist_ok=True)
    n = int(TRANS * FPS) + 3
    for i in range(n):
        t = i / FPS
        if estilo == "fire":
            fr = _frame_fire(W, H, rgb, t, noise)
        elif estilo == "glitch":
            fr = _frame_glitch(W, H, rgb, t, rnd)
        else:
            fr = _frame_electric(W, H, rgb, t, rnd)
        fr.save(fdir / f"f{i:04d}.png")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS),
                    "-i", str(fdir / "f%04d.png"), "-c:v", "png", "-pix_fmt", "rgba", str(out)],
                   check=True, timeout=120)
    for f in fdir.glob("*.png"):
        f.unlink()
    fdir.rmdir()
    return out, H


def _probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                        "-show_entries", "stream=width,height:format=duration",
                        "-of", "default=nw=1", str(path)], capture_output=True, text=True, timeout=20)
    kv = dict(l.split("=", 1) for l in r.stdout.splitlines() if "=" in l)
    return int(kv["width"]), int(kv["height"]), float(kv["duration"])


def aplicar_rasgo(clip_in, prox_img, clip_out, genero=None, estilo=None, cor=None, trans=TRANS):
    """Fim do clip_in vira a prox_img por um rasgo descendo + faixa animada na emenda.

    Mesma duracao/resolucao do clip_in; audio copiado. True se gerou."""
    try:
        W, H, dur = _probe(clip_in)
    except Exception:
        return False
    if dur < trans + 0.8:
        return False
    if not estilo or not cor:
        estilo, cor = estilo_do_genero(genero)
    try:
        mov, SH = faixa(estilo, cor, W)
    except Exception:
        return False
    off = dur - trans
    seam = "((1-P)*(H+80)-40)"     # P vai de 1 -> 0 no xfade custom
    y = f"(((t-{off:.3f})/{trans})*({H}+80)-40)-{SH}/2"
    fc = (
        f"[1:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,"
        f"fps={FPS},format=yuv420p[b];"
        f"[0:v]fps={FPS},format=yuv420p,setsar=1[a];"
        f"[a][b]xfade=transition=custom:duration={trans}:offset={off:.3f}:"
        f"expr='if(lt(Y,{seam}+{EDGE}),B,A)'[x];"
        f"[2:v]setpts=PTS-STARTPTS+{off:.3f}/TB[f];"
        f"[x][f]overlay=x=0:y='{y}':enable='between(t,{off:.3f},{dur:.3f})':eof_action=pass,"
        f"format=yuv420p[v]"
    )
    cmd = ["ffmpeg", "-y", "-i", str(clip_in),
           "-loop", "1", "-t", f"{trans + 0.2:.2f}", "-i", str(prox_img),
           "-i", str(mov),
           "-filter_complex", fc, "-map", "[v]", "-map", "0:a?",
           "-t", f"{dur:.3f}",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "copy",
           str(clip_out)]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=180)
        return Path(clip_out).exists() and Path(clip_out).stat().st_size > 5000
    except Exception:
        return False
