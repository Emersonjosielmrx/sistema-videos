"""
Engine de motion graphics para shorts MS Energy.
Gera vídeos verticais (1080x1920) via ffmpeg com textos animados,
fotos com zoom/pan, e overlays da marca.
"""
import json
import subprocess
import shutil
import os
from pathlib import Path

DIR_PROJETO = Path(__file__).resolve().parent.parent
DIR_ASSETS = DIR_PROJETO / "assets"
DIR_CONFIG = DIR_PROJETO / "config"
DIR_TMP = DIR_PROJETO / "cache" / "tmp_render"

W, H = 1080, 1920
FPS = 30

def _cor_hex_to_ffmpeg(hex_cor):
    hex_cor = hex_cor.lstrip("#")
    return f"0x{hex_cor}"

def carregar_marca():
    with open(DIR_CONFIG / "marca.json", encoding="utf-8") as f:
        return json.load(f)

def _ffmpeg(*args, **kwargs):
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"] + list(args)
    subprocess.run(cmd, check=True, **kwargs)

def _ffprobe_duracao(video_path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)],
        capture_output=True, text=True
    )
    return float(r.stdout.strip())

def gerar_fundo_cor(cor_hex, duracao_s, output_path):
    """Gera vídeo de cor sólida vertical."""
    _ffmpeg(
        "-f", "lavfi", "-i",
        f"color=c={_cor_hex_to_ffmpeg(cor_hex)}:s={W}x{H}:d={duracao_s}:r={FPS}",
        "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
        str(output_path)
    )

def gerar_clip_texto(texto, duracao_s, output_path, cor_fundo="#1E3A5F",
                     cor_texto="white", fontsize=72, font="Impact",
                     posicao="center", fade_in=0.5, fade_out=0.3):
    """Gera clip com texto centralizado sobre fundo colorido."""
    texto_escaped = texto.replace("'", "’").replace(":", "\\:")

    drawtext = (
        f"drawtext=text='{texto_escaped}':"
        f"fontcolor={cor_texto}:fontsize={fontsize}:font='{font}':"
        f"x=(w-text_w)/2:y=(h-text_h)/2:"
        f"borderw=3:bordercolor=black@0.6"
    )

    if fade_in > 0:
        drawtext += f":alpha='if(lt(t,{fade_in}),t/{fade_in},1)'"

    _ffmpeg(
        "-f", "lavfi", "-i",
        f"color=c={_cor_hex_to_ffmpeg(cor_fundo)}:s={W}x{H}:d={duracao_s}:r={FPS}",
        "-vf", drawtext,
        "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
        str(output_path)
    )

def gerar_clip_foto(foto_path, duracao_s, output_path, texto=None,
                    zoom=True, cor_fundo="#1E3A5F", cor_texto="white",
                    fontsize=54, texto_pos="bottom"):
    """Gera clip com foto (zoom lento ken burns) + texto opcional."""
    foto_path = str(foto_path)

    filtros = []

    filtros.append(f"scale={W}:{H}:force_original_aspect_ratio=increase")
    filtros.append(f"crop={W}:{H}")

    if zoom:
        filtros.append(
            f"zoompan=z='min(zoom+0.001,1.15)':x='iw/2-(iw/zoom/2)':"
            f"y='ih/2-(ih/zoom/2)':d={duracao_s * FPS}:s={W}x{H}:fps={FPS}"
        )

    if texto:
        texto_escaped = texto.replace("'", "’").replace(":", "\\:")
        y_pos = f"h-{fontsize+80}" if texto_pos == "bottom" else f"{80}"
        filtros.append(
            f"drawtext=text='{texto_escaped}':"
            f"fontcolor={cor_texto}:fontsize={fontsize}:font='Impact':"
            f"x=(w-text_w)/2:y={y_pos}:"
            f"borderw=3:bordercolor=black@0.7:"
            f"box=1:boxcolor=black@0.4:boxborderw=15"
        )

    filtro_chain = ",".join(filtros)

    _ffmpeg(
        "-loop", "1", "-i", foto_path,
        "-t", str(duracao_s),
        "-vf", filtro_chain,
        "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
        str(output_path)
    )

