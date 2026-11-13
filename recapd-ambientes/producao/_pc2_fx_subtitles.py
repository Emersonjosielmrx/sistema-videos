# -*- coding: utf-8 -*-
"""fx_subtitles.py — TEXTO NA TELA (legendas/karaokê/nametag/watermark) + censura de vídeo legada.
render_subtitles*, burn_subtitles, censurar_video, fontes (_load_font).

Parte do motor de efeitos — mapa completo na fachada effects_engine.py.
Split mecânico verbatim do _PRE_SPLIT_effects_engine.py.bak (2026-07-04).
"""
import random
import subprocess
import os
import re
from pathlib import Path
from fx_assets import H, QP, W




# ══════════════════════════════════════════════════════════════════════════
# SEÇÃO 4E: INTRO HOOK + OUTRO CTA (branding)
# ══════════════════════════════════════════════════════════════════════════

def _text_block_png(out_png, lines_styles, y_center_frac=0.5):
    """Renderiza um bloco de linhas (cada uma com (texto, fontsize, cor)) centralizado.

    lines_styles: lista de (texto, fontsize, (r,g,b)). Retorna o PNG 1080x1920.
    """
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    rendered = []
    total_h = 0
    for text, fs, color in lines_styles:
        font = _load_font(fs)
        lines = _wrap_lines(text, font, draw, max_w=int(W * 0.88))
        lh = int(fs * 1.2)
        for ln in lines:
            rendered.append((ln, font, color, lh))
            total_h += lh
    y = int(H * y_center_frac) - total_h // 2
    for ln, font, color, lh in rendered:
        bbox = draw.textbbox((0, 0), ln, font=font, stroke_width=8)
        x = (W - (bbox[2] - bbox[0])) // 2 - bbox[0]
        draw.text((x, y), ln, font=font, fill=(*color, 255),
                  stroke_width=8, stroke_fill=(0, 0, 0, 235))
        y += lh
    img.save(out_png)
    return out_png
# SEÇÃO 5B: LEGENDAS QUEIMADAS (estilo Shorts) — Ponto F
# Este ffmpeg não tem libass/drawtext, então renderizamos cada legenda como PNG
# transparente com PIL e sobrepomos via filtro overlay (sem dependências novas).
# ══════════════════════════════════════════════════════════════════════════

# Fontes bold disponíveis no macOS (heavy → bom pra Shorts)
_FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Impact.ttf",
    "/System/Library/Fonts/Supplemental/Arial Black.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Helvetica Bold.ttf",
    "/System/Library/Fonts/Impact.ttf",
    "/Library/Fonts/Impact.ttf",
    "/Library/Fonts/Arial Black.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "/Library/Fonts/Helvetica Bold.ttf",
]

# Fallback de fontes populares em Linux/Windows, se necessário
# (ex: para ambiente Docker ou CI/CD headless)
_FONT_CANDIDATES_FALLBACK = [
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", # Linux
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",        # Linux
    "C:/Windows/Fonts/impact.ttf",                                  # Windows
    "C:/Windows/Fonts/arialbd.ttf",                                 # Windows
]


def _load_font(size):
    from PIL import ImageFont
    for fp in _FONT_CANDIDATES + _FONT_CANDIDATES_FALLBACK:
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
    return lines[:3]  # no máx 3 linhas


def detect_context(text):
    """T6: detecta o TOM da frase p/ estilo de legenda (porte do SubtitleProcessor do n8n).
    Retorna 'shout'|'whisper'|'thought'|'emphasis'|'normal'. Ordem: emphasis(!!)>shout(!)>
    whisper(...)>thought(*) — !! checado antes de ! pra não virar shout."""
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


# Estilo por contexto (NOSSO formato PNG, não ASS). (mult_fontsize, cor_RGB|None=branco).
_SUB_CONTEXT_STYLE = {
    "normal":   (1.00, None),
    "shout":    (1.22, None),              # maior, outline forte (tratado no render)
    "whisper":  (0.82, (190, 190, 200)),   # menor, cinza
    "thought":  (0.90, (200, 200, 235)),   # leve azulado (pensamento)
    "emphasis": (1.10, (255, 214, 60)),    # amarelo
}


