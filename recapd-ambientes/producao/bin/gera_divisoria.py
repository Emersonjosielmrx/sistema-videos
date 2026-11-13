"""29/10 dona: "as transições boas são os EFEITOS da divisão de tela do manhwa-react; aplicar eles no longo, não só uma
linha — algo encorpado caminhando na transição". Usa o CÓDIGO do próprio manhwa-react (D:\\manhwa-react\\mr\\divider.py:
frame_electric, frame_fire, frame_glitch — raios ramificados com brilho, línguas de fogo, blocos de glitch) pra gerar a
faixa animada, gira de pé (a faixa atravessa a tela da esquerda pra direita ou o contrário em fx_clips._com_divisoria)
e grava leve (VP9 com alfa) em workspace/assets/overlays_leves/_divisoria_<estilo>_<cor>.webm.
    python gera_divisoria.py"""
import random
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, r"D:\manhwa-react")
from mr import divider  # noqa: E402

ALTURA_TELA, LARGURA_FAIXA, FPS, DUR = 720, 300, 30, 1.0
SAIDA = Path(__file__).resolve().parent.parent / "workspace" / "assets" / "overlays_leves"
ESTILOS = [("electric", "00d1ff"), ("electric", "c13cff"), ("fire", "ff6a1a"), ("glitch", "ff3ea5"),
           ("electric", "ffc83d"), ("glitch", "b455ff"),
           # 31/10 dona: "mais transições — fogo, água, rasgando a tela como um papel e outras"
           ("fire", "ff2a1a"), ("agua", "2a9df4"), ("papel", "f4efe4"), ("gelo", "bfefff"),
           # 01/11 dona: "água seria como esta" (-ZN0Twtxg2Y) — tinta líquida chapada, em 3 cores
           ("liquido", "3a4cf0"), ("liquido", "22ff22"), ("liquido", "111111")]


def _np():
    import numpy as np
    return np


def _borda(n, rnd, amp, suav):
    """Linha irregular (rasgo) com n pontos: passeio aleatório suavizado."""
    np = _np()
    r = np.cumsum(np.array([rnd.uniform(-1, 1) for _ in range(n)]))
    r = np.convolve(r - r.mean(), np.ones(suav) / suav, mode="same")
    r = r / (np.abs(r).max() or 1) * amp
    fino = np.array([rnd.uniform(-amp * 0.18, amp * 0.18) for _ in range(n)])
    return r + fino


def frame_papel(W, H, rgb, t, rnd, cache):
    """Papel rasgado: tira de papel com as 2 bordas irregulares, fibras, sombra; tremula de leve."""
    from PIL import Image, ImageFilter
    np = _np()
    if "b1" not in cache:
        cache["b1"], cache["b2"] = _borda(W, rnd, 26, 9), _borda(W, rnd, 26, 9)
        cache["fibra"] = np.array([[rnd.random() for _ in range(W)] for _ in range(H)]) ** 6
    y = np.arange(H)[:, None]
    tremor = 3 * np.sin(np.arange(W)[None, :] / 37 + t * 18)
    c1 = H / 2 - 52 + cache["b1"][None, :] + tremor
    c2 = H / 2 + 52 + cache["b2"][None, :] + tremor
    papel = (y > c1) & (y < c2)
    borda = papel & ((y - c1 < 6) | (c2 - y < 6))
    sombra = (y >= c2) & (y < c2 + 22)
    a = np.zeros((H, W, 4), np.uint8)
    a[sombra] = (0, 0, 0, 140)
    cor = np.array(rgb, float)
    tom = 1 - 0.10 * cache["fibra"]
    a[..., :3][papel] = (cor[None, None, :] * tom[..., None])[papel].clip(0, 255).astype(np.uint8)
    a[..., 3][papel] = 255
    a[..., :3][borda] = (255, 255, 255)
    img = Image.fromarray(a, "RGBA")
    return img.filter(ImageFilter.GaussianBlur(0.6))


def frame_agua(W, H, rgb, t, rnd, cache):
    """Onda d'água: faixa azul translúcida com ondas que correm, crista de espuma branca e gotas."""
    from PIL import Image, ImageDraw
    np = _np()
    x = np.arange(W)[None, :]
    y = np.arange(H)[:, None]
    o1 = 30 * np.sin(x / 41 + t * 9) + 14 * np.sin(x / 13 - t * 15)
    o2 = 30 * np.sin(x / 47 - t * 8 + 1.7) + 14 * np.sin(x / 11 + t * 13)
    c1, c2 = H / 2 - 70 + o1, H / 2 + 70 + o2
    dentro = (y > c1) & (y < c2)
    prof = ((y - c1) / (c2 - c1)).clip(0, 1)
    a = np.zeros((H, W, 4), np.uint8)
    cor = np.array(rgb, float)
    brilho = 0.75 + 0.35 * np.sin(x / 9 + y / 7 + t * 20) * (1 - prof)
    a[..., :3][dentro] = (cor[None, None, :] * brilho[..., None]).clip(0, 255).astype(np.uint8)[dentro]
    a[..., 3][dentro] = (170 + 60 * np.sin(prof * np.pi)).astype(np.uint8)[dentro]
    espuma = ((np.abs(y - c1) < 5) | (np.abs(y - c2) < 5))
    a[espuma] = (255, 255, 255, 235)
    img = Image.fromarray(a, "RGBA")
    d = ImageDraw.Draw(img)
    r2 = random.Random(int(t * 30))
    for _ in range(26):
        gx = r2.uniform(0, W)
        lado = r2.choice((-1, 1))
        gy = H / 2 + lado * (80 + r2.uniform(0, 60))
        rr = r2.uniform(2, 6)
        d.ellipse((gx - rr, gy - rr, gx + rr, gy + rr), fill=(220, 240, 255, 210))
    return divider._glow(img, 10, 0.5)