def gerar_clip_hook(texto, duracao_s, output_path, cor_primaria="#F59E0B",
                    cor_fundo="#1E3A5F"):
    """Gera clip de hook (primeiros segundos) com texto grande + animação."""
    texto_escaped = texto.replace("'", "’").replace(":", "\\:")

    drawtext_main = (
        f"drawtext=text='{texto_escaped}':"
        f"fontcolor={_cor_hex_to_ffmpeg(cor_primaria)}:fontsize=90:font='Impact':"
        f"x=(w-text_w)/2:y=(h-text_h)/2:"
        f"borderw=4:bordercolor=black@0.8:"
        f"alpha='if(lt(t,0.3),t/0.3,1)'"
    )

    solar_emoji = (
        f"drawtext=text='☀️':fontsize=120:"
        f"x=(w-text_w)/2:y=(h/2)-200:"
        f"alpha='if(lt(t,0.5),0,if(lt(t,0.8),(t-0.5)/0.3,1))'"
    )

    _ffmpeg(
        "-f", "lavfi", "-i",
        f"color=c={_cor_hex_to_ffmpeg(cor_fundo)}:s={W}x{H}:d={duracao_s}:r={FPS}",
        "-vf", f"{drawtext_main},{solar_emoji}",
        "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
        str(output_path)
    )

def gerar_clip_cta(texto_cta, duracao_s, output_path, cor_accent="#10B981",
                   cor_fundo="#1E3A5F", watermark="@MSEnergySolar"):
    """Gera clip final de CTA com chamada pra ação."""
    texto_escaped = texto_cta.replace("'", "’").replace(":", "\\:")
    wm_escaped = watermark.replace("'", "’").replace(":", "\\:")

    cta_draw = (
        f"drawtext=text='{texto_escaped}':"
        f"fontcolor=white:fontsize=72:font='Impact':"
        f"x=(w-text_w)/2:y=(h/2)-60:"
        f"borderw=3:bordercolor=black@0.6:"
        f"box=1:boxcolor={_cor_hex_to_ffmpeg(cor_accent)}@0.8:boxborderw=20:"
        f"alpha='if(lt(t,0.5),t/0.5,1)'"
    )

    wm_draw = (
        f"drawtext=text='{wm_escaped}':"
        f"fontcolor=white@0.7:fontsize=36:font='Arial':"
        f"x=(w-text_w)/2:y=h-100"
    )

    seta = (
        f"drawtext=text='👇':fontsize=80:"
        f"x=(w-text_w)/2:y=(h/2)+80:"
        f"alpha='if(lt(t,0.8),0,if(lt(t,1.1),(t-0.8)/0.3,1))'"
    )

    _ffmpeg(
        "-f", "lavfi", "-i",
        f"color=c={_cor_hex_to_ffmpeg(cor_fundo)}:s={W}x{H}:d={duracao_s}:r={FPS}",
        "-vf", f"{cta_draw},{wm_draw},{seta}",
        "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
        str(output_path)
    )

def gerar_clip_comparativo(valor_antes, valor_depois, duracao_s, output_path,
                           cor_fundo="#1E3A5F", cor_destaque="#F59E0B"):
    """Gera clip de comparação de valores (antes x depois)."""
    antes_draw = (
        f"drawtext=text='ANTES':fontcolor=red:fontsize=48:font='Impact':"
        f"x=(w/2)-250:y=(h/2)-180:borderw=2:bordercolor=black@0.6:"
        f"alpha='if(lt(t,0.3),t/0.3,1)'"
    )

    valor_antes_draw = (
        f"drawtext=text='R$ {valor_antes}':fontcolor=red:fontsize=80:font='Impact':"
        f"x=(w/2)-350:y=(h/2)-100:borderw=3:bordercolor=black@0.6:"
        f"alpha='if(lt(t,0.5),t/0.5,1)'"
    )

    seta_draw = (
        f"drawtext=text='→':fontcolor=white:fontsize=100:"
        f"x=(w-text_w)/2:y=(h/2)-100:"
        f"alpha='if(lt(t,1.0),0,if(lt(t,1.3),(t-1.0)/0.3,1))'"
    )

    depois_draw = (
        f"drawtext=text='DEPOIS':fontcolor={_cor_hex_to_ffmpeg(cor_destaque)}:"
        f"fontsize=48:font='Impact':"
        f"x=(w/2)+50:y=(h/2)-180:borderw=2:bordercolor=black@0.6:"
        f"alpha='if(lt(t,1.5),0,if(lt(t,1.8),(t-1.5)/0.3,1))'"
    )

    valor_depois_draw = (
        f"drawtext=text='R$ {valor_depois}':fontcolor={_cor_hex_to_ffmpeg(cor_destaque)}:"
        f"fontsize=80:font='Impact':"
        f"x=(w/2)+50:y=(h/2)-100:borderw=3:bordercolor=black@0.6:"
        f"alpha='if(lt(t,1.8),0,if(lt(t,2.1),(t-1.8)/0.3,1))'"
    )

    economia = round((1 - int(valor_depois) / int(valor_antes)) * 100)
    economia_draw = (
        f"drawtext=text='{economia}%%%% DE ECONOMIA':fontcolor=white:fontsize=64:font='Impact':"
        f"x=(w-text_w)/2:y=(h/2)+80:"
        f"box=1:boxcolor={_cor_hex_to_ffmpeg(cor_destaque)}@0.9:boxborderw=15:"
        f"borderw=2:bordercolor=black@0.5:"
        f"alpha='if(lt(t,2.5),0,if(lt(t,2.8),(t-2.5)/0.3,1))'"
    )

    vf = ",".join([
        antes_draw, valor_antes_draw, seta_draw,
        depois_draw, valor_depois_draw, economia_draw
    ])

    _ffmpeg(
        "-f", "lavfi", "-i",
        f"color=c={_cor_hex_to_ffmpeg(cor_fundo)}:s={W}x{H}:d={duracao_s}:r={FPS}",
        "-vf", vf,
        "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
        str(output_path)
    )

