# -*- coding: utf-8 -*-
"""fx_branding.py — CLIPS DE BRANDING/TEXTO (intro, outro, cold open, transição narrativa).

Clips de moldura do vídeo, todos baseados em texto sobre fundo (sem estado
mutável, sem depender de outras funções build_*). Extraído de fx_clips.py em
2026-07-11. fx_clips.py re-exporta tudo isto (fachada), então os imports
externos (story_pipeline) não mudaram.
"""
import os
import subprocess
from pathlib import Path

from fx_assets import FPS, H, QP, W
from fx_subtitles import _text_block_png
from fx_detect import sfx_duration

_CTA_FRASES = Path(__file__).resolve().parent.parent / "workspace" / "assets" / "cta_frases.json"


def frase_cta(seed=None):
    """Frase de CTA do encerramento, sorteada por peso de assets/cta_frases.json
    (inscrever/comentar/like). Sem emoji (a fonte do PNG nao desenha) e sem as que
    falam de "capitulo" (historia fecha no proprio video). Fallback fixo."""
    import json
    import random
    import re
    try:
        cats = json.load(open(_CTA_FRASES, encoding="utf-8"))["categorias"]
        rnd = random.Random(str(seed))
        pool = []
        for nome in ("inscrever", "comentar", "like"):
            c = cats.get(nome) or {}
            for f in c.get("frases", []):
                f = re.sub(r"[^\w\s!?.,:'\-À-ú]", "", f).strip()
                fl = f.lower()
                if f and not any(x in fl for x in ("capítulo", "capitulo", "time a")):
                    pool += [f] * int(c.get("peso", 1))
        if pool:
            return rnd.choice(pool).upper()
    except Exception:
        pass
    return "SE INSCREVE PRA NAO PERDER A PROXIMA!"


def build_intro_clip(titulo, first_panel, out_path, duration=1.8, sfx_file=None, opening_track=None):
    """Gera um clip de abertura: 1º painel borrado/escuro + título + zoom lento.
    Se o SFX de abertura for mais longo que `duration` (ex: re:zero 2.72s), a
    intro ESTICA pra caber o SFX inteiro — ele é a assinatura sonora e deve
    tocar completo antes da narração começar."""
    sfx_file = opening_track or sfx_file
    from PIL import Image, ImageFilter, ImageEnhance
    sfx_dur = sfx_duration(sfx_file) if sfx_file else 0.0
    if sfx_dur > duration:
        duration = sfx_dur + 0.3  # respiro curto após o SFX terminar
    tmp = Path(str(out_path) + "_introbg.jpg")
    try:
        img = Image.open(first_panel).convert("RGB")
        sw, sh = W / img.width, H / img.height
        sc = max(sw, sh)
        img = img.resize((int(img.width * sc), int(img.height * sc)), Image.LANCZOS)
        left = (img.width - W) // 2; top = (img.height - H) // 2
        img = img.crop((left, top, left + W, top + H))
        img = img.filter(ImageFilter.GaussianBlur(22))
        img = ImageEnhance.Brightness(img).enhance(0.4)
        img.save(tmp, quality=85)
    except Exception:
        Image.new("RGB", (W, H), (10, 12, 24)).save(tmp)
    txt_png = Path(str(out_path) + "_introtxt.png")
    # (_text_block_png reduz a fonte sozinho se o titulo nao couber em 3 linhas)
    _text_block_png(txt_png, [(titulo, 96, (255, 255, 255))], y_center_frac=0.46)

    frames = int(duration * FPS)
    zoom = f"zoompan=z='min(zoom+0.0015,1.12)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={FPS}"
    audio_in = ["-i", str(sfx_file)] if sfx_file and Path(sfx_file).exists() else \
               ["-f", "lavfi", "-t", f"{duration:.2f}", "-i", "anullsrc=r=44100:cl=mono"]
    # Abertura estilo "Return by Death" (re:zero): a tela fica PRETA no primeiro
    # instante — só o som tocando no escuro (mistério) — e a imagem só REVELA
    # depois. black_hold = tempo preto antes do fade; reveal = duração do fade-in.
    # Ajustável por env INTRO_BLACK_HOLD / INTRO_REVEAL.
    try:
        black_hold = max(0.0, float(os.environ.get("INTRO_BLACK_HOLD", "0.15")))
    except ValueError:
        black_hold = 0.15
    try:
        reveal = max(0.2, float(os.environ.get("INTRO_REVEAL", "1.0")))
    except ValueError:
        reveal = 1.0
    # nunca passar da metade do clip (precisa sobrar imagem visível antes do fim)
    black_hold = min(black_hold, duration * 0.45)
    # o título também só aparece junto da imagem (não some o suspense)
    fc = (f"[0:v]{zoom},format=yuv420p[bg];"
          f"[bg][1:v]overlay=0:0:format=auto,"
          f"fade=t=in:st={black_hold:.2f}:d={reveal:.2f}:color=black,"
          f"fade=t=out:st={duration-0.2:.2f}:d=0.2[v];"
          f"[2:a]apad=whole_dur={duration:.2f},atrim=0:{duration:.2f}[a]")
    cmd = ["ffmpeg", "-y",
           "-loop", "1", "-t", f"{duration:.2f}", "-i", str(tmp),
           "-i", str(txt_png), *audio_in,
           "-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-t", f"{duration:.2f}",
           "-c:v", "libx264", "-preset", QP["preset"], "-crf", str(QP["crf"]), "-g", "30",
           "-c:a", "aac", "-b:a", QP["audio_bitrate"], "-ar", "44100", "-ac", "2", "-pix_fmt", "yuv420p", str(out_path)]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=90)
        ok = True
    except Exception:
        ok = False
    for f in (tmp, txt_png):
        try: f.unlink()
        except Exception: pass
    return ok


