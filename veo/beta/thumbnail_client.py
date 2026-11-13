# -*- coding: utf-8 -*-
"""Thumbnail automatica 1080x1920 com texto grande + foto.

Usa Pillow. Gera 3 variantes pra A/B testing:
- Variante A: texto grande bold, sombra, cor neon
- Variante B: texto medio, fundo gradiente colorido
- Variante C: texto branco outline preto, foto blur de fundo
"""
import os, sys, json, time, random
from datetime import datetime

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "thumbnails")
os.makedirs(OUT_DIR, exist_ok=True)


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)


def quebra_texto(texto, max_chars_por_linha=18):
    """Quebra texto em linhas que cabem."""
    palavras = texto.split()
    linhas, cur = [], ""
    for p in palavras:
        if len(cur) + len(p) + 1 > max_chars_por_linha:
            if cur:
                linhas.append(cur)
            cur = p
        else:
            cur = (cur + " " + p).strip()
    if cur:
        linhas.append(cur)
    return linhas[:5]


def gerar_thumbnail(foto_path, fala, canal, variante="A", out_path=None):
    """Gera thumbnail 1080x1920 em uma das 3 variantes."""
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageFilter
    except ImportError:
        log("[thumb] pip install Pillow")
        return None

    W, H = 1080, 1920
    img = Image.new("RGB", (W, H), (0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Tenta carregar fonte
    font_paths = [
        "C:/Windows/Fonts/impact.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    font_big = None
    font_med = None
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                font_big = ImageFont.truetype(fp, 130)
                font_med = ImageFont.truetype(fp, 70)
                font_small = ImageFont.truetype(fp, 50)
                break
            except Exception:
                continue
    if not font_big:
        font_big = ImageFont.load_default()
        font_med = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Foto de fundo
    if foto_path and os.path.exists(foto_path):
        try:
            foto = Image.open(foto_path).convert("RGB")
            # Crop central
            ratio = max(W / foto.width, H / foto.height)
            nw, nh = int(foto.width * ratio), int(foto.height * ratio)
            foto = foto.resize((nw, nh), Image.LANCZOS)
            x = (W - nw) // 2
            y = (H - nh) // 2
            foto = foto.crop((x, y, x + W, y + H))
            if variante == "C":
                # Blur forte
                foto = foto.filter(ImageFilter.GaussianBlur(20))
            img.paste(foto, (0, 0))
        except Exception as e:
            log(f"[thumb] foto falhou: {e}")
    else:
        # Sem foto: gradiente
        for y in range(H):
            t = y / H
            r = int(50 + 205 * t)
            g = int(0 + 100 * (1 - t))
            b = int(150 + 50 * t)
            draw.line([(0, y), (W, y)], fill=(r, g, b))

    # Overlay escuro (40% preto)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 100))
    img = img.convert("RGBA")
    img.alpha_composite(overlay)
    img = img.convert("RGB")
    draw = ImageDraw.Draw(img)

    # Texto
    linhas = quebra_texto(fala, max_chars_por_linha=18)
    n = len(linhas)
    line_h = 130
    total_h = n * line_h
    start_y = (H - total_h) // 2 - 50

    if variante == "A":
        # Bold com sombra, cor neon
        cores = [(255, 0, 255), (0, 255, 200), (255, 255, 0), (0, 200, 255)]
        cor = random.choice(cores)
        for i, ln in enumerate(linhas):
            y = start_y + i * line_h
            # Sombra
            for dx, dy in [(-5, -5), (5, 5), (3, 3)]:
                draw.text((50 + dx, y + dy), ln, font=font_big, fill=(0, 0, 0))
            draw.text((50, y), ln, font=font_big, fill=cor)
    elif variante == "B":
        # Medio com outline grosso
        for i, ln in enumerate(linhas):
            y = start_y + i * line_h
            for dx, dy in [(-4, -4), (-4, 4), (4, -4), (4, 4), (-4, 0), (4, 0), (0, -4), (0, 4)]:
                draw.text((50 + dx, y + dy), ln, font=font_big, fill=(255, 255, 255))
            draw.text((50, y), ln, font=font_big, fill=(255, 0, 100))
    elif variante == "C":
        # Texto branco outline preto, fundo ja blur
        for i, ln in enumerate(linhas):
            y = start_y + i * line_h
            for dx, dy in [(dx, dy) for dx in (-3, 0, 3) for dy in (-3, 0, 3) if dx or dy]:
                draw.text((50 + dx, y + dy), ln, font=font_big, fill=(0, 0, 0))
            draw.text((50, y), ln, font=font_big, fill=(255, 255, 255))

    # Marca d'agua canal
    canal_txt = (canal or "VIRAL AI").upper()[:20]
    draw.rectangle([(0, 0), (W, 80)], fill=(0, 0, 0))
    draw.text((30, 15), canal_txt, font=font_med, fill=(255, 255, 0))

    # Salva
    if out_path is None:
        ts = int(time.time() * 1000)
        out_path = os.path.join(OUT_DIR, f"thumb_{variante}_{ts}.jpg")
    img.save(out_path, "JPEG", quality=85)
    log(f"[thumb] {variante}: {out_path}")
    return out_path


def gen_3_variants(foto_path, fala, canal):
    """Gera as 3 variantes (A, B, C)."""
    paths = {}
    for v in ["A", "B", "C"]:
        paths[v] = gerar_thumbnail(foto_path, fala, canal, variante=v)
    return paths


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("uso: thumbnail_client.py foto_path fala [canal] [variante(A|B|C)]")
        sys.exit(1)
    foto = sys.argv[1]
    fala = sys.argv[2]
    canal = sys.argv[3] if len(sys.argv) > 3 else "VIRAL AI"
    variante = sys.argv[4] if len(sys.argv) > 4 else "all"
    if variante == "all":
        out = gen_3_variants(foto, fala, canal)
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        out = gerar_thumbnail(foto, fala, canal, variante=variante)
        print(out)
