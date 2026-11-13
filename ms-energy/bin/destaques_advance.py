# -*- coding: utf-8 -*-
r"""destaques_advance.py — destaques do perfil @advance_novoestrela com capinha padronizada (dona 30/10: "falta colocar
coisas aqui, fotos e vídeos específicos, colocar as capinhas bonitinhas, padronizado as cores").

Capa = círculo roxo da matriz (degradê roxo, anel laranja, ícone branco desenhado aqui, sem texto dentro). O Instagram
usa como capa a imagem de um story: cada capa vai como story 1080x1920 e, junto com os stories do tema, vira o destaque
(postar.py criar_destaque). Os 5 destaques antigos ("Destaques") ficam como estão.

    D:\veo\venv\Scripts\python.exe destaques_advance.py --capas     # só desenha as capas (para conferir)
    D:\veo\venv\Scripts\python.exe destaques_advance.py --criar     # posta as capas como story e cria os destaques
"""
import json
import math
import sys
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, r"D:\ms-energy\bin")
import carrossel_advance as ca  # noqa: E402

W, H = 1080, 1920
DIR = Path(r"D:\ms-energy\videos\destaques_advance")
ESTADO = DIR / "estado.json"
BRANCO = (255, 255, 255)

# (titulo do destaque, icone, de onde vêm os stories)
DESTAQUES = [
    ("Orçamento", "whats", "cta"),
    ("Instalações", "casa", "fotos"),
    ("Dúvidas", "pergunta", "carrosseis"),
    ("Economia", "raio", "carrosseis"),
    ("Sobre nós", "sol", "logo"),
]


