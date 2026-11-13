"""Gera o arquivo ASS: legendas palavra-a-palavra, gancho, faixa divisoria (handle + obra), marca d'agua, barra, keywords e CTA."""
import re
from .common import log


def _ts(t):
    t = max(0.0, float(t))
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def _esc(txt):
    return txt.replace("{", "(").replace("}", ")").replace("\\", "/")


def ass_color(hex_rgb, alpha="00"):
    """'#RRGGBB' -> '&HAABBGGRR'."""
    h = hex_rgb.lstrip("#")
    if len(h) != 6:
        return "&H0000D7FF"
    r, g, b = h[0:2], h[2:4], h[4:6]
    return f"&H{alpha}{b}{g}{r}".upper()


def _clean_word(w, upper=True):
    w = w.strip()
    w = re.sub(r"^[\"'(\[]+|[\"')\]]+$", "", w)
    return w.upper() if upper else w


def chunk_words(words, max_words=3, max_span=1.4, max_gap=0.6):
    chunks, cur = [], []
    for w in words:
        if cur:
            gap = w["s"] - cur[-1]["e"]
            span = w["e"] - cur[0]["s"]
            ends = cur[-1]["w"].rstrip().endswith((".", "!", "?", ","))
            if len(cur) >= max_words or gap > max_gap or span > max_span or ends:
                chunks.append(cur)
                cur = []
        cur.append(w)
    if cur:
        chunks.append(cur)
    return chunks


def _wrap(text, width=16):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > width:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(cur)
    return "\\N".join(lines[:3])


