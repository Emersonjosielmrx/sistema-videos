"""Efeitos de TRANSIÇÃO por impacto (28/10, dona: "os efeitos de choque e fogo que o manhwa-react usa para dividir a
tela, só que para transicionar a tela, quando dá o choque aparece a próxima, ou para impactos").

Cópia adaptada de D:\\manhwa-react\\mr\\divider.py (frame_electric / frame_fire / frame_glitch, desenhados por código):
lá a faixa fica parada na emenda webcam/conteúdo; aqui a faixa ATRAVESSA a tela de cima a baixo em ~0,6 s na troca
de cena, com um clarão branco curto no meio (o "choque"). Sai UMA camada transparente do vídeo inteiro (vazia fora das
trocas) que entra entre as cenas e a faixa de texto.
"""
import math
import random
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ESTILOS = ("eletrico", "fogo", "glitch")
FAIXA = 400  # altura da faixa do efeito (px); 300 com os traços do manhwa-react ficava fino no vídeo inteiro


def _glow(img, radius, strength=1.0):
    blur = img.filter(ImageFilter.GaussianBlur(radius))
    a = np.asarray(img).astype(np.float32)
    b = np.asarray(blur).astype(np.float32) * strength
    return Image.fromarray(np.clip(a + b, 0, 255).astype(np.uint8), "RGBA")


def _raio(width, y0, amp, seg, rnd):
    pts = [(0, y0 + rnd.uniform(-amp, amp))]
    x = 0
    while x < width:
        x += rnd.uniform(seg * 0.5, seg * 1.5)
        pts.append((min(width, x), y0 + rnd.uniform(-amp, amp)))
    return pts


def eletrico(W, H, cor, t, rnd):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cy, c1 = H / 2, cor + (255,)
    for b in range(3):
        amp = H * (0.12 + 0.1 * b)
        pts = _raio(W, cy, amp, 28 + 14 * b, rnd)
        d.line(pts, fill=c1, width=14 - 3 * b)
        for _ in range(rnd.randint(2, 5)):
            px, py = pts[rnd.randrange(1, len(pts) - 1)]
            br = [(px, py)] + [(px + rnd.uniform(-40, 40) * (k + 1) * 0.5, py + rnd.uniform(-amp, amp))
                               for k in range(rnd.randint(2, 5))]
            d.line(br, fill=c1, width=4)
    d.line(_raio(W, cy, H * 0.08, 30, rnd), fill=(255, 255, 255, 255), width=8)
    return _glow(_glow(img, 8, 1.0), 26, 0.8)


