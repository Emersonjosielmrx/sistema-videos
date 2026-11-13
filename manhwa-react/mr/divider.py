"""Divisoria animada e irregular entre webcam e conteudo (gerada por codigo, na cor do canal).

Estilos de efeito (MOV rgba em loop, 1080 x altura, centrado na emenda):
- electric: raio/eletricidade serpenteando na horizontal, com brilho e tremulacao.
- fire: chamas (cores reais de fogo com um toque da cor do canal) subindo a partir da emenda.
- glitch: blocos deslocados e linha neon com falhas.
- none: sem efeito (so a borda irregular).

Borda irregular (mascara): "tear" (rasgo de papel), "zigzag" (serra), "wave" (ondulado), "flat" (reta).
"""
import math
import random
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from .common import log


def _hex(h, default=(0, 215, 255)):
    try:
        h = h.lstrip("#")
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    except Exception:  # noqa: BLE001
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


# ----------------------------------------------------------------------------- efeitos
def frame_electric(W, H, color, t, rnd, bolts=3):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cy = H / 2
    c1 = color + (255,)
    white = (255, 255, 255, 255)
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
    d.line(_bolt(W, cy, H * 0.08, 30, rnd), fill=white, width=3)
    img = _glow(img, 6, 0.9)
    img = _glow(img, 18, 0.7)
    flick = 0.75 + 0.25 * math.sin(t * 23.0) * rnd.uniform(0.6, 1.0)
    a = np.asarray(img).astype(np.float32)
    a[..., 3] *= flick
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