def _render_caption_png(text, out_png, fontsize=65, highlight_idx=None,
                        highlight_color=(255, 214, 60)):
    """Renderiza uma legenda como PNG transparente (recortado na região do texto).

    Branco com contorno preto grosso, embaixo-centro. Retorna (png, x, y) com a
    posição do recorte no canvas 1080x1920, pra overlay leve (pouca memória).

    highlight_idx: índice da palavra (na contagem global do texto) a destacar em
    amarelo (estilo karaokê). None = sem destaque (legenda estática).
    """
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # T6: estilo por contexto (SUB_CONTEXT=1). Ajusta fontsize/cor base pelo tom da frase.
    _ctx_color = None
    _ctx_stroke_boost = 0
    if os.environ.get("SUB_CONTEXT", "0") == "1":
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
    # Base: ~85-88% da altura (área de leitura de Shorts, evita balões)
    y0 = int(H * 0.85) - total_h
    stroke = 8 + _ctx_stroke_boost
    _base_fill = (*_ctx_color, 255) if _ctx_color else (255, 255, 255, 255)
    word_counter = 0  # índice global da palavra (pra casar com highlight_idx)
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
            # desenha palavra a palavra pra colorir a ativa
            cx = x
            for word in line.split():
                color = (*highlight_color, 255) if word_counter == highlight_idx \
                    else _base_fill
                draw.text((cx, y), word, font=font, fill=color,
                          stroke_width=stroke, stroke_fill=(0, 0, 0, 235))
                cx += draw.textlength(word, font=font) + space_w
                word_counter += 1

    # Recorta só a região do texto (com folga) → PNG pequeno, overlay barato
    bbox = img.getbbox()
    if not bbox:
        return None
    pad = 6
    cx0 = max(0, bbox[0] - pad); cy0 = max(0, bbox[1] - pad)
    cx1 = min(W, bbox[2] + pad); cy1 = min(H, bbox[3] + pad)
    img.crop((cx0, cy0, cx1, cy1)).save(out_png)
    return (out_png, cx0, cy0)


def render_subtitles(entries, tmp_dir, offsets=None):
    """Gera PNGs das legendas com timing cumulativo.

    entries: lista de (texto, duracao_segundos) na ORDEM dos clips.
    offsets: se fornecido, lista de timestamps absolutos de início para cada entry.
             Usado quando as legendas são filtradas (ex: só narrador) e os tempos
             não são mais sequenciais.
    Retorna lista de dicts {png, start, end} (só pros painéis com texto).
    """
    tmp_dir = Path(tmp_dir)
    subs = []
    t = 0.0
    for i, (text, dur) in enumerate(entries):
        dur = max(0.4, float(dur or 0))
        if offsets:
            start = offsets[i]
            end = start + dur
        else:
            start, end = t, t + dur
            t = end
        if not (text or "").strip():
            continue
        png = tmp_dir / f"_cap_{i:03d}.png"
        res = _render_caption_png(text, png)
        if res:
            _, x, y = res
            subs.append({"png": str(png), "x": x, "y": y, "start": start, "end": end})
    return subs


