# -*- coding: utf-8 -*-
"""fx_subtitles.py — TEXTO NA TELA (legendas, karaokê, name tag, watermark) + censura.

Parte do motor de efeitos (ver mapa completo em effects_engine.py).
Tudo que desenha texto/tarja sobre o vídeo mora aqui.

  render_subtitles(entries, ...)            legendas estáticas (estilo Shorts).
  render_subtitles_progressive(...)         karaokê (palavra ativa destacada).
  render_name_tag(name, ...)                etiqueta com nome do personagem.
  render_watermark(text, ...)               marca d'água do canal.
  burn_subtitles(v_in, subs, v_out)         queima as legendas no vídeo (ffmpeg).
  censurar_video(v_in, windows, v_out)      tarja/mosaico nas janelas +18.
        (obs: a censura ATUAL do pipeline é na imagem, via censura_visual.py;
         esta é a legada de vídeo — ver CLAUDE.md antes de mexer.)
  _load_font / _wrap_lines / _render_caption_png   helpers de fonte/quebra/PNG.
  _FONT_CANDIDATES(_FALLBACK)               fontes procuradas no sistema.

Importa só fx_assets (W,H). fx_clips depende DELE (usa as fontes).
Mexa aqui pra: estilo/tamanho/cor de legenda, posição do watermark, name tag.
"""
import random
import shutil
import subprocess
import os
import re
from pathlib import Path
from fx_assets import W, H


# Fontes bold disponíveis no macOS (heavy -> bom pra Shorts)
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
    font = _load_font(fontsize)
    lines = _wrap_lines(text, font, draw, max_w=int(W * 0.86))
    if not lines:
        return None

    line_h = int(fontsize * 1.18)
    total_h = line_h * len(lines)
    # Base: ~85-88% da altura (área de leitura de Shorts, evita balões)
    y0 = int(H * 0.85) - total_h
    stroke = 8
    word_counter = 0  # índice global da palavra (pra casar com highlight_idx)
    space_w = draw.textlength(" ", font=font)
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font, stroke_width=stroke)
        lw = bbox[2] - bbox[0]
        x = (W - lw) // 2 - bbox[0]
        y = y0 + i * line_h
        if highlight_idx is None:
            draw.text((x, y), line, font=font, fill=(255, 255, 255, 255),
                      stroke_width=stroke, stroke_fill=(0, 0, 0, 235))
        else:
            # desenha palavra a palavra pra colorir a ativa
            cx = x
            for word in line.split():
                color = (*highlight_color, 255) if word_counter == highlight_idx \
                    else (255, 255, 255, 255)
                draw.text((cx, y), word, font=font, fill=color,
                          stroke_width=stroke, stroke_fill=(0, 0, 0, 235))
                cx += draw.textlength(word, font=font) + space_w
                word_counter += 1

    # Recorta só a região do texto (com folga) -> PNG pequeno, overlay barato
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


def render_subtitles_progressive(entries, tmp_dir, offsets=None):
    """Legendas KARAOKÊ OTIMIZADO: a palavra ativa fica amarela, sincronizada por tempo.

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
        per = dur / n  # duração por palavra

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
                w_start = start + highlight * per
                w_end = start + (highlight + 1) * per
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
    """Aplica mosaico/blur PESADO nas janelas de tempo [start,end] (painéis +18).

    windows: lista de (start, end) em segundos. Gera versão censurada pra Shorts.
    Uma passada só (re-encode do vídeo; áudio copiado).
    """
    windows = [(float(s), float(e)) for s, e in windows if e > s]
    if not windows:
        shutil.copy2(str(video_in), str(video_out))
        return True
    enable = "+".join(f"between(t,{s:.2f},{e:.2f})" for s, e in windows)
    # mosaico forte: pixelize via scale down/up + boxblur, só nas janelas
    vf = (f"boxblur=luma_radius={radius}:luma_power=2:"
          f"chroma_radius={radius}:chroma_power=2:enable='{enable}'")
    cmd = [
        "ffmpeg", "-y", "-i", str(video_in),
        "-vf", vf,
        "-c:v", "libx264", "-preset", "fast", "-crf", "23", "-g", "30",
        "-c:a", "copy", "-movflags", "+faststart", "-pix_fmt", "yuv420p",
        str(video_out),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=1200)
        return Path(video_out).exists() and Path(video_out).stat().st_size > 0
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False


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
            # Último batch -> output final
            current_out = str(video_out)
        else:
            # Batch intermediário -> arquivo temporário
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
            "-c:v", "libx264", "-preset", "fast", "-crf", "23", "-g", "30",
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