def build_outro_clip(out_path, duration=2.4, sfx_file=None,
                     linha1="INSCREVA-SE", linha2="e ative o sino",
                     linha3="PRÓXIMO CAPÍTULO EM BREVE"):
    """Gera um clip de fechamento: fundo escuro + CTA inscreva-se."""
    txt_png = Path(str(out_path) + "_outrotxt.png")
    _text_block_png(txt_png, [
        (linha1, 110, (255, 70, 70)),
        (linha3, 64, (255, 255, 255)),
    ], y_center_frac=0.5)
    frames = int(duration * FPS)
    pulse = f"zoompan=z='1+0.03*sin(on/{frames}*3.14159*4)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={FPS}"
    audio_in = ["-i", str(sfx_file)] if sfx_file and Path(sfx_file).exists() else \
               ["-f", "lavfi", "-t", f"{duration:.2f}", "-i", "anullsrc=r=44100:cl=mono"]
    fc = (f"color=c=0x0a0e1a:s={W}x{H}:d={duration:.2f}:r={FPS}[bg0];"
          f"[bg0]{pulse}[bg];"
          f"[bg][0:v]overlay=0:0,fade=t=in:st=0:d=0.2:color=black[v];"
          f"[1:a]apad=whole_dur={duration:.2f},atrim=0:{duration:.2f}[a]")
    cmd = ["ffmpeg", "-y", "-loop", "1", "-t", f"{duration:.2f}", "-i", str(txt_png),
           *audio_in,
           "-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-t", f"{duration:.2f}",
           "-c:v", "libx264", "-preset", QP["preset"], "-crf", str(QP["crf"]), "-g", "30",
           "-c:a", "aac", "-b:a", QP["audio_bitrate"], "-ar", "44100", "-ac", "2", "-pix_fmt", "yuv420p", str(out_path)]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=90)
        ok = True
    except Exception:
        ok = False
    try: txt_png.unlink()
    except Exception: pass
    return ok