def render_subtitles_progressive(entries, tmp_dir, offsets=None, word_times=None):
    """Legendas KARAOKÊ OTIMIZADO: a palavra ativa fica amarela, sincronizada por tempo.

    word_times (MELHORIA WordBoundary): lista alinhada às entries; cada item é a lista de
    [start_s,end_s,word] REAL do edge-tts (sidecar .words.json). Quando presente p/ a entry,
    usa o timing REAL de cada palavra (mata o drift do karaokê); senão, estimativa por len().

    OTIMIZAÇÃO: Em vez de 1 PNG por palavra (que gerava centenas de overlays e timeout),
    gera 1 PNG a cada CHUNK de 3 palavras. Dentro de cada chunk, a palavra destacada
    muda — mas o total de PNGs fica ~3x menor que o original.

    Sem timestamps do TTS, estima o timing dividindo a duração do clip igualmente
    entre as palavras. Reusa o mesmo wrap/layout da legenda estática.

    offsets: se fornecido, lista de timestamps absolutos de início para cada entry.
    """
    tmp_dir = Path(tmp_dir)
    subs = []
    t = 0.0
    CHUNK_SIZE = 5  # Palavras por PNG (aumentado de 3 pra 5 pra gerar menos PNGs)

    for i, (text, dur) in enumerate(entries):
        dur = max(0.4, float(dur or 0))
        if offsets:
            start = offsets[i]
        else:
            start = t
            t += dur
        words = (text or "").strip().split()
        if not words:
            continue
        n = len(words)
        # MELHORIA WordBoundary: usa timing REAL de cada palavra se veio o sidecar da entry.
        wt_real = None
        if word_times and i < len(word_times) and word_times[i] and len(word_times[i]) == n:
            wt_real = word_times[i]  # [[start,end,word],...] relativo ao clip
        # Distribuição proporcional ao comprimento de cada palavra (fallback quando sem real)
        weights = [max(2, len(w)) for w in words]
        total_weight = sum(weights)
        word_durs = [dur * (wt / total_weight) for wt in weights]

        # Gerar PNGs em chunks: cada chunk destaca 1 palavra diferente
        # mas só cria 1 PNG por chunk (a palavra central do chunk fica amarela)
        for w_idx in range(0, n, CHUNK_SIZE):
            chunk_end = min(w_idx + CHUNK_SIZE, n)
            # Pra cada palavra do chunk, gerar um PNG com ela destacada
            for highlight in range(w_idx, chunk_end):
                png = tmp_dir / f"_capk_{i:03d}_{highlight:03d}.png"
                res = _render_caption_png(text, png, highlight_idx=highlight)
                if not res:
                    continue
                _, x, y = res
                if wt_real:
                    # timing REAL do edge-tts (relativo ao clip) + offset absoluto do clip
                    w_start = start + wt_real[highlight][0]
                    w_end = start + wt_real[highlight][1]
                else:
                    w_start = start + sum(word_durs[:highlight])
                    w_end = start + sum(word_durs[:highlight + 1])
                subs.append({"png": str(png), "x": x, "y": y,
                             "start": w_start, "end": w_end})

        # LIMITE DE SEGURANÇA: se já ultrapassou 300 PNGs, para de gerar karaokê
        # e volta pra estático pro restante (evita timeout no ffmpeg)
        if len(subs) > 300:
            # Restante em modo estático (1 PNG por entry)
            for j in range(i + 1, len(entries)):
                txt_j, dur_j = entries[j]
                dur_j = max(0.4, float(dur_j or 0))
                if offsets:
                    start_j = offsets[j]
                else:
                    start_j = t
                    t += dur_j
                if not (txt_j or "").strip():
                    continue
                png = tmp_dir / f"_capk_{j:03d}_static.png"
                res = _render_caption_png(txt_j, png)
                if res:
                    _, x, y = res
                    subs.append({"png": str(png), "x": x, "y": y,
                                 "start": start_j, "end": start_j + dur_j})
            break

    return subs


def render_name_tag(name, out_png, fontsize=58):
    """Renderiza o nome do personagem (tag) acima da legenda, em destaque.

    Retorna (png, x, y) recortado. Cor de destaque amarela com contorno preto.
    """
    from PIL import Image, ImageDraw
    name = (name or "").strip().upper()
    if not name:
        return None
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = _load_font(fontsize)
    bbox = draw.textbbox((0, 0), name, font=font, stroke_width=6)
    # Canto superior-esquerdo (abaixo do watermark central, longe da legenda)
    x = 60 - bbox[0]
    y = int(H * 0.12)
    draw.text((x, y), name, font=font, fill=(255, 214, 60, 255),
              stroke_width=6, stroke_fill=(0, 0, 0, 235))
    crop = img.getbbox()
    if not crop:
        return None
    img.crop(crop).save(out_png)
    return (out_png, crop[0], crop[1])


def render_watermark(text, tmp_dir, total_dur, fontsize=40):
    """Gera um watermark (handle do canal) fixo no topo, semitransparente.

    Retorna um spec de overlay {png,x,y,start,end} pro burn_subtitles.
    """
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = _load_font(fontsize)
    bbox = draw.textbbox((0, 0), text, font=font, stroke_width=4)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (W - tw) // 2 - bbox[0]
    y = int(H * 0.045)
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 200),
              stroke_width=4, stroke_fill=(0, 0, 0, 160))
    crop = img.getbbox()
    if not crop:
        return None
    out = Path(tmp_dir) / "_watermark.png"
    img.crop(crop).save(out)
    return {"png": str(out), "x": crop[0], "y": crop[1], "start": 0.0, "end": total_dur}


