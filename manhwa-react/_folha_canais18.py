# -*- coding: utf-8 -*-
"""Folha de conferência: perfil + banner de cada canal novo (canais_novos_18nov.py)."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from canais_novos_18nov import CANAIS, RAIZ  # noqa: E402

W, H = 1600, 300
fonte = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 26)
folha = Image.new("RGB", (W, H * len(CANAIS)), (20, 20, 24))
d = ImageDraw.Draw(folha)
for i, ch in enumerate(CANAIS):
    p = RAIZ / ch["slug"]
    y = i * H
    if (p / "perfil.png").exists():
        folha.paste(Image.open(p / "perfil.png").resize((260, 260)), (10, y + 30))
    if (p / "banner.png").exists():
        folha.paste(Image.open(p / "banner.png").resize((480, 270)), (290, y + 25))
    if (p / "marca_dagua.png").exists():
        m = Image.open(p / "marca_dagua.png").convert("RGBA").resize((100, 100))
        folha.paste(m, (790, y + 30), m)
    d.text((910, y + 40), ch["name"], font=fonte, fill=(255, 255, 255))
    d.text((910, y + 80), ch["handle"], font=fonte, fill=(180, 180, 180))
    d.text((910, y + 120), "Aplicar por: " + ch["via"], font=fonte, fill=(255, 200, 0))
folha.save(RAIZ / "_NOVOS_18NOV.jpg", quality=88)
print(RAIZ / "_NOVOS_18NOV.jpg")
