# -*- coding: utf-8 -*-
"""Adaptacao de fx_subtitles.py do historias-em-frames pra Veo.

Mudancas vs original:
- W=1080, H=1920 (mesmo do historias-em-frames, ja correto).
- _FONT_CANDIDATES prioriza Impact/Arial Bold do Windows (o que existe).
- Nao importa censurar_video, send_telegram, etc.
"""

import os
import re
import subprocess
from pathlib import Path

W, H = 1080, 1920

# Fontes bold disponíveis no Windows
_FONT_CANDIDATES = [
    r"C:\Windows\Fonts\impact.ttf",
    r"C:\Windows\Fonts\arialbd.ttf",
    r"C:\Windows\Fonts\Arial Black.ttf",
    r"C:\Windows\Fonts\segoeuib.ttf",  # Segoe UI Bold
    "/System/Library/Fonts/Supplemental/Impact.ttf",
    "/Library/Fonts/Impact.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def _load_font(size):
    from PIL import ImageFont
    for fp in _FONT_CANDIDATES:
        if Path(fp).exists():
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _wrap_lines(text, font, draw, max_w):
    """Quebra o texto em linhas que cabem em max_w pixels."""
    words = (text or "").strip().replace("\n", " ").split()
    lines, cur = [], ""
    for w in words:
        test = f"{cur} {w}".strip()
        bbox = draw.textbbox((0, 0), test, font=font, stroke_width=8)
        if cur and (bbox[2] - bbox[0]) > max_w:
            lines.append(cur)
            cur = w
        else:
            cur = test
    if cur:
        lines.append(cur)
    return lines[:3]  # max 3 linhas


def detect_context(text):
    """Detecta tom: shout|whisper|thought|emphasis|normal."""
    t = (text or "")
    low = t.lower()
    if "!!" in t or re.search(r"import|crític|critic|vital", low):
        return "emphasis"
    if "!" in t or re.search(r"grito|berro|alto\b", low):
        return "shout"
    if "..." in t or re.search(r"sussurr|baixo|murmur", low):
        return "whisper"
    if "*" in t or re.search(r"pensa|imagin|reflet", low):
        return "thought"
    return "normal"


_SUB_CONTEXT_STYLE = {
    "normal":   (1.00, None),
    "shout":    (1.22, None),
    "whisper":  (0.82, (190, 190, 200)),
    "thought":  (0.90, (200, 200, 235)),
    "emphasis": (1.10, (255, 214, 60)),
}


def render_caption_png(text, out_png, fontsize=65, highlight_idx=None,
                       highlight_color=(255, 214, 60), context_aware=True):
    """Renderiza legenda como PNG transparente (recortado). Branco com stroke preto,
    embaixo-centro. Retorna (png, x, y) ou None.

    context_aware: se True, detecta shout/whisper etc e ajusta fontsize/cor.
    """
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    _ctx_color = None
    _ctx_stroke_boost = 0
    if context_aware and os.environ.get("SUB_CONTEXT", "1") == "1":
        _ctx = detect_context(text)
        _mult, _col = _SUB_CONTEXT_STYLE.get(_ctx, (1.0, None))
        fontsize = int(fontsize * _mult)
        _ctx_color = _col
        if _ctx == "shout":
            _ctx_stroke_boost = 3
    font = _load_font(fontsize)
    lines = _wrap_lines(text, font, draw, max_w=int(W * 0.86))
    if not lines:
        return None

    line_h = int(fontsize * 1.18)
    total_h = line_h * len(lines)
    y0 = int(H * 0.85) - total_h
    stroke = 8 + _ctx_stroke_boost
    _base_fill = (*_ctx_color, 255) if _ctx_color else (255, 255, 255, 255)
    space_w = draw.textlength(" ", font=font)
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font, stroke_width=stroke)
        lw = bbox[2] - bbox[0]
        x = (W - lw) // 2 - bbox[0]
        y = y0 + i * line_h
        if highlight_idx is None:
            draw.text((x, y), line, font=font, fill=_base_fill,
                      stroke_width=stroke, stroke_fill=(0, 0, 0, 235))
        else:
            cx = x
            word_counter = 0
            for word in line.split():
                color = (*highlight_color, 255) if word_counter == highlight_idx \
                    else _base_fill
                draw.text((cx, y), word, font=font, fill=color,
                          stroke_width=stroke, stroke_fill=(0, 0, 0, 235))
                cx += draw.textlength(word, font=font) + space_w
                word_counter += 1

    bbox = img.getbbox()
    if not bbox:
        return None
    pad = 6
    cx0 = max(0, bbox[0] - pad); cy0 = max(0, bbox[1] - pad)
    cx1 = min(W, bbox[2] + pad); cy1 = min(H, bbox[3] + pad)
    img.crop((cx0, cy0, cx1, cy1)).save(out_png)
    return (out_png, cx0, cy0)


def burn_caption_overlay(video_mp4, captions, out_mp4):
    """Aplica legenda(s) como overlay no video.

    captions: lista de dicts {png, x, y, start, end}. start/end em segundos.
    """
    if not captions:
        return False
    # constroi filter_complex
    parts = []
    inputs = ["[0:v]"]
    for i, cap in enumerate(captions):
        inputs.append(f"-loop 1 -t {cap['end'] - cap['start']:.3f} -i {cap['png']}")
    # overlay chain
    fc = "[0:v]"
    cur_v = "[0:v]"
    for i, cap in enumerate(captions):
        idx = i + 1
        next_v = f"[v{i}]"
        fc = f"{fc}[{idx}:v]overlay={cap['x']}:{cap['y']}:enable='between(t,{cap['start']},{cap['end']})'{next_v}"
        cur_v = next_v
    cmd = [
        r"D:\hipercool-materiais\bin\ffmpeg.exe", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(video_mp4),
    ]
    for cap in captions:
        cmd += ["-loop", "1", "-t", f"{cap['end'] - cap['start']:.3f}", "-i", cap['png']]
    cmd += ["-filter_complex", fc, "-map", cur_v, "-map", "0:a?",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
            "-c:a", "copy",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            str(out_mp4)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return r.returncode == 0 and Path(out_mp4).exists()