def frame_gelo(W, H, rgb, t, rnd, cache):
    """Gelo: cacos de cristal (triângulos) brilhando ao longo da faixa, com brilho frio."""
    from PIL import Image, ImageDraw
    if "cacos" not in cache:
        cache["cacos"] = []
        for _ in range(110):
            cx, cy = rnd.uniform(0, W), H / 2 + rnd.gauss(0, 38)
            s = rnd.uniform(10, 34)
            pts = [(cx + rnd.uniform(-s, s), cy + rnd.uniform(-s * 1.6, s * 1.6)) for _ in range(3)]
            cache["cacos"].append((pts, rnd.uniform(0, 6.28)))
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    import math
    for pts, fase in cache["cacos"]:
        luz = 0.6 + 0.4 * math.sin(t * 14 + fase)
        cor = tuple(int(min(255, c * luz + 40)) for c in rgb) + (int(170 + 70 * luz),)
        d.polygon(pts, fill=cor, outline=(255, 255, 255, 255))
    return divider._glow(img, 18, 0.9)


def frame_liquido(W, H, rgb, t, rnd, cache):
    """01/11 dona (referência -ZN0Twtxg2Y): transição LÍQUIDA de cor chapada — miolo sólido e escorridos em cápsula
    (pontas redondas) pros dois lados no sentido do movimento, com uma 2ª cor (branco) por baixo; os escorridos esticam
    e encolhem como tinta jogada."""
    from PIL import Image, ImageDraw
    import math
    if "caps" not in cache:
        cache["caps"] = []
        for _ in range(26):  # (posição ao longo da faixa, espessura, comprimento, lado, fase, cor 2?)
            cache["caps"].append((rnd.uniform(0, W), rnd.uniform(10, 26), rnd.uniform(0.25, 0.48),
                                  rnd.choice((-1, 1)), rnd.uniform(0, 6.28), rnd.random() < 0.35))
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cor, branco = tuple(rgb) + (255,), (255, 255, 255, 255)
    meio = H / 2
    nucleo = H * 0.18
    for segunda in (True, False):  # a cor 2 vai por baixo e um pouco maior
        for x, esp, comp, lado, fase, eh2 in cache["caps"]:
            if eh2 != segunda:
                continue
            ext = H * comp * (0.75 + 0.25 * math.sin(t * 7 + fase))
            y0, y1 = sorted((meio, meio + lado * (nucleo + ext)))
            e = esp * (1.25 if segunda else 1.0)
            d.rounded_rectangle((x - e / 2, y0, x + e / 2, y1), radius=e / 2, fill=branco if segunda else cor)
    d.rectangle((0, meio - nucleo, W, meio + nucleo), fill=cor)  # miolo sólido: cobre a emenda das cenas
    return img


def gerar(estilo, cor):
    alvo = SAIDA / f"_divisoria_{estilo}_{cor}.webm"
    if alvo.exists():
        return
    W, H = ALTURA_TELA, LARGURA_FAIXA  # gera DEITADO (como no manhwa-react) e gira
    rnd = random.Random(f"{estilo}{cor}")
    rgb = divider._hex(cor)
    noise = divider._fire_noise(W, H, rnd) if estilo == "fire" else None
    cache = {}
    novos = {"papel": frame_papel, "agua": frame_agua, "gelo": frame_gelo, "liquido": frame_liquido}
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{H}x{W}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", "0",
                          "-crf", "32", str(alvo)], stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)):
        t = i / FPS
        if estilo in novos:
            fr = novos[estilo](W, H, rgb, t, rnd, cache)
        elif estilo == "fire":
            fr = divider.frame_fire(W, H, rgb, t, rnd, noise)
        elif estilo == "glitch":
            fr = divider.frame_glitch(W, H, rgb, t, rnd)
        else:
            # dona: "não só uma linha" — 2 camadas de raios do manhwa-react sobrepostas (6 raios) + brilho largo
            fr = divider.frame_electric(W, H, rgb, t, rnd, bolts=3)
            fr.alpha_composite(divider.frame_electric(W, H, (255, 255, 255), t, rnd, bolts=3))
            fr = divider._glow(fr, 30, 0.8)
        p.stdin.write(fr.rotate(90, expand=True).tobytes())
    p.stdin.close()
    p.wait()
    print(alvo.name, alvo.stat().st_size // 1024, "KB", flush=True)


if __name__ == "__main__":
    SAIDA.mkdir(parents=True, exist_ok=True)
    for velho in SAIDA.glob("_divisoria_*.webm"):  # a 1ª versão (linha fina de 120 px) sai
        if velho.stem.count("_") == 2:
            velho.unlink()
    for estilo, cor in ESTILOS:
        gerar(estilo, cor)
