# -*- coding: utf-8 -*-
"""thumbnail_pro.py - Thumbnails profissionais compostas por genero.

Seleciona a cena mais dramatica, gera imagem 1280x720 com composicao:
imagem de fundo + gradient overlay + titulo viral em fonte bold com outline.
3 templates por genero (A/B/C) pra testes futuros.
"""
import os
import sys
import hashlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hp_common import PROJECT_DIR, IMAGES_DIR, log

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
except ImportError:
    Image = None

THUMB_DIR = PROJECT_DIR / "workspace" / "thumbnails"
THUMB_DIR.mkdir(parents=True, exist_ok=True)

THUMB_W, THUMB_H = 1280, 720

GENRE_COLORS = {
    "superacao": {"gradient": [(255, 180, 0, 200), (255, 80, 0, 220)], "text": (255, 255, 255)},
    "terror": {"gradient": [(20, 0, 0, 220), (80, 0, 0, 200)], "text": (255, 50, 50)},
    "misterio": {"gradient": [(0, 20, 50, 220), (0, 50, 80, 200)], "text": (100, 200, 255)},
    "motivacional": {"gradient": [(0, 80, 150, 180), (0, 40, 100, 220)], "text": (255, 255, 255)},
    "curiosidades": {"gradient": [(50, 0, 100, 200), (100, 0, 180, 220)], "text": (255, 220, 50)},
    "religioso": {"gradient": [(80, 60, 0, 180), (40, 30, 0, 220)], "text": (255, 230, 150)},
    "romance": {"gradient": [(150, 0, 80, 200), (80, 0, 50, 220)], "text": (255, 180, 200)},
    "comedia": {"gradient": [(0, 100, 0, 180), (0, 60, 0, 200)], "text": (255, 255, 0)},
    "drama": {"gradient": [(30, 30, 30, 220), (60, 40, 20, 200)], "text": (255, 255, 255)},
    "fantasia": {"gradient": [(30, 0, 80, 200), (80, 0, 150, 220)], "text": (200, 150, 255)},
}


def _pick_dramatic_scene(cenas):
    """Seleciona a cena com maior score emocional."""
    DRAMATIC_MOODS = {"tense_dramatic": 5, "sad_emotional": 4, "action": 5,
                      "romantic_sexy": 3, "funny_lighthearted": 2, "calm_chill": 1, "neutral_chill": 0}
    best_idx = 0
    best_score = 0
    for i, cena in enumerate(cenas):
        mood = cena.get("mood", "neutral_chill")
        score = DRAMATIC_MOODS.get(mood, 1)
        texto = cena.get("texto", "")
        if any(w in texto.lower() for w in ("morte", "morreu", "sangue", "grito", "explosao", "nunca")):
            score += 2
        if score > best_score:
            best_score = score
            best_idx = i
    return best_idx


def _wrap_text(text, max_chars=25):
    """Quebra texto em linhas de no maximo max_chars."""
    words = text.split()
    lines = []
    current = ""
    for w in words:
        if len(current) + len(w) + 1 > max_chars:
            if current:
                lines.append(current)
            current = w
        else:
            current = f"{current} {w}".strip()
    if current:
        lines.append(current)
    return lines[:3]


def generate_thumbnail(titulo, cenas, images, genero="superacao", story_id=None, template="A"):
    """Gera thumbnail profissional 1280x720.

    Args:
        titulo: titulo viral do video
        cenas: lista de cenas do roteiro
        images: lista de Paths das imagens geradas
        genero: genero da historia
        story_id: id pra cache
        template: A, B ou C (variante visual)

    Returns:
        Path da thumbnail ou None
    """
    if not Image:
        log("  thumbnail_pro: PIL nao disponivel")
        return None

    cache_name = f"{story_id or hashlib.md5(titulo.encode()).hexdigest()[:10]}_{template}.jpg"
    cached = THUMB_DIR / cache_name
    if cached.exists():
        return cached

    scene_idx = _pick_dramatic_scene(cenas)
    bg_img = images[scene_idx] if scene_idx < len(images) and images[scene_idx] else None

    if not bg_img or not Path(bg_img).exists():
        for img in images:
            if img and Path(img).exists():
                bg_img = img
                break

    if not bg_img:
        log("  thumbnail_pro: nenhuma imagem disponivel")
        return None

    try:
        bg = Image.open(str(bg_img)).convert("RGBA")
        bg = bg.resize((THUMB_W, THUMB_H), Image.LANCZOS)

        colors = GENRE_COLORS.get(genero, GENRE_COLORS["superacao"])

        if template == "A":
            gradient = Image.new("RGBA", (THUMB_W, THUMB_H), (0, 0, 0, 0))
            draw_g = ImageDraw.Draw(gradient)
            for y in range(THUMB_H):
                frac = y / THUMB_H
                c1, c2 = colors["gradient"]
                r = int(c1[0] * (1-frac) + c2[0] * frac)
                g = int(c1[1] * (1-frac) + c2[1] * frac)
                b = int(c1[2] * (1-frac) + c2[2] * frac)
                a = int(c1[3] * (1-frac) + c2[3] * frac)
                draw_g.line([(0, y), (THUMB_W, y)], fill=(r, g, b, a))
            bg = Image.alpha_composite(bg, gradient)

        elif template == "B":
            gradient = Image.new("RGBA", (THUMB_W, THUMB_H), (0, 0, 0, 0))
            draw_g = ImageDraw.Draw(gradient)
            for x in range(THUMB_W):
                frac = x / THUMB_W
                a = int(240 * frac)
                draw_g.line([(x, 0), (x, THUMB_H)], fill=(0, 0, 0, a))
            bg = Image.alpha_composite(bg, gradient)

        elif template == "C":
            dark = Image.new("RGBA", (THUMB_W, THUMB_H), (0, 0, 0, 160))
            bg = Image.alpha_composite(bg, dark)

        canvas = bg.convert("RGB")
        draw = ImageDraw.Draw(canvas)

        font_size = 72
        font_outline = 4
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", font_size)
        except (IOError, OSError):
            try:
                font = ImageFont.truetype("C:/Windows/Fonts/impact.ttf", font_size)
            except (IOError, OSError):
                font = ImageFont.load_default()
                font_outline = 0

        lines = _wrap_text(titulo.upper(), max_chars=22)
        text_color = colors["text"]
        y_start = THUMB_H // 2 - (len(lines) * (font_size + 10)) // 2

        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            tw = bbox[2] - bbox[0]
            x = (THUMB_W - tw) // 2
            y = y_start + i * (font_size + 10)

            if font_outline:
                for ox in range(-font_outline, font_outline + 1):
                    for oy in range(-font_outline, font_outline + 1):
                        if ox != 0 or oy != 0:
                            draw.text((x + ox, y + oy), line, font=font, fill=(0, 0, 0))

            draw.text((x, y), line, font=font, fill=text_color)

        canvas.save(str(cached), "JPEG", quality=90)
        log(f"  thumbnail_pro: gerada {cached.name} (template {template})")
        return cached

    except Exception as e:
        log(f"  thumbnail_pro: ERRO — {e}")
        return None


def generate_all_templates(titulo, cenas, images, genero="superacao", story_id=None):
    """Gera 3 variantes (A/B/C) pra A/B testing futuro."""
    results = {}
    for t in ("A", "B", "C"):
        path = generate_thumbnail(titulo, cenas, images, genero, story_id, template=t)
        if path:
            results[t] = path
    return results