def build_ass(cfg, words, duration, plan, meta, keywords=(), channel=None, part_label=None):
    """words: ja remapeadas para o timeline cortado e so do criador. channel: dict do canal (handle, color)."""
    OW, OH = cfg["output"]["width"], cfg["output"]["height"]
    C, O = cfg["captions"], cfg["overlays"]
    accent = ass_color(channel["color"]) if channel and channel.get("color") else C["highlight_color"]
    handle = (channel or {}).get("handle") or O.get("watermark_text", "")
    div = plan.get("divider_out", 0)
    band = plan.get("band") or {"y": div, "h": 0}
    content_top = div + band.get("h", 0) if div else int(OH * 0.25)
    cap_y = (div + C["y_offset_from_divider"]) if div else int(OH * 0.62)
    cap_y = max(120, min(OH - 200, cap_y))
    hook_y = content_top + 230
    key_y = content_top + int((OH - content_top) * 0.45)
    hl = accent

    styles = [
        f"Style: Cap,{C['font']},{C['font_size']},{C['primary_color']},{hl},{C['outline_color']},&H80000000,-1,0,0,0,100,100,0,0,1,{C['outline']},{C['shadow']},5,40,40,0,1",
        f"Style: Hook,{O['hook_font']},{O['hook_font_size']},{hl},&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,1,0,1,8,4,8,60,60,0,1",
        f"Style: Mark,{C['font']},34,&H55FFFFFF,&H00FFFFFF,&H55000000,&H00000000,-1,0,0,0,100,100,0,0,1,2,0,9,30,30,30,1",
        f"Style: Band,{C['font']},34,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,1,0,1,1,0,4,0,0,0,1",
        f"Style: Seam,{C['font']},44,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,2,0,1,5,2,5,40,40,0,1",
        f"Style: Bar,Arial,20,{hl},&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1",
        f"Style: Key,Bangers,{C.get('keyword_font_size', 150)},{hl},&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,2,0,1,8,4,5,60,60,0,1",
        f"Style: CTA,{O['hook_font']},64,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,1,0,1,6,3,2,60,60,130,1",
    ]
    ev = []
    # --- legendas palavra a palavra (palavra ativa destacada + pop)
    if C.get("enabled", True) and words:
        chunks = chunk_words(words, C["max_words"], C["max_chunk_seconds"])
        for ci, ch in enumerate(chunks):
            toks = [_clean_word(w["w"], C.get("uppercase", True)) for w in ch]
            next_start = chunks[ci + 1][0]["s"] if ci + 1 < len(chunks) else duration
            for i, w in enumerate(ch):
                start = w["s"]
                end = ch[i + 1]["s"] if i + 1 < len(ch) else min(w["e"] + 0.25, next_start, duration)
                if end - start < 0.05:
                    end = start + 0.05
                parts = []
                for j, tok in enumerate(toks):
                    if not tok:
                        continue
                    if j == i:
                        anim = "\\t(0,70,\\fscx113\\fscy113)\\t(70,150,\\fscx100\\fscy100)" if C.get("pop_in", True) else ""
                        parts.append(f"{{\\c{hl}{anim}}}{_esc(tok)}{{\\r}}")
                    else:
                        parts.append(_esc(tok))
                text = f"{{\\an5\\pos({OW//2},{cap_y})}}" + " ".join(parts)
                ev.append(f"Dialogue: 2,{_ts(start)},{_ts(end)},Cap,,0,0,0,,{text}")
    # --- gancho (primeiros segundos)
    hook = (meta.get("hook") or "").strip()
    if O.get("hook") and hook:
        hs = min(O["hook_seconds"], max(1.5, duration - 1))
        text = (f"{{\\an8\\pos({OW//2},{hook_y})\\fscx0\\fscy0\\t(0,160,\\fscx108\\fscy108)\\t(160,240,\\fscx100\\fscy100)\\fad(0,250)}}"
                + _wrap(_esc(hook.upper()), 15))
        ev.append(f"Dialogue: 3,{_ts(0)},{_ts(hs)},Hook,,0,0,0,,{text}")
    # --- faixa divisoria: linha de destaque + handle a esquerda + obra/parte a direita
    if band.get("h"):
        by, bh = band["y"], band["h"]
        ev.append(f"Dialogue: 0,{_ts(0)},{_ts(duration)},Bar,,0,0,0,,{{\\an7\\pos(0,{by})\\p1\\c{hl}}}m 0 0 l {OW} 0 l {OW} 4 l 0 4{{\\p0}}")
        cy = by + bh // 2 + 2
        if handle:
            ev.append(f"Dialogue: 1,{_ts(0)},{_ts(duration)},Band,,0,0,0,,{{\\an4\\pos(36,{cy})}}{_esc(handle)}")
        right = []
        if cfg.get("band", {}).get("show_work", True) and meta.get("work"):
            right.append(_esc(str(meta["work"]).upper()[:28]))
        if part_label:
            right.append(_esc(part_label))
        if right:
            ev.append(f"Dialogue: 1,{_ts(0)},{_ts(duration)},Band,,0,0,0,,{{\\an6\\pos({OW-36},{cy})\\c{hl}}}{'  |  '.join(right)}")
    else:
        if O.get("watermark") and handle:
            ev.append(f"Dialogue: 1,{_ts(0)},{_ts(duration)},Mark,,0,0,0,,{{\\an9\\pos({OW-30},30)}}{_esc(handle)}")
        seam = plan.get("seam") or {}
        if div and seam.get("overlap"):
            right = []
            if cfg.get("band", {}).get("show_work", True) and meta.get("work"):
                right.append(_esc(str(meta["work"]).upper()[:28]))
            if part_label:
                right.append(_esc(part_label))
            if right:
                text = (f"{{\\an5\\pos({OW//2},{div})\\fscx0\\fscy0\\t(0,200,\\fscx106\\fscy106)\\t(200,300,\\fscx100\\fscy100)}}" + "  |  ".join(right))
                ev.append(f"Dialogue: 2,{_ts(0)},{_ts(duration)},Seam,,0,0,0,,{text}")
    # --- barra de progresso (desenho vetorial escalado no tempo)
    if O.get("progress_bar"):
        h = 10
        rect = f"m 0 0 l {OW} 0 l {OW} {h} l 0 {h}"
        ev.append(f"Dialogue: 0,{_ts(0)},{_ts(duration)},Bar,,0,0,0,,{{\\an7\\pos(0,{OH-h})\\p1\\alpha&H99&\\c&H000000&}}{rect}{{\\p0}}")
        ev.append(f"Dialogue: 1,{_ts(0)},{_ts(duration)},Bar,,0,0,0,,{{\\an7\\pos(0,{OH-h})\\p1\\fscx0\\t(0,{int(duration*1000)},\\fscx100)}}{rect}{{\\p0}}")
    # --- keywords de impacto
    if O.get("keywords"):
        for k in keywords:
            t = float(k["t"])
            txt = _clean_word(str(k["text"]))[:18]
            if not txt or t >= duration - 0.5:
                continue
            text = (f"{{\\an5\\pos({OW//2},{key_y})\\fscx0\\fscy0\\t(0,110,\\fscx118\\fscy118)\\t(110,190,\\fscx100\\fscy100)\\fad(0,150)}}" + _esc(txt))
            ev.append(f"Dialogue: 4,{_ts(t)},{_ts(min(t + 1.3, duration))},Key,,0,0,0,,{text}")
    # --- CTA final em texto (so quando nao ha overlay animado)
    cta = (meta.get("cta") or O.get("cta_text") or "").strip()
    if O.get("cta") and cta and duration > 8 and not O.get("cta_overlay"):
        cs = max(0.0, duration - O["cta_seconds"])
        text = "{\\an2\\fad(200,0)\\fscx90\\fscy90\\t(0,160,\\fscx100\\fscy100)}" + _esc(cta.upper())
        ev.append(f"Dialogue: 3,{_ts(cs)},{_ts(duration)},CTA,,0,0,0,,{text}")

    header = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {OW}", f"PlayResY: {OH}", "WrapStyle: 2", "ScaledBorderAndShadow: yes", "",
              "[V4+ Styles]",
              "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
              *styles, "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    log(f"legendas: {len(ev)} eventos ASS")
    return "\n".join(header + ev) + "\n"