# ══════════════════════════════════════════════════════════════════════════
# COLD OPEN — teaser de 3s antes do intro
# ══════════════════════════════════════════════════════════════════════════

def build_cold_open(teaser_text, bg_image, out_path, duration=3.0):
    """Gera um clip de cold open: imagem dramatica + texto teaser + vinheta/zoom.

    Mostra a imagem mais dramatica com vignette pesado e zoom,
    overlaid com texto grande (hook). Fade to black no final.
    Uso: inserir ANTES do intro_clip no pipeline.

    Args:
        teaser_text: texto curto de gancho (ex: "Voce abriria a porta?")
        bg_image: path da imagem de fundo (cena mais dramatica)
        out_path: path de saida do clip
        duration: duracao em segundos (default 3.0)
    """
    from PIL import Image, ImageFilter, ImageEnhance

    tmp_bg = Path(str(out_path) + "_coldbg.jpg")
    try:
        img = Image.open(bg_image).convert("RGB")
        sw, sh = W / img.width, H / img.height
        sc = max(sw, sh)
        img = img.resize((int(img.width * sc), int(img.height * sc)), Image.LANCZOS)
        left = (img.width - W) // 2
        top = (img.height - H) // 2
        img = img.crop((left, top, left + W, top + H))
        # Vignette: escurecer bordas
        img = ImageEnhance.Contrast(img).enhance(1.3)
        img = ImageEnhance.Brightness(img).enhance(0.6)
        img.save(tmp_bg, quality=90)
    except Exception:
        Image.new("RGB", (W, H), (5, 5, 15)).save(tmp_bg)

    # Texto overlay
    txt_png = Path(str(out_path) + "_coldtxt.png")
    _text_block_png(txt_png, [(teaser_text, 84, (255, 255, 255))], y_center_frac=0.50)

    frames = int(duration * FPS)
    # Zoom lento + vignette via ffmpeg
    zoom = (
        f"zoompan=z='min(zoom+0.003,1.20)':"
        f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"d={frames}:s={W}x{H}:fps={FPS}"
    )
    # Vinheta circular (simula com drawbox escuro nas bordas)
    vignette = "vignette=PI/3"

    fc = (
        f"[0:v]{zoom},{vignette},format=yuv420p[bg];"
        f"[bg][1:v]overlay=0:0:format=auto,"
        f"fade=t=in:st=0:d=0.3:color=black,"
        f"fade=t=out:st={duration - 0.4:.2f}:d=0.4:color=black[v]"
    )

    # Audio silencioso (cold open nao tem narracao)
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-t", f"{duration:.2f}", "-i", str(tmp_bg),
        "-loop", "1", "-t", f"{duration:.2f}", "-i", str(txt_png),
        "-f", "lavfi", "-t", f"{duration:.2f}", "-i", "anullsrc=r=44100:cl=mono",
        "-filter_complex", fc,
        "-map", "[v]", "-map", "2:a",
        "-t", f"{duration:.2f}",
        "-c:v", "libx264", "-preset", QP["preset"], "-crf", str(QP["crf"]), "-g", "30",
        "-c:a", "aac", "-b:a", QP["audio_bitrate"], "-ar", "44100", "-ac", "2",
        "-pix_fmt", "yuv420p",
        str(out_path),
    ]

    ok = False
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=60)
        if Path(out_path).exists() and Path(out_path).stat().st_size > 3000:
            ok = True
    except Exception:
        pass

    # Cleanup
    for f in (tmp_bg, txt_png):
        try:
            f.unlink()
        except Exception:
            pass

    return ok


# ══════════════════════════════════════════════════════════════════════════
# TRANSICAO NARRATIVA ANIMADA
# ══════════════════════════════════════════════════════════════════════════