def censurar_video(video_in, windows, video_out, radius=45):
    """Censura com 3 níveis por janela de tempo (painéis +18).

    windows: lista de tuplas. Aceita 2 formatos:
      - (start, end)          → censura FORTE (retrocompat)
      - (start, end, nivel)   → 'forte' / 'leve' / 'intacto'
    nivel='forte': UM método só — tarja preta central (default) OU blur pesado.
                   Escolha por CENSURA_FORTE_MODO: 'tarja' (default) | 'blur'.
                   NUNCA os dois juntos.
    nivel='leve':  UM método só — shift de cor sutil (engana detector sem destruir cena).
    Uma passada só (re-encode do vídeo; áudio copiado).
    """
    parsed = []
    for w in windows:
        if len(w) == 3:
            s, e, niv = float(w[0]), float(w[1]), w[2]
        else:
            s, e, niv = float(w[0]), float(w[1]), "forte"
        if e > s and niv != "intacto":
            parsed.append((s, e, niv))
    if not parsed:
        import shutil as _shu
        _shu.copy2(str(video_in), str(video_out))
        return True
    fortes = [(s, e) for s, e, n in parsed if n == "forte"]
    leves = [(s, e) for s, e, n in parsed if n == "leve"]
    modo_forte = os.environ.get("CENSURA_FORTE_MODO", "tarja").strip().lower()
    filters = []
    if fortes:
        en_f = "+".join(f"between(t,{s:.2f},{e:.2f})" for s, e in fortes)
        if modo_forte == "blur":
            # MÉTODO ÚNICO: blur pesado na tela toda (sem tarja).
            filters.append(
                f"boxblur=luma_radius=28:luma_power=3:chroma_radius=28:chroma_power=3:enable='{en_f}'")
        else:
            # MÉTODO ÚNICO (default): tarja preta central sólida (sem blur junto).
            filters.append(
                f"drawbox=x=iw*0.10:y=ih*0.10:w=iw*0.80:h=ih*0.78:color=black:t=fill:enable='{en_f}'")
    if leves:
        # MÉTODO ÚNICO: grade de cor sutil (dessatura + leve brilho/contraste), sem blur/tarja.
        en_l = "+".join(f"between(t,{s:.2f},{e:.2f})" for s, e in leves)
        filters.append(f"hue=s=0.78:enable='{en_l}'")
        filters.append(f"eq=brightness=0.02:contrast=1.05:enable='{en_l}'")
    vf = ",".join(filters)
    cmd = [
        "ffmpeg", "-y", "-i", str(video_in),
        "-vf", vf,
        "-c:v", "libx264", "-preset", QP["preset"], "-crf", str(QP["crf"]), "-g", "30",
        "-c:a", "copy", "-movflags", "+faststart", "-pix_fmt", "yuv420p",
        str(video_out),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=1200)
        return Path(video_out).exists() and Path(video_out).stat().st_size > 0
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False


def render_subtitles_short(entries, tmp_dir, offsets=None, words_per_card=None, word_times=None):
    """Legenda DINÂMICA estilo Shorts/TikTok: 1-2 palavras na tela por vez.

    Em vez de mostrar a frase inteira (render_subtitles_progressive), mostra só
    um grupo de `words_per_card` palavras de cada vez, trocando rápido — deixa o
    vídeo mais dinâmico/moderno. Cada grupo vira 1 PNG curtinho centralizado.

    words_per_card: nº de palavras por card (default lê env SUB_WORDS_PER_CARD, senão 2).
    offsets: timestamps absolutos de início de cada entry (sincronia pós-xfade).
    word_times (WordBoundary): lista alinhada às entries; cada item é [[start,end,word],...]
      REAL do edge-tts (relativo ao clip). Quando presente e casa nº de palavras, usa o
      timing REAL de cada palavra (mata o drift legenda×balão); senão, estimativa por len().
    """
    import os as _os
    if words_per_card is None:
        try:
            words_per_card = max(1, int(_os.environ.get("SUB_WORDS_PER_CARD", "2")))
        except ValueError:
            words_per_card = 2
    tmp_dir = Path(tmp_dir)
    subs = []
    t = 0.0
    for i, (text, dur) in enumerate(entries):
        dur = max(0.4, float(dur or 0))
        start = offsets[i] if offsets else t
        if not offsets:
            t += dur
        words = (text or "").strip().split()
        if not words:
            continue
        # tempo de cada palavra proporcional ao tamanho (palavra longa dura mais)
        weights = [max(2, len(w)) for w in words]
        total_w = sum(weights)
        word_durs = [dur * (wt / total_w) for wt in weights]
        # WordBoundary: timing REAL de cada palavra (relativo ao clip) se veio o sidecar
        # e o nº de palavras casa. Mata o drift legenda×balão.
        wt_real = None
        if word_times and i < len(word_times) and word_times[i] and len(word_times[i]) == len(words):
            wt_real = word_times[i]
        # agrupa em cards de N palavras; cada palavra do card ACENDE amarelo no seu tempo
        for g in range(0, len(words), words_per_card):
            grp = words[g:g + words_per_card]
            card_text = " ".join(grp)
            for local_idx in range(len(grp)):
                png = tmp_dir / f"_capshort_{i:03d}_{g:03d}_{local_idx}.png"
                # highlight_idx é relativo ao card_text (que começa na palavra g)
                res = _render_caption_png(card_text, png, highlight_idx=local_idx)
                if not res:
                    continue
                _, x, y = res
                gi = g + local_idx
                if wt_real:
                    w_start = start + wt_real[gi][0]
                    w_end = start + wt_real[gi][1]
                else:
                    w_start = start + sum(word_durs[:gi])
                    w_end = start + sum(word_durs[:gi + 1])
                subs.append({"png": str(png), "x": x, "y": y, "start": w_start, "end": w_end})
    return subs


