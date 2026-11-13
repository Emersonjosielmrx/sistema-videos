"""branding_watermark: adiciona watermark + outro CTA ao video.

CPU-only (PIL pra texto, ffmpeg pra composicao).

Diferencas vs versao antiga:
  - Watermark gerado como PNG via PIL (fonte Arial Bold, stroke preto), nao drawtext
  - Outro eh um card simples com PIL+animacao ffmpeg (fade in)
  - Sem intro (intro eh papel do plugin historia_intro - futuro)
"""

import json
import os
import subprocess
from pathlib import Path

SUFFIX = "branded"
_BASE = Path(__file__).resolve().parent.parent.parent
_ASSETS = _BASE / "pos_producao" / "assets"
_LOGOS = _BASE / "pos_producao" / "logos"
_FFMPEG = r"D:\hipercool-materiais\bin\ffmpeg.exe"
_BRANDING = _ASSETS / "branding.json"

# 16/10/2026: nada de marca escrita aqui. Ate 15/10 este plugin carimbava
# "@InovareStories" no canto de todo video e num cartao final "Siga @...", o que
# esta entre as causas apontadas da suspensao dos 22 canais em 04/09/2026
# (D:\postador-de-videos\SPAM_BANIMENTO_2026-09-04.md). O @ do canal de destino e
# gravado na HORA DE POSTAR pela rede (D:\manhwa-react\mr\rede.py::rebrand), entao
# o padrao aqui e VAZIO: sem handle no assets\branding.json, o plugin nao estampa
# nada. Quem quiser marca de proposito preenche "handle" no branding.json.
_DEFAULT = {
    "handle": "",
    "cta_texto": "",
    "watermark_texto": "",
    "watermark_opacidade": 0.85,
}


def _carregar_branding():
    if not _BRANDING.exists():
        _BRANDING.parent.mkdir(parents=True, exist_ok=True)
        with open(_BRANDING, "w", encoding="utf-8") as f:
            json.dump(_DEFAULT, f, ensure_ascii=False, indent=2)
        return _DEFAULT
    try:
        with open(_BRANDING, encoding="utf-8") as f:
            cfg = json.load(f)
        merged = dict(_DEFAULT)
        merged.update(cfg)
        return merged
    except Exception:
        return _DEFAULT


def _gerar_watermark_png(texto: str, out_png: Path, w=1080, h=1920):
    """PNG transparente 1080x1920 com watermark no canto inferior direito.
    Estilo Shorts: branco com stroke preto grosso, fonte Impact/Bold."""
    import sys
    sys.path.insert(0, str(_BASE / "pos_producao"))
    from subtitles_veo import _load_font
    from PIL import Image, ImageDraw

    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    fs = 70
    font = _load_font(fs)
    bbox = draw.textbbox((0, 0), texto, font=font, stroke_width=8)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    margin = 60
    x = w - tw - margin - bbox[0]
    y = h - th - margin - bbox[1]
    draw.text((x, y), texto, font=font, fill=(255, 255, 255, 220),
              stroke_width=8, stroke_fill=(0, 0, 0, 230))
    # crop na regiao do texto
    bbox_full = img.getbbox()
    if bbox_full:
        pad = 8
        img.crop((max(0, bbox_full[0]-pad), max(0, bbox_full[1]-pad),
                  min(w, bbox_full[2]+pad), min(h, bbox_full[3]+pad))).save(out_png)
    return out_png


