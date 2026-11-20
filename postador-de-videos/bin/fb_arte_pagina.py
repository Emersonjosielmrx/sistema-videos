"""Foto (1024x1024) e capa (1640x624) de uma Página nova, por tema. Gera assets/facebook/<chave>_{foto,capa}.png
    python fb_arte_pagina.py <chave> "<Título>" "<subtítulo>" "<linha 2>" <tema>
tema: curiosidades | dorama | filmes | manhwa | futebol"""
import sys, math, random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

OUT = Path(r"D:\postador-de-videos\assets\facebook"); OUT.mkdir(parents=True, exist_ok=True)
FB, FR = r"C:\Windows\Fonts\segoeuib.ttf", r"C:\Windows\Fonts\segoeui.ttf"
FSYM = r"C:\Windows\Fonts\seguisym.ttf"
TEMAS = {  # fundo topo, fundo base, destaque, símbolo
    "curiosidades": ((14, 6, 40), (60, 20, 110), (255, 205, 70), "?"),
    "dorama": ((40, 8, 30), (150, 40, 90), (255, 170, 200), "♥"),
    "filmes": ((10, 10, 14), (70, 10, 10), (255, 190, 60), "▶"),
    "manhwa": ((6, 10, 30), (30, 40, 110), (120, 220, 255), "✦"),
    "futebol": ((4, 30, 12), (20, 110, 50), (255, 255, 255), "⚽"),
    # 20/11: temas da fila das 53 Páginas (fb_criar_fila.py)
    "financas": ((4, 20, 40), (10, 90, 70), (90, 230, 140), "$"),
    "games": ((20, 4, 40), (80, 20, 140), (120, 255, 200), "✚"),
    "ia": ((4, 12, 40), (20, 70, 140), (110, 200, 255), "✦"),
    "humor": ((40, 20, 0), (170, 80, 10), (255, 230, 90), "☺"),
    "bichos": ((10, 30, 10), (60, 110, 30), (255, 220, 120), "✿"),
    "misterio": ((6, 6, 20), (40, 30, 80), (170, 255, 170), "✪"),
    "musica": ((30, 0, 40), (140, 20, 120), (255, 160, 240), "♫"),
    "historias": ((30, 14, 4), (110, 50, 20), (255, 200, 120), "✎"),
}
chave, titulo, sub, linha2, tema = sys.argv[1:6]
C1, C2, DEST, SIMB = TEMAS[tema]
BR = (248, 248, 255)


def fundo(w, h, seed=1):
    im = Image.new("RGB", (w, h)); d = ImageDraw.Draw(im)
    for y in range(h):
        t = y / h
        d.line([(0, y), (w, y)], fill=tuple(int(C1[i] * (1 - t) + C2[i] * t) for i in range(3)))
    random.seed(seed)
    est = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ed = ImageDraw.Draw(est)
    for _ in range(int(w * h / 9000)):
        x, y, r = random.randint(0, w), random.randint(0, int(h * 0.8)), random.choice([1, 1, 2, 2, 3])
        ed.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, random.randint(60, 200)))
    im.paste(est, (0, 0), est)
    return im


def lua(im, cx, cy, r):
    g = Image.new("RGBA", im.size, (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
    gd.ellipse([cx - r * 1.6, cy - r * 1.6, cx + r * 1.6, cy + r * 1.6], fill=DEST + (60,))
    g = g.filter(ImageFilter.GaussianBlur(r * 0.5))
    ImageDraw.Draw(g).ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 246, 220, 255))
    im.paste(g, (0, 0), g)


def simbolo(im, cx, cy, tam):
    f = ImageFont.truetype(FB if SIMB in ("?", "$") else FSYM, tam)
    d = ImageDraw.Draw(im)
    w = d.textlength(SIMB, font=f)
    sombra = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sombra).text((cx - w / 2, cy - tam * 0.62), SIMB, font=f, fill=DEST + (255,))
    im.paste(sombra.filter(ImageFilter.GaussianBlur(tam * 0.06)), (0, 0), sombra.filter(ImageFilter.GaussianBlur(tam * 0.06)))
    d.text((cx - w / 2, cy - tam * 0.62), SIMB, font=f, fill=DEST)


def centro(d, cx, y, txt, fonte, cor):
    w = d.textlength(txt, font=fonte)
    d.text((cx - w / 2 + 3, y + 3), txt, font=fonte, fill=(0, 0, 0)); d.text((cx - w / 2, y), txt, font=fonte, fill=cor)


def caber(d, txt, fonte_path, tam, largura):
    while tam > 20 and d.textlength(txt, font=ImageFont.truetype(fonte_path, tam)) > largura:
        tam -= 4
    return ImageFont.truetype(fonte_path, tam)


# FOTO
S = 1024
foto = fundo(S, S)
lua(foto, 760, 250, 120)
simbolo(foto, S / 2, 470, 420)
d = ImageDraw.Draw(foto)
palavras = titulo.upper().split()
l1, l2 = (palavras[0], " ".join(palavras[1:])) if len(palavras) > 1 else (titulo.upper(), "")
centro(d, S / 2, 680, l1, caber(d, l1, FB, 130, 900), BR)
if l2:
    centro(d, S / 2, 830, l2, caber(d, l2, FB, 100, 900), DEST)
foto.save(OUT / f"{chave}_foto.png")

# CAPA
W, H = 1640, 624
capa = fundo(W, H, seed=2)
lua(capa, 1380, 190, 110)
simbolo(capa, 1250, 400, 300)
d = ImageDraw.Draw(capa)
d.text((90, 150), titulo, font=caber(d, titulo, FB, 120, 1000), fill=BR)
d.text((95, 310), sub, font=caber(d, sub, FR, 48, 1000), fill=DEST)
d.text((95, 390), linha2, font=caber(d, linha2, FR, 40, 1000), fill=(220, 220, 240))
d.text((95, 460), "Reels novos todo dia", font=ImageFont.truetype(FB, 40), fill=DEST)
capa.save(OUT / f"{chave}_capa.png")
print("ok", OUT / f"{chave}_foto.png", OUT / f"{chave}_capa.png")