def gerar_clip_infografico(titulo, dado, duracao_s, output_path,
                           icone="☀️", cor_fundo="#1E3A5F",
                           cor_titulo="#F59E0B"):
    """Gera clip de infográfico com ícone + título + dado."""
    titulo_escaped = titulo.replace("'", "’").replace(":", "\\:")
    dado_escaped = dado.replace("'", "’").replace(":", "\\:")

    icone_draw = (
        f"drawtext=text='{icone}':fontsize=150:"
        f"x=(w-text_w)/2:y=(h/2)-250:"
        f"alpha='if(lt(t,0.3),t/0.3,1)'"
    )

    titulo_draw = (
        f"drawtext=text='{titulo_escaped}':"
        f"fontcolor={_cor_hex_to_ffmpeg(cor_titulo)}:fontsize=56:font='Impact':"
        f"x=(w-text_w)/2:y=(h/2)-60:"
        f"borderw=2:bordercolor=black@0.5:"
        f"alpha='if(lt(t,0.5),t/0.5,1)'"
    )

    dado_draw = (
        f"drawtext=text='{dado_escaped}':fontcolor=white:fontsize=44:font='Arial':"
        f"x=(w-text_w)/2:y=(h/2)+40:"
        f"borderw=2:bordercolor=black@0.5:"
        f"alpha='if(lt(t,0.8),0,if(lt(t,1.1),(t-0.8)/0.3,1))'"
    )

    vf = f"{icone_draw},{titulo_draw},{dado_draw}"

    _ffmpeg(
        "-f", "lavfi", "-i",
        f"color=c={_cor_hex_to_ffmpeg(cor_fundo)}:s={W}x{H}:d={duracao_s}:r={FPS}",
        "-vf", vf,
        "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
        str(output_path)
    )

def concatenar_clips(clips_paths, output_path, musica_path=None, volume_musica=0.15):
    """Concatena clips em sequência + adiciona música de fundo."""
    DIR_TMP.mkdir(parents=True, exist_ok=True)
    lista = DIR_TMP / "concat_list.txt"

    with open(lista, "w", encoding="utf-8") as f:
        for p in clips_paths:
            f.write(f"file '{Path(p).resolve()}'\n")

    concat_tmp = DIR_TMP / "concat_raw.mp4"
    _ffmpeg(
        "-f", "concat", "-safe", "0", "-i", str(lista),
        "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
        str(concat_tmp)
    )

    if musica_path and Path(musica_path).exists():
        duracao_video = _ffprobe_duracao(concat_tmp)
        _ffmpeg(
            "-i", str(concat_tmp),
            "-i", str(musica_path),
            "-filter_complex",
            f"[1:a]atrim=0:{duracao_video},afade=t=out:st={duracao_video-2}:d=2,"
            f"volume={volume_musica}[bg];"
            f"[bg]apad[aout]",
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy", "-c:a", "aac", "-shortest",
            str(output_path)
        )
    else:
        silent_dur = _ffprobe_duracao(concat_tmp)
        _ffmpeg(
            "-i", str(concat_tmp),
            "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo:d={silent_dur}",
            "-c:v", "copy", "-c:a", "aac", "-shortest",
            str(output_path)
        )

    if concat_tmp.exists():
        concat_tmp.unlink()
    if lista.exists():
        lista.unlink()

