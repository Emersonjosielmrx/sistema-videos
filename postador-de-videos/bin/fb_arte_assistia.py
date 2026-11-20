"""Foto (1024x1024) e capa (1640x624, proporção da capa de Página) da Página Assist-IA Investimentos. Gera em
D:\\postador-de-videos\\assets\\facebook\\assistia_{foto,capa}.png"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math, random

OUT = Path(r"D:\postador-de-videos\assets\facebook"); OUT.mkdir(parents=True, exist_ok=True)
F_BOLD = r"C:\Windows\Fonts\segoeuib.ttf"
F_REG = r"C:\Windows\Fonts\segoeui.ttf"
AZ1, AZ2, VERDE, OURO, BRANCO = (8, 18, 48), (18, 52, 120), (40, 220, 140), (255, 200, 60), (245, 248, 255)


def fundo(w, h):
    im = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(im)
    for y in range(h):
        t = y / h
        d.line([(0, y), (w, y)], fill=tuple(int(AZ1[i] * (1 - t) + AZ2[i] * t) for i in range(3)))
    # grade
    g = Image.new("RGBA", (w, h), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
    passo = max(40, w // 24)
    for x in range(0, w, passo):
        gd.line([(x, 0), (x, h)], fill=(120, 170, 255, 22))
    for y in range(0, h, passo):
        gd.line([(0, y), (w, y)], fill=(120, 170, 255, 22))
    im.paste(g, (0, 0), g)
    return im


def grafico(im, caixa, n=9, seed=7):
    x0, y0, x1, y1 = caixa
    random.seed(seed)
    larg = (x1 - x0) / n
    camada = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(camada)
    pts, nivel = [], 0.15
    for i in range(n):
        nivel = min(0.95, nivel + random.uniform(0.02, 0.13))
        topo = y1 - (y1 - y0) * nivel
        bx = x0 + i * larg + larg * 0.18
        d.rounded_rectangle([bx, topo, bx + larg * 0.64, y1], radius=int(larg * 0.12),
                            fill=(40, 220, 140, 70 + int(120 * i / n)))
        pts.append((bx + larg * 0.32, topo - larg * 0.25))
    brilho = Image.new("RGBA", im.size, (0, 0, 0, 0)); bd = ImageDraw.Draw(brilho)
    bd.line(pts, fill=(255, 200, 60, 255), width=max(6, int(larg * 0.12)), joint="curve")
    camada.alpha_composite(brilho.filter(ImageFilter.GaussianBlur(int(larg * 0.12))))
    camada.alpha_composite(brilho)
    # seta na ponta
    (ax, ay), (bx2, by2) = pts[-2], pts[-1]
    ang = math.atan2(by2 - ay, bx2 - ax); s = larg * 0.45
    tri = [(bx2 + s * math.cos(ang), by2 + s * math.sin(ang)),
           (bx2 + s * 0.6 * math.cos(ang + 2.4), by2 + s * 0.6 * math.sin(ang + 2.4)),
           (bx2 + s * 0.6 * math.cos(ang - 2.4), by2 + s * 0.6 * math.sin(ang - 2.4))]
    ImageDraw.Draw(camada).polygon(tri, fill=OURO + (255,))
    im.paste(camada, (0, 0), camada)


def texto_centro(d, cx, y, txt, fonte, cor, sombra=True):
    w = d.textlength(txt, font=fonte)
    if sombra:
        d.text((cx - w / 2 + 3, y + 3), txt, font=fonte, fill=(0, 0, 0))
    d.text((cx - w / 2, y), txt, font=fonte, fill=cor)


# FOTO
S = 1024
foto = fundo(S, S)
grafico(foto, (150, 360, 874, 760), n=7)
d = ImageDraw.Draw(foto)
texto_centro(d, S / 2, 120, "ASSIST-IA", ImageFont.truetype(F_BOLD, 150), BRANCO)
texto_centro(d, S / 2, 790, "INVESTIMENTOS", ImageFont.truetype(F_BOLD, 92), VERDE)
foto.save(OUT / "assistia_foto.png")

# CAPA
W, H = 1640, 624
capa = fundo(W, H)
grafico(capa, (900, 120, 1580, 560), n=10, seed=3)
d = ImageDraw.Draw(capa)
d.text((90, 150), "Assist-IA", font=ImageFont.truetype(F_BOLD, 130), fill=BRANCO)
d.text((95, 300), "Investimentos com Inteligência Artificial", font=ImageFont.truetype(F_REG, 48), fill=VERDE)
d.text((95, 380), "Dinheiro • Bolsa • Renda Extra • IA", font=ImageFont.truetype(F_REG, 40), fill=(200, 215, 245))
d.text((95, 450), "Reels novos todo dia", font=ImageFont.truetype(F_BOLD, 40), fill=OURO)
capa.save(OUT / "assistia_capa.png")

# capa do Anime Noturno no tamanho certo (2000x1125 -> 1640x624, corte central-alto)
an = Image.open(r"D:\hipercool-materiais\AMOSTRAS_CANAIS_14nov\aplicar\AnimeNoturno_banner.jpg").convert("RGB")
esc = W / an.width
an = an.resize((W, int(an.height * esc)), Image.LANCZOS)
topo = int((an.height - H) * 0.35)
an.crop((0, topo, W, topo + H)).save(OUT / "animenoturno_capa.png")
print("ok", list(OUT.iterdir()))