def burn_subtitles(video_in, subs, video_out, max_overlays_per_pass=30):
    """Sobrepõe os PNGs de legenda no vídeo em MÚLTIPLAS PASSADAS.

    O FFmpeg não suporta mais de ~100 overlays PNG numa única filter_complex
    (a cadeia de overlay fica enorme e o parser do FFmpeg estoura).

    SOLUÇÃO: divide os overlays em lotes de max_overlays_per_pass (default 30)
    e aplica em passadas sequenciais. Cada passada recebe o output da anterior.
    """
    if not subs:
        return False

    # Defesa: este burner é só de PNG. Ignora entradas sem "png" (ex: overlays webm
    # do karaokê HyperFrames, que são queimados em outro caminho) — evita KeyError 'png'.
    subs = [s for s in subs if isinstance(s, dict) and s.get("png")]
    if not subs:
        return False

    MAX_PER_PASS = max(max_overlays_per_pass, 100)  # Aumentado de 30 pra 100 (reduz passadas)
    batches = [subs[i:i + MAX_PER_PASS] for i in range(0, len(subs), MAX_PER_PASS)]
    temp_dir = Path(str(video_out)).parent
    temp_input = str(video_in)
    temp_outputs = []

    for batch_idx, batch in enumerate(batches):
        if batch_idx == len(batches) - 1:
            # Último batch → output final
            current_out = str(video_out)
        else:
            # Batch intermediário → arquivo temporário
            current_out = str(temp_dir / f"_subs_batch_{batch_idx:02d}.mp4")
            temp_outputs.append(current_out)

        inputs = ["-i", temp_input]
        for s in batch:
            inputs += ["-i", s["png"]]

        parts = []
        cur = "[0:v]"
        for idx, s in enumerate(batch, start=1):
            out = f"[v{idx}]"
            parts.append(
                f"{cur}[{idx}:v]overlay={s.get('x', 0)}:{s.get('y', 0)}:"
                f"enable='between(t,{s['start']:.2f},{s['end']:.2f})'{out}"
            )
            cur = out

        filter_complex = ";".join(parts)
        cmd = [
            "ffmpeg", "-y", *inputs,
            "-filter_complex", filter_complex,
            "-map", cur, "-map", "0:a?",
            "-c:v", "libx264", "-preset", QP["preset"], "-crf", str(QP["crf"]), "-g", "30",
            "-c:a", "copy",
            "-movflags", "+faststart", "-pix_fmt", "yuv420p",
            current_out,
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=1800)
            if not (Path(current_out).exists() and Path(current_out).stat().st_size > 0):
                return False
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False

        # Próxima passada usa o output atual como input
        temp_input = current_out

    # Cleanup: remover arquivos temporários
    for t in temp_outputs:
        try:
            Path(t).unlink()
        except Exception:
            pass

    return Path(video_out).exists() and Path(video_out).stat().st_size > 0