def _fire_noise(W, H, rnd):
    def layer(div, blur):
        big = np.random.RandomState(rnd.randint(0, 99999)).rand(H * 3, max(8, W // div)).astype(np.float32)
        im = Image.fromarray((big * 255).astype(np.uint8)).resize((W, H * 3), Image.BICUBIC).filter(ImageFilter.GaussianBlur(blur))
        return np.asarray(im).astype(np.float32) / 255.0
    return layer(10, 3), layer(22, 6)


def frame_fire(W, H, color, t, rnd, noise):
    """Linguas de fogo esparsas subindo da emenda (meio da faixa) + brasa fina na linha. Cores reais de fogo com toque do canal."""
    n1, _ = noise
    base = int(H * 0.56)
    xs = np.arange(W, dtype=np.float32)[None, :]
    ys = np.arange(H, dtype=np.float32)[:, None]
    # linguas: posicoes fixas por seed (rnd ja esta "avancado" por frame; usar estado proprio deterministico)
    st = np.random.RandomState(1234)
    K = 30
    cx0 = st.uniform(0, W, K)
    wd = st.uniform(28, 80, K)
    h0 = st.uniform(50, 125, K)
    f = st.uniform(2.5, 6.0, K)
    ph = st.uniform(0, 6.28, K)
    drift = st.uniform(-14, 14, K)
    inten = np.zeros((H, W), np.float32)
    for k in range(K):
        cx = cx0[k] + drift[k] * math.sin(t * 1.7 + ph[k])
        h = h0[k] * (0.72 + 0.28 * math.sin(t * f[k] + ph[k])) * (0.85 + 0.15 * math.sin(t * 11 + k))
        w = wd[k] * (0.9 + 0.1 * math.cos(t * 3 + k))
        up = (base - ys) / max(h, 1)                       # 0 na base, 1 na ponta
        lat = (xs - cx) / (w / 2 * np.clip(1 - up * 0.8, 0.15, 1))  # estreita para a ponta
        tongue = np.clip(1 - lat * lat, 0, 1) * np.clip(1 - up, 0, 1) * (up >= 0)
        inten += tongue ** 1.4
    # brasa na linha da emenda (abaixo da base) e ruido para esfarrapar
    ember = np.clip(1 - np.abs(ys - base) / 10.0, 0, 1) * (0.55 + 0.45 * np.sin(xs / 23.0 + t * 9))
    sh = int(t * 240) % n1.shape[0]
    nz = np.roll(n1, -sh, axis=0)[:H]
    inten = np.clip(inten * (0.65 + 0.7 * nz) + ember * 0.9, 0, 1.6)
    k = np.clip(inten, 0, 1)
    R = np.clip(k * 2.6, 0, 1) * 255
    G = np.clip((k - 0.22) * 2.0, 0, 1) * 235
    B = np.clip((k - 0.72) * 3.2, 0, 1) * 190
    r, g, b = color
    cold = np.clip(1 - k * 3, 0, 1) * (k > 0.03)
    R = R * (1 - 0.3 * cold) + r * 0.3 * cold
    G = G * (1 - 0.3 * cold) + g * 0.3 * cold
    B = B * (1 - 0.3 * cold) + b * 0.3 * cold
    alpha = np.clip(k * 2.2, 0, 1) * 255
    out = np.dstack([R, G, B, alpha]).astype(np.uint8)
    img = Image.fromarray(out, "RGBA").filter(ImageFilter.GaussianBlur(0.8))
    return _glow(img, 10, 0.55)


def frame_glitch(W, H, color, t, rnd):
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
        bh = rnd.randint(3, 12)
        col = rnd.choice([c, (255, 255, 255, 220), (255, 0, 90, 200), (0, 255, 230, 200)])
        d.rectangle([bx, by, bx + bw, by + bh], fill=col)
    for yy in range(0, H, 4):
        d.line([(0, yy), (W, yy)], fill=(0, 0, 0, 40))
    return _glow(img, 8, 0.8)


def render_divider(cfg, style, color_hex, out_path, duration=6.0, fps=30, height=None, seed=None):
    """Gera o MOV rgba em loop da divisoria. Retorna (caminho, altura)."""
    W = cfg["output"]["width"]
    D = cfg.get("divider", {})
    H = int(height or D.get("height", 160))
    H -= H % 2
    color = _hex(color_hex)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    frames_dir = out_path.parent / (out_path.stem + "_frames")
    frames_dir.mkdir(exist_ok=True)
    rnd = random.Random(seed if seed is not None else style)
    n = int(duration * fps)
    noise = _fire_noise(W, H, rnd) if style == "fire" else None
    import time
    for i in range(n):
        t = i / fps
        for attempt in range(6):
            try:
                if style == "fire":
                    fr = frame_fire(W, H, color, t, rnd, noise)
                elif style == "glitch":
                    fr = frame_glitch(W, H, color, t, rnd)
                else:
                    fr = frame_electric(W, H, color, t, rnd)
                fr.save(frames_dir / f"f{i:04d}.png")
                break
            except MemoryError:
                # maquina com pagefile cheio: espera liberar
                log(f"divisoria: sem memoria no frame {i}; aguardando 15s")
                time.sleep(15)
        else:
            raise MemoryError("divisoria: sem memoria para gerar os frames")
    from .common import ffmpeg
    ffmpeg(cfg, ["-framerate", str(fps), "-i", str(frames_dir / "f%04d.png"), "-c:v", "png", "-pix_fmt", "rgba", str(out_path)])
    for f in frames_dir.glob("*.png"):
        f.unlink()
    frames_dir.rmdir()
    log(f"divisoria '{style}' gerada: {out_path.name} ({W}x{H}, {duration:.0f}s loop)")
    return out_path, H


def divider_asset(cfg, style, color_hex, duration=6.0):
    """Divisoria em cache por estilo+cor (assets/dividers/<style>_<cor>.mov). None para style 'none'/'flat'."""
    if style in (None, "none", "flat"):
        return None, 0
    base = Path(cfg["paths"]["assets"]) / "dividers"
    H = int(cfg.get("divider", {}).get("height", 160)) // 2 * 2
    p = base / f"{style}_{color_hex.lstrip('#').lower()}_{H}.mov"
    if p.exists():
        return p, H
    return render_divider(cfg, style, color_hex, p, duration=duration, height=H)


# ----------------------------------------------------------------------------- borda irregular
def seam_mask(cfg, content_h, overlap, edge="tear", seed=7):
    """Mascara (PNG cinza) 1080 x content_h: branco = conteudo visivel, preto = webcam visivel.
    As primeiras `overlap` linhas tem a borda irregular; o resto e branco."""
    W = cfg["output"]["width"]
    base = Path(cfg["paths"]["assets"]) / "dividers"
    base.mkdir(parents=True, exist_ok=True)
    p = base / f"mask_{edge}_{W}x{content_h}_{overlap}_{seed}.png"
    if p.exists():
        return p
    rnd = random.Random(seed)
    img = Image.new("L", (W, content_h), 255)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, overlap], fill=0)
    pts = [(0, overlap)]
    x = 0.0
    if edge == "zigzag":
        step = overlap * 0.9
        up = True
        while x < W:
            x += step
            pts.append((min(W, x), overlap * (0.15 if up else 0.85)))
            up = not up
    elif edge == "wave":
        while x < W:
            x += 6
            pts.append((min(W, x), overlap * (0.5 + 0.38 * math.sin(x / 70.0) * math.cos(x / 190.0 + 1.3))))
    elif edge == "flat":
        pts.append((W, overlap * 0.5))
    else:  # tear
        y = overlap * 0.5
        while x < W:
            x += rnd.uniform(4, 14)
            y += rnd.uniform(-overlap, overlap) * 0.22
            y = max(overlap * 0.12, min(overlap * 0.88, y))
            pts.append((min(W, x), y))
    pts += [(W, overlap), (W, overlap + 2), (0, overlap + 2)]
    d.polygon(pts, fill=255)
    if edge == "tear":
        # fibras: pequenos recortes na borda
        for _ in range(140):
            px = rnd.uniform(0, W)
            py = overlap * rnd.uniform(0.3, 0.75)
            d.polygon([(px, py), (px + rnd.uniform(-10, 10), py - rnd.uniform(4, 16)), (px + rnd.uniform(-6, 6), py + rnd.uniform(2, 8))], fill=rnd.choice([0, 255]))
    img = img.filter(ImageFilter.GaussianBlur(0.8))
    img.save(p)
    return p