def overlay_texto_sobre_video(video_path, texto, output_path, cor_texto="white",
                               fontsize=72, font="Impact", posicao="center",
                               fade_in=0.5, box=True, box_cor="black", box_opacidade=0.5):
    """Sobrepõe texto animado sobre um vídeo existente (não fundo sólido)."""
    texto_escaped = texto.replace("'", "’").replace(":", "\\:")

    if posicao == "top":
        y_expr = "120"
    elif posicao == "bottom":
        y_expr = f"h-{fontsize+120}"
    else:
        y_expr = "(h-text_h)/2"

    drawtext = (
        f"drawtext=text='{texto_escaped}':"
        f"fontcolor={cor_texto}:fontsize={fontsize}:font='{font}':"
        f"x=(w-text_w)/2:y={y_expr}:"
        f"borderw=3:bordercolor=black@0.6"
    )

    if box:
        drawtext += f":box=1:boxcolor={_cor_hex_to_ffmpeg(box_cor) if box_cor.startswith('#') else box_cor}@{box_opacidade}:boxborderw=15"

    if fade_in > 0:
        drawtext += f":alpha='if(lt(t,{fade_in}),t/{fade_in},1)'"

    _ffmpeg(
        "-i", str(video_path),
        "-vf", drawtext,
        "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        str(output_path)
    )


def overlay_hook_sobre_video(video_path, texto, output_path, cor_primaria="#F59E0B"):
    """Sobrepõe hook grande sobre um vídeo existente."""
    texto_escaped = texto.replace("'", "’").replace(":", "\\:")

    drawtext_main = (
        f"drawtext=text='{texto_escaped}':"
        f"fontcolor={_cor_hex_to_ffmpeg(cor_primaria)}:fontsize=90:font='Impact':"
        f"x=(w-text_w)/2:y=(h-text_h)/2:"
        f"borderw=4:bordercolor=black@0.8:"
        f"box=1:boxcolor=black@0.5:boxborderw=20:"
        f"alpha='if(lt(t,0.3),t/0.3,1)'"
    )

    _ffmpeg(
        "-i", str(video_path),
        "-vf", drawtext_main,
        "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        str(output_path)
    )


def overlay_cta_sobre_video(video_path, texto_cta, output_path,
                             cor_accent="#10B981", watermark="@MSEnergySolar"):
    """Sobrepõe CTA + watermark sobre um vídeo existente."""
    texto_escaped = texto_cta.replace("'", "’").replace(":", "\\:")
    wm_escaped = watermark.replace("'", "’").replace(":", "\\:")

    cta_draw = (
        f"drawtext=text='{texto_escaped}':"
        f"fontcolor=white:fontsize=72:font='Impact':"
        f"x=(w-text_w)/2:y=(h/2)-60:"
        f"borderw=3:bordercolor=black@0.6:"
        f"box=1:boxcolor={_cor_hex_to_ffmpeg(cor_accent)}@0.8:boxborderw=20:"
        f"alpha='if(lt(t,0.5),t/0.5,1)'"
    )

    wm_draw = (
        f"drawtext=text='{wm_escaped}':"
        f"fontcolor=white@0.7:fontsize=36:font='Arial':"
        f"x=(w-text_w)/2:y=h-100"
    )

    _ffmpeg(
        "-i", str(video_path),
        "-vf", f"{cta_draw},{wm_draw}",
        "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        str(output_path)
    )


def adicionar_watermark(video_path, output_path, texto="@MSEnergySolar", opacidade=0.7):
    """Adiciona watermark discreto no canto inferior direito."""
    texto_escaped = texto.replace("'", "’").replace(":", "\\:")

    _ffmpeg(
        "-i", str(video_path),
        "-vf", (
            f"drawtext=text='{texto_escaped}':"
            f"fontcolor=white@{opacidade}:fontsize=28:font='Arial':"
            f"x=w-text_w-30:y=h-50:"
            f"borderw=1:bordercolor=black@0.3"
        ),
        "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        str(output_path)
    )

def limpar_tmp():
    if DIR_TMP.exists():
        shutil.rmtree(DIR_TMP, ignore_errors=True)