def _gerar_outro_mp4(cta: str, saida: Path, w=1080, h=1920, duracao=2.0, fps=30,
                     handle: str = ""):
    """Card simples com CTA grande, fade in/out, fundo preto.

    handle: so desenha se vier preenchido (vem da config). Ate 15/10 havia um
    "@InovareStories" escrito aqui no codigo, que aparecia mesmo com a config
    trocada."""
    import sys
    sys.path.insert(0, str(_BASE / "pos_producao"))
    from subtitles_veo import _load_font
    from PIL import Image, ImageDraw

    png = saida.with_suffix(".outro.png")
    img = Image.new("RGB", (w, h), (0, 0, 0))
    draw = ImageDraw.Draw(img)

    fs_cta = 100
    fs_handle = 60
    fnt_cta = _load_font(fs_cta)
    fnt_h = _load_font(fs_handle)

    cx = w // 2
    bbox = draw.textbbox((0, 0), cta, font=fnt_cta, stroke_width=10)
    cw = bbox[2] - bbox[0]
    ch = bbox[3] - bbox[1]
    y_cta = int(h * 0.45) - ch // 2
    draw.text((cx - cw // 2 - bbox[0], y_cta - bbox[1]), cta,
              font=fnt_cta, fill=(255, 255, 255),
              stroke_width=10, stroke_fill=(0, 0, 0))
    if handle:
        bbox = draw.textbbox((0, 0), handle, font=fnt_h, stroke_width=6)
        hw = bbox[2] - bbox[0]
        y_h = int(h * 0.62) - (bbox[3]-bbox[1]) // 2
        draw.text((cx - hw // 2 - bbox[0], y_h - bbox[1]),
                  handle, font=fnt_h, fill=(200, 200, 200),
                  stroke_width=6, stroke_fill=(0, 0, 0))
    img.save(png)

    n_frames = int(duracao * fps)
    cmd = [
        _FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(png),
        "-vf",
        f"zoompan=z='1.0':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"d={n_frames}:s={w}x{h}:fps={fps},"
        f"fade=t=in:st=0:d=0.3,fade=t=out:st={duracao-0.3:.2f}:d=0.3",
        "-frames:v", str(n_frames),
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-r", str(fps),
        "-movflags", "+faststart",
        str(saida),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    try:
        png.unlink()
    except Exception:
        pass
    return r.returncode == 0 and saida.exists()


def _concat(lista, saida: Path):
    """Wrapper do _concat_safe (3-passos com normalizacao de audio)."""
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).parent))
    from _concat_safe import _concat_safe
    return _concat_safe(lista, saida)


def _concat_xfade(lista, saida: Path, fade_dur: float = 0.3):
    """Wrapper com xfade (transicao cruzada) entre segmentos."""
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).parent))
    from propaganda_inteligente import _concat_xfade as _xf
    return _xf(lista, saida, fade_dur)


def processar(input_mp4: str, output_mp4: str, meta: dict) -> bool:
    cfg = _carregar_branding()
    if not Path(_FFMPEG).exists() or not Path(input_mp4).exists():
        return False

    wm_texto = (cfg.get("watermark_texto") or "").strip()
    cta_texto = (cfg.get("cta_texto") or "").strip()
    handle = (cfg.get("handle") or "").strip()
    # Config sem marca (o padrao desde 16/10) = plugin nao faz nada: devolve o
    # video como veio, em vez de carimbar texto vazio. Ver o cabecalho de _DEFAULT.
    if not wm_texto and not cta_texto:
        try:
            if str(Path(input_mp4).resolve()) != str(Path(output_mp4).resolve()):
                import shutil
                shutil.copy(input_mp4, output_mp4)
            return Path(output_mp4).exists()
        except Exception:
            return False

    # 1. aplica watermark via overlay (so se houver texto de marca)
    tmp_wm = Path(output_mp4).with_suffix(".wm.mp4")
    png = Path(output_mp4).with_suffix(".wm.png")
    if wm_texto:
        try:
            _gerar_watermark_png(wm_texto, png)
            cmd = [
                _FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
                "-i", str(input_mp4),
                "-i", str(png),
                "-filter_complex", "[0:v][1:v]overlay=0:0",
                "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
                "-c:a", "copy", "-pix_fmt", "yuv420p",
                "-movflags", "+faststart", str(tmp_wm),
            ]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if r.returncode != 0 or not tmp_wm.exists():
                return False
        finally:
            try:
                png.unlink()
            except Exception:
                pass
    else:
        import shutil
        shutil.copy(input_mp4, tmp_wm)

    # 2. gera outro e concatena (so se houver CTA)
    outro = Path(output_mp4).with_suffix(".outro.mp4")
    if not cta_texto or not _gerar_outro_mp4(cta_texto, outro, handle=handle):
        tmp_wm.replace(output_mp4)
        return Path(output_mp4).exists()
    ok = _concat_xfade([tmp_wm, str(outro)], Path(output_mp4), fade_dur=0.3)
    try:
        tmp_wm.unlink()
    except Exception:
        pass
    try:
        outro.unlink()
    except Exception:
        pass
    return ok