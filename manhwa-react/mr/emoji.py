"""Emoji colorido como PNG (Segoe UI Emoji via Pillow) para overlay nas keywords/reacoes (libass nao renderiza emoji colorido)."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from .common import log

_FONT = "C:/Windows/Fonts/seguiemj.ttf"


def emoji_png(cfg, emoji, size=220):
    """Gera (ou reutiliza) um PNG rgba com o emoji e um leve brilho. Retorna o caminho ou None."""
    emoji = (emoji or "").strip()
    if not emoji:
        return None
    base = Path(cfg["paths"]["assets"]) / "emoji"
    base.mkdir(parents=True, exist_ok=True)
    key = "_".join(f"{ord(c):x}" for c in emoji)[:40]
    p = base / f"e_{key}_{size}.png"
    if p.exists():
        return p
    try:
        font = ImageFont.truetype(_FONT, int(size * 0.5))  # Segoe UI Emoji so rasteriza em 109px; escalamos depois
        im = Image.new("RGBA", (size * 2, size * 2), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.text((size * 0.5, size * 0.4), emoji, font=ImageFont.truetype(_FONT, 109), embedded_color=True)
        bbox = im.getbbox()
        if not bbox:
            return None
        im = im.crop(bbox)
        im = im.resize((size, int(size * im.height / im.width)), Image.LANCZOS)
        glow = Image.new("RGBA", (im.width + 40, im.height + 40), (0, 0, 0, 0))
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
        sh.paste((0, 0, 0, 160), (0, 0), im.split()[3])
        glow.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)), (20, 24))
        glow.alpha_composite(im, (20, 20))
        glow.save(p)
        return p
    except Exception as e:  # noqa: BLE001
        log(f"emoji: falhou ({e})")
        return None