NARRATIVE_TRANSITIONS = [
    "Enquanto isso...",
    "3 anos depois...",
    "Do outro lado da cidade...",
    "Naquele mesmo instante...",
    "Horas antes...",
    "No dia seguinte...",
    "Longe dali...",
    "Ninguem sabia, mas...",
    "O tempo passou...",
    "De volta ao presente...",
]


def build_narrative_transition(text, out_path, duration=2.0, style="fade_text"):
    """Gera clip de transicao narrativa animada.

    Fundo escuro com texto centralizado que aparece com animacao.
    Usado entre cenas com moods muito diferentes.

    Args:
        text: texto da transicao (ex: "Enquanto isso...")
        out_path: path de saida
        duration: duracao em segundos (default 2.0)
        style: "fade_text" | "typewriter" | "slide_up"
    """
    frames = int(duration * FPS)

    # Gerar texto PNG
    txt_png = Path(str(out_path) + "_nartxt.png")
    _text_block_png(txt_png, [(text, 72, (230, 230, 230))], y_center_frac=0.50)

    # Estilos de animacao.
    # zoompan PRIMEIRO: com imagem parada ele expande o 1o quadro em `frames`
    # quadros. Se o fade vier antes, esse 1o quadro ja sai escurecido e o texto
    # fica preto a cartela inteira. alpha=1 faz o fade na transparencia (o
    # fade comum escurece o RGB e deixa texto preto sobre o fundo escuro).
    if style == "typewriter":
        # Simula typewriter com fade-in rapido + leve zoom
        text_anim = (
            f"zoompan=z='min(zoom+0.001,1.05)':"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d={frames}:s={W}x{H}:fps={FPS},"
            f"fade=t=in:st=0.3:d=0.15:alpha=1"
        )
    elif style == "slide_up":
        # Texto sobe de baixo
        text_anim = (
            f"zoompan=z='1.0':"
            f"x='iw/2-(iw/zoom/2)':y='max(ih/2-(ih/zoom/2), ih/2-(ih/zoom/2) - on*0.3)':"
            f"d={frames}:s={W}x{H}:fps={FPS},"
            f"fade=t=in:st=0.2:d=0.4:alpha=1"
        )
    else:
        # fade_text: fade in suave + zoom sutil no texto
        text_anim = (
            f"zoompan=z='min(zoom+0.0012,1.08)':"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d={frames}:s={W}x{H}:fps={FPS},"
            f"fade=t=in:st=0.2:d=0.6:alpha=1,"
            f"fade=t=out:st={duration - 0.4:.2f}:d=0.4:alpha=1"
        )

    fc = (
        f"color=c=0x0a0c14:s={W}x{H}:d={duration:.2f}:r={FPS}[bg];"
        f"[1:v]{text_anim}[txt];"
        f"[bg][txt]overlay=0:0:format=auto,"
        f"fade=t=in:st=0:d=0.2:color=black,"
        f"fade=t=out:st={duration - 0.3:.2f}:d=0.3:color=black[v]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-t", f"{duration:.2f}", "-i", f"color=c=0x0a0c14:s={W}x{H}:r={FPS}",
        "-i", str(txt_png),  # quadro unico: o zoompan gera a duracao inteira
        "-f", "lavfi", "-t", f"{duration:.2f}", "-i", "anullsrc=r=44100:cl=mono",
        "-filter_complex", fc,
        "-map", "[v]", "-map", "2:a",
        "-t", f"{duration:.2f}",
        "-c:v", "libx264", "-preset", QP["preset"], "-crf", str(QP["crf"]), "-g", "30",
        "-c:a", "aac", "-b:a", QP["audio_bitrate"], "-ar", "44100", "-ac", "2",
        "-pix_fmt", "yuv420p",
        str(out_path),
    ]

    ok = False
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=60)
        if Path(out_path).exists() and Path(out_path).stat().st_size > 2000:
            ok = True
    except Exception:
        pass

    try:
        txt_png.unlink()
    except Exception:
        pass

    return ok