def _icone(d, nome, cx, cy, r, cor=BRANCO, lw=None):
    lw = lw or max(8, r // 7)
    if nome == "sol":
        d.ellipse((cx - r * .42, cy - r * .42, cx + r * .42, cy + r * .42), fill=cor)
        for i in range(8):
            a = i * math.pi / 4
            d.line([(cx + math.cos(a) * r * .62, cy + math.sin(a) * r * .62),
                    (cx + math.cos(a) * r * .92, cy + math.sin(a) * r * .92)], fill=cor, width=lw)
    elif nome == "casa":
        d.polygon([(cx - r * .85, cy - r * .05), (cx, cy - r * .8), (cx + r * .85, cy - r * .05)], fill=cor)
        d.rectangle((cx - r * .62, cy - r * .1, cx + r * .62, cy + r * .75), fill=cor)
        # painel solar no telhado (grade roxa)
        for k in range(3):
            x0 = cx - r * .55 + k * r * .3
            d.polygon([(x0, cy - r * .2), (x0 + r * .26, cy - r * .2), (x0 + r * .26 + r * .16, cy - r * .42),
                       (x0 + r * .16, cy - r * .42)], fill=ca.ROXO)
        d.rectangle((cx - r * .15, cy + r * .3, cx + r * .15, cy + r * .75), fill=ca.ROXO)
    elif nome == "raio":
        d.polygon([(cx + r * .15, cy - r * .9), (cx - r * .5, cy + r * .12), (cx - r * .02, cy + r * .12),
                   (cx - r * .2, cy + r * .9), (cx + r * .5, cy - r * .15), (cx + r * .02, cy - r * .15)], fill=cor)
    elif nome == "pergunta":
        d.arc((cx - r * .5, cy - r * .85, cx + r * .5, cy + r * .1), start=180, end=50, fill=cor, width=lw + 4)
        d.line([(cx + r * .3, cy - r * .1), (cx, cy + r * .15), (cx, cy + r * .4)], fill=cor, width=lw + 4)
        d.ellipse((cx - r * .12, cy + r * .58, cx + r * .12, cy + r * .82), fill=cor)
    elif nome == "whats":
        d.ellipse((cx - r * .8, cy - r * .8, cx + r * .8, cy + r * .8), outline=cor, width=lw)
        d.polygon([(cx - r * .62, cy + r * .45), (cx - r * .9, cy + r * .92), (cx - r * .3, cy + r * .72)], fill=cor)
        # cifrão no balão (orçamento)
        from PIL import ImageFont
        f = ImageFont.truetype(ca.ANTON, int(r * 1.05))
        d.text((cx, cy + r * .02), "$", font=f, fill=cor, anchor="mm")


def capa(titulo, icone, destino):
    """Story 9:16: o Instagram recorta o CÍRCULO do centro como capa do destaque."""
    im = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(im)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(ca.ROXO[i] * (1 - t) + ca.ROXO_ESC[i] * t) for i in range(3)) + (255,))
    cx, cy, R = W // 2, H // 2, 420
    brilho = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(brilho).ellipse((cx - R, cy - R, cx + R, cy + R), fill=ca.ROXO + (255,))
    im.alpha_composite(brilho.filter(ImageFilter.GaussianBlur(40)))
    d = ImageDraw.Draw(im)
    d.ellipse((cx - R, cy - R, cx + R, cy + R), outline=ca.LARANJA, width=26)
    _icone(d, icone, cx, cy, 240)
    # nome embaixo (aparece só no story, a capa recortada fica limpa)
    from PIL import ImageFont
    f = ImageFont.truetype(ca.ANTON, 120)
    t = titulo.upper()
    d.text(((W - d.textlength(t, font=f)) / 2, cy + R + 90), t, font=f, fill=BRANCO)
    lg = ca.logo(520)
    im.alpha_composite(lg, ((W - lg.width) // 2, 180))
    im.convert("RGB").save(destino, quality=94)
    return destino


def fazer_capas():
    DIR.mkdir(parents=True, exist_ok=True)
    saidas = [capa(t, i, DIR / f"capa_{n}.jpg") for n, (t, i, _) in enumerate(DESTAQUES, 1)]
    # folha para conferir: o círculo recortado como o Instagram mostra
    folha = Image.new("RGB", (len(saidas) * 260, 320), (15, 18, 26))
    d = ImageDraw.Draw(folha)
    for k, (s, (t, _, _)) in enumerate(zip(saidas, DESTAQUES)):
        im = Image.open(s).crop((W // 2 - 430, H // 2 - 430, W // 2 + 430, H // 2 + 430)).resize((220, 220))
        m = Image.new("L", (220, 220), 0)
        ImageDraw.Draw(m).ellipse((0, 0, 219, 219), fill=255)
        folha.paste(im, (k * 260 + 20, 20), m)
        d.text((k * 260 + 130 - len(t) * 5, 260), t, fill="white")
    folha.save(DIR / "_folha_capas.jpg", quality=90)
    return saidas


def _stories_do_tema(fonte, ig):
    """Imagens extras de cada destaque (já existentes, sem gerar nada novo)."""
    pastas = sorted(ca.DIR.glob("2026*/meta.json"))
    if fonte == "cta":
        return [str(p.parent / "slide_6.jpg") for p in pastas[-1:]]
    if fonte == "fotos":
        return [str(p.parent / "slide_1.jpg") for p in pastas[-3:]]
    if fonte == "carrosseis":
        return [str(p.parent / f"slide_{k}.jpg") for p in pastas[-2:] for k in (2, 3)]
    return []


def criar():
    sys.path.insert(0, str(ca.NSN))
    from services.instagram.postar import InstagramPostar
    est = json.loads(ESTADO.read_text("utf-8")) if ESTADO.exists() else {}
    ig = InstagramPostar(ca.CONTA)
    capas = fazer_capas()
    for (titulo, _, fonte), cap in zip(DESTAQUES, capas):
        if est.get(titulo, {}).get("destaque"):
            print(f"{titulo}: já existe")
            continue
        ids = [ig.story(str(cap))]
        time.sleep(15)
        for extra in _stories_do_tema(fonte, ig):
            if Path(extra).exists():
                ids.append(ig.story(extra))
                time.sleep(15)
        time.sleep(10)
        did = ig.criar_destaque(titulo, ids)
        est[titulo] = {"destaque": did, "stories": ids}
        ESTADO.write_text(json.dumps(est, ensure_ascii=False, indent=1), "utf-8")
        print(f"{titulo}: destaque {did} com {len(ids)} stories", flush=True)
        time.sleep(30)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if "--criar" in sys.argv:
        criar()
    else:
        print(fazer_capas())
