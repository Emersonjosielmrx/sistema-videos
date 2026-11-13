"""Thumbnail 1080x1920: frame mais expressivo do criador + gancho grande + handle do canal (Pillow)."""
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from .common import log


def best_time(series, keeps, words):
    """Momento com a boca mais aberta (expressao) dentro dos trechos mantidos e perto de fala do criador."""
    speech = [(w["s"], w["e"]) for w in words if w.get("speaker") != "content"]
    best, bt = -1.0, None
    for t, v in series or []:
        if v is None or not any(a <= t <= b for a, b in keeps):
            continue
        if speech and not any(a - 0.5 <= t <= b + 0.5 for a, b in speech):
            continue
        if v > best:
            best, bt = v, t
    if bt is None and keeps:
        a, b = keeps[len(keeps) // 2]
        bt = (a + b) / 2
    return bt or 0.0


def _frame(video, t):
    cap = cv2.VideoCapture(str(video))
    cap.set(cv2.CAP_PROP_POS_MSEC, max(0.0, t) * 1000)
    ok, f = cap.read()
    cap.release()
    if not ok:
        return None
    return Image.fromarray(cv2.cvtColor(f, cv2.COLOR_BGR2RGB))


def _wrap(draw, text, font, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if draw.textlength(test, font=font) <= max_w or not cur:
            cur = test
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _hex(h, default=(255, 215, 0)):
    try:
        h = h.lstrip("#")
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    except Exception:  # noqa: BLE001
        return default


def make_thumb(cfg, video, t, plan, hook, out_path, handle=None, color=None):
    T = cfg.get("thumb", {})
    accent = _hex(color) if color else (255, 215, 0)
    OW, OH = cfg["output"]["width"], cfg["output"]["height"]
    src = _frame(video, t)
    if src is None:
        log("thumb: nao consegui ler o frame")
        return None
    canvas = Image.new("RGB", (OW, OH), (12, 12, 16))
    if plan.get("webcam"):
        x, y, w, h = plan["webcam"]["crop"]
        wh = plan["webcam"]["out_h"]
        z = float(T.get("webcam_zoom", 1.25))
        cw, chh = int(w / z), int(h / z)
        cx, cy = x + (w - cw) // 2, y + int((h - chh) * 0.3)
        web = src.crop((cx, cy, cx + cw, cy + chh)).resize((OW, wh), Image.LANCZOS)
        canvas.paste(web, (0, 0))
        cx0, cy0, cw2, ch2 = plan["content"]["crop"]
        cont = src.crop((cx0, cy0, cx0 + cw2, cy0 + ch2)).resize(tuple(plan["content"]["scale"]), Image.LANCZOS)
        seam = plan.get("seam") or {}
        ov = int(seam.get("overlap") or 0)
        mask_p = seam.get("mask")
        if ov and mask_p and Path(mask_p).exists():
            m = Image.open(mask_p).convert("L").resize(cont.size)
            canvas.paste(cont, (0, wh - ov), m)
        else:
            canvas.paste(cont, (0, plan["content"].get("out_y", wh)))
        text_y = wh + 150
    else:
        cx0, cy0, cw2, ch2 = plan["content"]["crop"]
        canvas.paste(src.crop((cx0, cy0, cx0 + cw2, cy0 + ch2)).resize((OW, OH), Image.LANCZOS), (0, 0))
        text_y = int(OH * 0.55)
    draw = ImageDraw.Draw(canvas)
    fonts = Path(cfg["paths"]["assets"]) / "fonts"
    try:
        font = ImageFont.truetype(str(fonts / T.get("font", "LuckiestGuy-Regular.ttf")), int(T.get("font_size", 120)))
        small = ImageFont.truetype(str(fonts / "Montserrat-ExtraBold.ttf"), 44)
    except Exception:  # noqa: BLE001
        font = ImageFont.truetype("C:/Windows/Fonts/impact.ttf", int(T.get("font_size", 120)))
        small = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 44)
    if hook:
        lines = _wrap(draw, hook.upper(), font, OW - 120)
        lh = int(font.size * 1.12)
        total = lh * len(lines)
        y0 = min(text_y, OH - total - 200)
        # faixa escura translucida atras do texto
        band = Image.new("RGBA", (OW, total + 60), (0, 0, 0, 110))
        canvas.paste(Image.alpha_composite(canvas.crop((0, y0 - 30, OW, y0 - 30 + total + 60)).convert("RGBA"), band).convert("RGB"), (0, y0 - 30))
        draw = ImageDraw.Draw(canvas)
        for i, line in enumerate(lines):
            tw = draw.textlength(line, font=font)
            x = (OW - tw) / 2
            y = y0 + i * lh
            draw.text((x, y), line, font=font, fill=accent, stroke_width=12, stroke_fill=(0, 0, 0))
    handle = handle or cfg["overlays"].get("watermark_text", "")
    if handle:
        draw.text((OW - 40 - draw.textlength(handle, font=small), 36), handle, font=small, fill=(255, 255, 255), stroke_width=4, stroke_fill=(0, 0, 0))
    out_path = Path(out_path)
    canvas.save(out_path, quality=92)
    log(f"thumb: {out_path.name} (t={t:.1f}s)")
    return out_path