def _ruido_fogo(W, H, rnd):
    big = np.random.RandomState(rnd.randint(0, 99999)).rand(H * 3, max(8, W // 10)).astype(np.float32)
    im = Image.fromarray((big * 255).astype(np.uint8)).resize((W, H * 3), Image.BICUBIC).filter(ImageFilter.GaussianBlur(3))
    return np.asarray(im).astype(np.float32) / 255.0


def fogo(W, H, cor, t, rnd, ruido):
    base = int(H * 0.75)
    xs = np.arange(W, dtype=np.float32)[None, :]
    ys = np.arange(H, dtype=np.float32)[:, None]
    st = np.random.RandomState(1234)
    K = 30
    cx0, wd, h0 = st.uniform(0, W, K), st.uniform(40, 110, K), st.uniform(130, 290, K)
    f, ph, drift = st.uniform(2.5, 6.0, K), st.uniform(0, 6.28, K), st.uniform(-14, 14, K)
    inten = np.zeros((H, W), np.float32)
    for k in range(K):
        cx = cx0[k] + drift[k] * math.sin(t * 1.7 + ph[k])
        h = h0[k] * (0.72 + 0.28 * math.sin(t * f[k] + ph[k])) * (0.85 + 0.15 * math.sin(t * 11 + k))
        w = wd[k] * (0.9 + 0.1 * math.cos(t * 3 + k))
        up = (base - ys) / max(h, 1)
        lat = (xs - cx) / (w / 2 * np.clip(1 - up * 0.8, 0.15, 1))
        inten += (np.clip(1 - lat * lat, 0, 1) * np.clip(1 - up, 0, 1) * (up >= 0)) ** 1.4
    brasa = np.clip(1 - np.abs(ys - base) / 10.0, 0, 1) * (0.55 + 0.45 * np.sin(xs / 23.0 + t * 9))
    nz = np.roll(ruido, -(int(t * 240) % ruido.shape[0]), axis=0)[:H]
    k = np.clip(np.clip(inten * (0.65 + 0.7 * nz) + brasa * 0.9, 0, 1.6), 0, 1)
    R, G, B = np.clip(k * 2.6, 0, 1) * 255, np.clip((k - 0.22) * 2.0, 0, 1) * 235, np.clip((k - 0.72) * 3.2, 0, 1) * 190
    r, g, b = cor
    frio = np.clip(1 - k * 3, 0, 1) * (k > 0.03)
    R, G, B = (R * (1 - 0.3 * frio) + r * 0.3 * frio, G * (1 - 0.3 * frio) + g * 0.3 * frio,
               B * (1 - 0.3 * frio) + b * 0.3 * frio)
    out = np.dstack([R, G, B, np.clip(k * 2.2, 0, 1) * 255]).astype(np.uint8)
    return _glow(Image.fromarray(out, "RGBA").filter(ImageFilter.GaussianBlur(0.8)), 10, 0.55)


def glitch(W, H, cor, t, rnd):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cy, c = H // 2, cor + (255,)
    x = 0
    while x < W:
        seg = rnd.randint(40, 220)
        if rnd.random() >= 0.18:
            off = rnd.choice([0, 0, 0, -6, 6, -12, 12])
            d.rectangle([x, cy - 9 + off, x + seg, cy + 9 + off], fill=c)
        x += seg + rnd.randint(0, 24)
    for _ in range(rnd.randint(6, 12)):
        bx, bw = rnd.randint(0, W - 80), rnd.randint(40, 300)
        by, bh = cy + rnd.randint(-H // 3, H // 3), rnd.randint(3, 14)
        d.rectangle([bx, by, bx + bw, by + bh],
                    fill=rnd.choice([c, (255, 255, 255, 220), (255, 0, 90, 200), (0, 255, 230, 200)]))
    return _glow(img, 8, 0.8)


def camada(trocas, total, saida, cor, estilo, W=1080, H=1920, fps=30, dur=0.6, seed=None):
    """Grava `saida` (.mov qtrle com alfa, `total` s): em cada instante de `trocas` a faixa do `estilo` atravessa a
    tela de cima a baixo em `dur` s, com clarão branco curto no meio (impacto)."""
    rnd = random.Random(seed)
    ruido = _ruido_fogo(W, FAIXA, rnd) if estilo == "fogo" else None
    vazio = bytes(W * H * 4)
    n = int(math.ceil(total * fps))
    proc = subprocess.Popen([r"D:\hipercool-materiais\bin\ffmpeg.exe", "-y", "-v", "error", "-f", "rawvideo",
                             "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-", "-c:v", "qtrle",
                             "-pix_fmt", "argb", str(saida)], stdin=subprocess.PIPE)
    try:
        for q in range(n):
            t = q / fps
            ativa = next((tc for tc in trocas if tc - dur / 2 <= t < tc + dur / 2), None)
            if ativa is None:
                proc.stdin.write(vazio)
                continue
            p = (t - (ativa - dur / 2)) / dur  # 0..1 da passagem
            if estilo == "eletrico":
                faixa = eletrico(W, FAIXA, cor, t, rnd)
            elif estilo == "fogo":
                faixa = fogo(W, FAIXA, cor, t, rnd, ruido)
            else:
                faixa = glitch(W, FAIXA, cor, t, rnd)
            im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            y = int(-FAIXA + (H + FAIXA) * (1 - (1 - p) ** 2))
            topo, fim = max(y, 0), min(y + FAIXA, H)  # só a parte da faixa que está dentro da tela
            if fim > topo:
                im.alpha_composite(faixa.crop((0, topo - y, W, fim - y)), (0, topo))
            clarao = max(0.0, 1 - abs(p - 0.5) / 0.12) * 0.55  # 2–3 quadros de flash no meio
            if clarao > 0:
                im = Image.alpha_composite(im, Image.new("RGBA", (W, H), (255, 255, 255, int(255 * clarao))))
            proc.stdin.write(im.tobytes())
    finally:
        proc.stdin.close()
        proc.wait(timeout=600)
    if proc.returncode:
        raise RuntimeError("ffmpeg da camada de efeitos de transição falhou")
    return saida
