# -*- coding: utf-8 -*-
"""fx_clips.py — MONTAGEM DOS CLIPS (ffmpeg). O coração do render.
build_clip*, intro/outro, memes/transições, concat_with_xfade/transitions, upscale_to_fullhd.

Parte do motor de efeitos — mapa completo na fachada effects_engine.py.
Split mecânico verbatim do _PRE_SPLIT_effects_engine.py.bak (2026-07-04).
"""
import hashlib
import logging
import random
import shutil
import subprocess
import os
import re
from pathlib import Path
from fx_assets import FPS, H, QP, TRANSITION_DURATION, VIRAL_FILTERS, W
from fx_detect import OVERLAYS_DIR, SFX_DIR, is_impact_panel, is_tension_panel, pick_sfx, pick_sfx_by_mood, sfx_duration
from fx_subtitles import _text_block_png
from hp_common import CACHE_DIR

try:  # COMUM (dona 02/11): transições gl-transitions; sem moderngl (Kaggle/PC2) segue o xfade de sempre
    import realce_visual
except Exception:  # noqa: BLE001
    realce_visual = None
# fração das fronteiras fala->fala que viram transição gl
GL_TRANS_CHANCE = float(os.environ.get("ANIME_GL_TRANS_CHANCE", "0.4"))

# 04/11 (dona: "põe pra rodar" os Galaxy S20): o junta-trechos (_render_xfade_segment) vai pro celular livre. Só no PC1
# (PC2/PC3/Kaggle não têm D:\video-fila\celulares.py nem a chave dos celulares); celular fora/ocupado/falhou = roda aqui
# como sempre. Doc: D:\video-fila\CELULARES.md. Desligar: controle.py desligar celulares producao (ou CELULARES=0).
_celulares = None
if os.environ.get("CELULARES") != "0" and os.path.isfile(r"D:\video-fila\celulares.py"):
    try:
        import importlib.util as _ilu
        _spec = _ilu.spec_from_file_location("celulares", r"D:\video-fila\celulares.py")
        _celulares = _ilu.module_from_spec(_spec)
        _spec.loader.exec_module(_celulares)
    except Exception:  # noqa: BLE001
        _celulares = None




def build_glitch_filter(duration=0.08):
    """Gera filtro de glitch RGB split (deslocamento de canais R/G/B).

    Efeito moderno usado em transições de tensão/revelação.
    Duração curtíssima (0.08s = 2-3 frames) pra não enjoar.
    """
    # RGB split: desloca o canal R pra direita e B pra esquerda
    return (
        f"rgbashift=rh=-4:bh=4:rv=2:bv=-2,"
        f"noise=alls=30:allf=t+u,"
        f"eq=contrast=1.3:brightness=-0.05"
    )


def build_letterbox_filter():
    """Adiciona barras cinematográficas (letterbox 2.39:1 dentro de 9:16).

    Usado em momentos dramáticos pra dar clima de cinema.
    """
    # Barras pretas top/bottom (120px cada = ~12.5% do frame)
    bar_h = 120
    return f"drawbox=x=0:y=0:w={W}:h={bar_h}:color=black:t=fill,drawbox=x=0:y={H-bar_h}:w={W}:h={bar_h}:color=black:t=fill"


def build_rewind_filter():
    """Gera um efeito de rebobinar retrô com scanlines, chromatic aberration e ruído."""
    return (
        "rgbashift=rh=-8:bh=8:rv=4:bv=-4,"
        "noise=alls=40:allf=t+u,"
        "eq=contrast=1.35:brightness=-0.08"
    )


def _build_pagetear_filter():
    """Simula o efeito de rasgar página: wipe diagonal rápido com distorção.

    Combina um scale acelerado + deslocamento horizontal que simula
    a página sendo arrancada para o lado com um leve twist.
    """
    # Wipe lateral acelerado com distorção horizontal (simula rasgar)
    return (
        f"scale={W}:{H}:force_original_aspect_ratio=decrease,"
        f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,"
        f"avgblur=sizeX=30:sizeY=1"
    )


def sfx_gap_s(sfx_dur):
    """Dona 31/10: som de efeito e voz não tocam juntos. Segundos de silêncio antes da voz (= quanto o SFX toca).
    ANIME_SFX_GAP=0 = mistura como antes."""
    if os.environ.get("ANIME_SFX_GAP", "0") != "1" or not sfx_dur or sfx_dur <= 0:
        return 0.0
    try:
        teto = min(float(os.environ.get("ANIME_SFX_GAP_MAX", "1.2")), float(os.environ.get("SFX_PLAY_MAX", "1.5")))
    except ValueError:
        teto = 1.2
    return round(max(0.2, min(sfx_dur, teto)), 2)


def apply_effects_to_cmd(cmd, transition_type, sfx_file, duration):
    """
    Modifica em tempo de execução a lista de argumentos 'cmd' do FFmpeg
    para aplicar a transição (fade/flash/glitch) e mixagem de SFX em uma única passada.
    """
    if not transition_type and not sfx_file:
        return cmd

    # 1. Encontrar os índices importantes no cmd original
    try:
        fc_idx = cmd.index("-filter_complex")
        filter_complex = cmd[fc_idx + 1]
    except ValueError:
        return cmd

    # 2. Contar inputs existentes e localizar o input de áudio principal
    input_indices = [i for i, x in enumerate(cmd) if x == "-i"]
    num_inputs = len(input_indices)

    orig_audio_map = None
    try:
        map_indices = [i for i, x in enumerate(cmd) if x == "-map"]
        for idx in map_indices:
            val = cmd[idx + 1]
            if val.endswith(":a"):
                orig_audio_map = val
                break
    except Exception:
        pass

    if not orig_audio_map:
        orig_audio_map = f"{num_inputs - 1}:a"

    orig_video_map = None
    try:
        map_indices = [i for i, x in enumerate(cmd) if x == "-map"]
        for idx in map_indices:
            val = cmd[idx + 1]
            if val.startswith("[") and val.endswith("]"):
                orig_video_map = val
                break
    except Exception:
        pass

    if not orig_video_map:
        orig_video_map = "[v]"

    # 3. Se houver SFX, adicionar o novo input
    if sfx_file:
        sfx_idx = num_inputs
        cmd.insert(fc_idx, "-i")
        cmd.insert(fc_idx + 1, str(sfx_file))
        fc_idx += 2

        sfx_vol = "1.2" if transition_type == "flash" or "impact" in str(sfx_file) else "0.8"
        # Duração de reprodução do SFX no mix:
        #  - teto pela duração do clip (amix usa duration=first → nunca estende vídeo)
        #  - teto absoluto SFX_PLAY_MAX (default 1.5s) pra um SFX longo (ex:
        #    fast_whoosh 9s) não arrastar por cima da fala. A abertura re:zero é
        #    tratada à parte em build_intro_clip e NÃO passa por aqui.
        try:
            play_max = max(0.3, float(os.environ.get("SFX_PLAY_MAX", "1.5")))
        except ValueError:
            play_max = 1.5
        sfx_dur = sfx_duration(sfx_file)
        play = min(sfx_dur, duration, play_max) if sfx_dur > 0 else 1.0
        play = max(0.20, play)
        if sfx_gap_s(sfx_dur):  # 31/10: a voz espera o SFX acabar (anime_segments._voz_depois_do_sfx)
            play = min(play, sfx_gap_s(sfx_dur))
        # loudnorm nivela cada SFX a um volume parelho e audível — resolve os
        # arquivos quase mudos (new_transition_1 -77dB, swoosh_light -68dB) que
        # sumiam no mix. Aplicado ANTES do volume/trim. SFX_LOUDNORM=0 desliga.
        norm = ("loudnorm=I=-16:TP=-1.5,"
                if os.environ.get("SFX_LOUDNORM", "1") != "0" else "")
        # 14/11 (achado A18 do agente online, medido no D: com este filtro): o amix sem normalize=0 DIVIDE cada entrada
        # pelo nº de entradas — a VOZ caía 6 dB (-36 -> -42 dB) enquanto o SFX tocava e voltava subindo em 0,3 s: a 1ª
        # palavra depois de cada corte com SFX saía engolida, em todo Short e longo. Com normalize=0 a voz fica estável
        # (-35,8 dB o clipe inteiro). Como aí voz e SFX passam a SOMAR, o volume do SFX vai à metade (1.2 -> 0.6,
        # 0.8 -> 0.4): medido, o SFX fica igual ao de antes (-30,4 contra -30,8 dB). alimiter = sem estouro na soma.
        # SFX_AMIX_ANTIGO=1 volta ao mix de antes.
        if os.environ.get("SFX_AMIX_ANTIGO") == "1":
            fim_mix = ""
        else:
            sfx_vol = f"{float(sfx_vol) / 2:g}"
            fim_mix = ":normalize=0,alimiter=limit=0.95"
        audio_mix_filter = (
            f";[{sfx_idx}:a]{norm}volume={sfx_vol},atrim=0:{play:.2f},"
            f"afade=t=out:st={max(0.0, play - 0.12):.2f}:d=0.12,apad=whole_dur={play:.2f}[sfx_temp];"
            f"[{orig_audio_map}][sfx_temp]amix=inputs=2:duration=first:dropout_transition=0.3{fim_mix}[aout]"
        )
        filter_complex += audio_mix_filter
        new_audio_map = "[aout]"
    else:
        new_audio_map = orig_audio_map

    # 4. Adicionar a transição de vídeo
    v_in = orig_video_map
    v_out = orig_video_map
    video_filters = []

    # Transições simples (fade auto-janelado — só afeta os primeiros frames)
    SIMPLE_TRANS = {
        "flash":     "fade=t=in:st=0:d=0.25:color=white",
        "flashred":  "fade=t=in:st=0:d=0.28:color=0xCC1111",
        "flashgold": "fade=t=in:st=0:d=0.30:color=0xE8B500",
        "flashblue": "fade=t=in:st=0:d=0.30:color=0x2244CC",
        "fade":      "fade=t=in:st=0:d=0.40:color=black",
    }
    # Transições "split": efeito só nos primeiros segundos, depois corte limpo.
    # (duração, filtro aplicado no trecho inicial). Dimensões PARES p/ libx264.
    _zw = (int(W * 1.25) // 2) * 2
    _zh = (int(H * 1.25) // 2) * 2
    _zw2 = (int(W * 1.45) // 2) * 2
    _zh2 = (int(H * 1.45) // 2) * 2
    SPLIT_TRANS = {
        "glitch":  ("0.10", build_glitch_filter()),
        "blurin":  ("0.18", "gblur=sigma=26"),
        "pixelin": ("0.16", f"scale={W//12}:{H//12}:flags=neighbor,scale={W}:{H}:flags=neighbor"),
        "zoomin":  ("0.18", f"scale={_zw}:{_zh},crop={W}:{H}:({_zw}-{W})/2:({_zh}-{H})/2"),
        "whip":    ("0.12", "avgblur=sizeX=60:sizeY=1"),
        "pagetear": ("0.15", _build_pagetear_filter()),
        "rewind":   ("0.25", build_rewind_filter()),
        "punch":    ("0.14", f"scale={_zw2}:{_zh2},crop={W}:{H}:({_zw2}-{W})/2:({_zh2}-{H})/2"),
        "snap":     ("0.16", f"scale={_zw2}:{_zh2},crop={W}:{H}:({_zw2}-{W})/2:({_zh2}-{H})/2,eq=contrast=1.15:brightness=0.04"),
        "speedblur": ("0.14", "avgblur=sizeX=1:sizeY=40"),
        "zoomout":   ("0.20", f"scale={_zw2}:{_zh2},crop={W}:{H}:({_zw2}-{W})/2:({_zh2}-{H})/2,gblur=sigma=8"),
        "flashpink": ("0.16", "fade=t=in:st=0:d=0.16:color=0xFF66AA"),
    }

    if transition_type in SIMPLE_TRANS:
        v_out = "[vfinal_trans]"
        video_filters.append(SIMPLE_TRANS[transition_type])
    elif transition_type in SPLIT_TRANS:
        v_out = "[vfinal_trans]"
        d, eff = SPLIT_TRANS[transition_type]
        filter_complex += (
            f";{v_in}split[tA][tB];"
            f"[tA]trim=0:{d},setpts=PTS-STARTPTS,{eff}[tAo];"
            f"[tB]trim={d},setpts=PTS-STARTPTS[tBo];"
            f"[tAo][tBo]concat=n=2:v=1:a=0{v_out}"
        )
        v_in = ""

    if video_filters and v_in:
        filter_complex += f";{v_in}{','.join(video_filters)}{v_out}"

    # Atualizar o filter_complex no cmd
    cmd[fc_idx + 1] = filter_complex

    # 5. Atualizar os mapeamentos de áudio/vídeo no cmd
    map_indices = [i for i, x in enumerate(cmd) if x == "-map"]
    for idx in map_indices:
        val = cmd[idx + 1]
        if val == orig_video_map:
            cmd[idx + 1] = v_out
        elif val == orig_audio_map:
            cmd[idx + 1] = new_audio_map

    return cmd


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
        black_hold = max(0.0, float(os.environ.get("INTRO_BLACK_HOLD", "0.8")))
    except ValueError:
        black_hold = 0.8
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


def _append_overlay(filter_complex, overlay_video, input_idx=2, opacity=0.3):
    """Anexa overlay atmosférico ao filter_complex usando overlay com opacidade.
    Usa colorkey pra remover fundo preto do overlay (mais seguro que blend=screen).
    """
    if not overlay_video or not Path(overlay_video).exists():
        return filter_complex, []
    if not filter_complex.endswith("[v]"):
        return filter_complex, []
    base = filter_complex[:-3] + "[vbase]"
    base += (
        f";[{input_idx}:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
        f"crop={W}:{H},setsar=1,colorkey=black:0.3:0.2,"
        f"format=yuva420p,colorchannelmixer=aa={opacity}[ovl];"
        f"[vbase][ovl]overlay=0:0:format=auto,format=yuv420p[v]"
    )
    return base, ["-stream_loop", "-1", "-i", str(overlay_video)]


# ══════════════════════════════════════════════════════════════════════════
# SEÇÃO 5: FUNÇÕES DE MONTAGEM (ffmpeg commands)
# ══════════════════════════════════════════════════════════════════════════

def build_clip(img_path, audio_path, out_path, panel_idx, effects_mgr, duration=None,
               transition_type=None, sfx_file=None, overlay_video=None, mood=None,
               narr_text=None):
    """Cria clip de um painel com efeitos visuais completos.

    Aplica: background blur + movimento (pan/zoom) + filtro de cor + vinheta.
    O background blur usa uma versão borrada e escurecida da própria imagem
    como fundo, em vez de bordas pretas — muito mais profissional.
    """
    from PIL import Image
    img = Image.open(img_path)
    pw, ph = img.size

    if duration is None:
        # Obter duração do áudio
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                 "-of", "csv=p=0", str(audio_path)],
                capture_output=True, text=True, timeout=10,
            )
            duration = float(result.stdout.strip())
        except Exception:
            duration = 4.0
    duration = max(duration, 1.5)
    frames = int(duration * FPS)

    try:
        m = hashlib.md5()
        with open(img_path, "rb") as f: m.update(f.read())
        if audio_path and Path(audio_path).exists():
            with open(audio_path, "rb") as f: m.update(f.read())
        m.update(str(duration).encode('utf-8'))
        # 23/10: usava color_filter ANTES de ele existir -> NameError engolido pelo except -> cache nunca valia aqui
        m.update(str(mood or "").encode('utf-8'))
        m.update("V1_LEGACY".encode('utf-8'))
        
        clip_hash = m.hexdigest()
        cached_clip = CACHE_DIR / f"{clip_hash}.mp4"
        
        if cached_clip.exists() and cached_clip.stat().st_size > 1000:
            shutil.copy2(str(cached_clip), str(out_path))
            return duration, f"{frames} frames (CACHED)"
    except Exception as e:
        clip_hash = None


    # Escolher movimento baseado nas dimensões
    # T7: se CONTEXT_MOTION=1 e há texto, o ritmo é guiado pela emoção da narração.
    _prefer_speed = None
    if narr_text and os.environ.get("CONTEXT_MOTION", "0") == "1":
        try:
            import contextual_motion as _cmot
            _pref = _cmot.motion_pref(narr_text)
            if _pref:
                _prefer_speed = _pref.get("speed")
        except Exception:
            _prefer_speed = None
    movement = effects_mgr.pick_movement(ph, pw, prefer_speed=_prefer_speed)
    movement_filter = movement["filter"].format(frames=frames) if isinstance(movement, dict) else movement.format(frames=frames)

    # Escolher cor — se mood fornecido, usar filtro viral por emoção
    if mood and mood in VIRAL_FILTERS:
        color_filter = VIRAL_FILTERS[mood]
    else:
        color = effects_mgr.pick_color()
        color_filter = color["filter"] if isinstance(color, dict) else color

    # T5: correção adaptativa (CONTENT_ADAPT=1). Mede a imagem e ANEXA um eq de correção
    # (clareia painel escuro, sobe contraste lavado) ao grading já escolhido — não substitui.
    if os.environ.get("CONTENT_ADAPT", "0") == "1":
        try:
            import content_analyzer as _ca
            _eq, _ = _ca.adaptive_eq(img_path)
            if _eq:
                color_filter = f"{color_filter},{_eq}"
        except Exception:
            pass

    # Vinheta (opcional)
    vignette = effects_mgr.pick_vignette()
    vignette_filter = vignette if isinstance(vignette, str) else (vignette["filter"] if isinstance(vignette, dict) else None)

    # Ratio da imagem vs canvas
    img_ratio = ph / pw
    canvas_ratio = H / W  # 1920/1080 = 1.78

    if img_ratio > 2.0:
        # Painel ALTO — pan vertical na imagem inteira
        prescale = f"scale=1080:-1"
        filters = [prescale, movement_filter, color_filter]
        if vignette_filter:
            filters.append(vignette_filter)
        filters.append(f"fade=t=out:st={duration-0.3:.2f}:d=0.3")
        filters.append("format=yuv420p")
        filter_chain = ",".join(filters)
        filter_complex = f"[0:v]{filter_chain}[v]"
    elif img_ratio > 1.2:
        # Painel médio/alto — zoompan direto
        filters = [movement_filter, color_filter]
        if vignette_filter:
            filters.append(vignette_filter)
        filters.append(f"fade=t=out:st={duration-0.3:.2f}:d=0.3")
        filters.append("format=yuv420p")
        filter_chain = ",".join(filters)
        filter_complex = f"[0:v]{filter_chain}[v]"
    else:
        # Painel LARGO (ratio < 1.2) — background blur profissional
        # Em vez de bordas pretas, usa a própria imagem borrada como fundo (n8n V5.1)
        filter_complex = (
            f"[0:v]split=2[bg][fg];"
            f"[bg]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
            f"boxblur=18:8,eq=brightness=-0.3[bg_blur];"
            f"[fg]scale={W}:{H}:force_original_aspect_ratio=decrease[fg_scaled];"
            f"[bg_blur][fg_scaled]overlay=(W-w)/2:(H-h)/2,"
            f"{color_filter}"
        )
        if vignette_filter:
            filter_complex += f",{vignette_filter}"
        filter_complex += f",fade=t=out:st={duration-0.3:.2f}:d=0.3,format=yuv420p[v]"

    # Overlay atmosférico (chuva/neve/faíscas/pétalas) entra como input 2
    filter_complex, overlay_input = _append_overlay(filter_complex, overlay_video)

    # Clip base (movimento + cor + vinheta + overlay). Transição/SFX embutidos na
    # MESMA chamada (single-pass) via apply_effects_to_cmd — sem re-encode extra.
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-t", f"{duration:.2f}", "-i", str(img_path),
        "-i", str(audio_path),
        *overlay_input,
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "1:a",
        "-c:v", "libx264", "-preset", QP["preset"], "-crf", str(QP["crf"]), "-g", "30",
        "-c:a", "aac", "-b:a", QP["audio_bitrate"], "-ar", "44100", "-ac", "2",
        "-pix_fmt", "yuv420p", "-t", f"{duration:.2f}",
        str(out_path),
    ]

    try:
        cmd = apply_effects_to_cmd(cmd, transition_type, sfx_file, duration)
        subprocess.run(cmd, check=True, capture_output=True, timeout=180)
        if clip_hash and Path(out_path).exists():
            try: shutil.copy2(str(out_path), str(cached_clip))
            except Exception: pass
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, Exception) as e:
        # Fallback: escala simples com padding escuro
        minimal = f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=0x0a0f1c,{color_filter},format=yuv420p"
        cmd_simple = [
            "ffmpeg", "-y",
            "-loop", "1", "-t", f"{duration:.2f}", "-i", str(img_path),
            "-i", str(audio_path),
            "-filter_complex", f"[0:v]{minimal}[v]",
            "-map", "[v]", "-map", "1:a",
            "-c:v", "libx264", "-preset", QP["preset"], "-crf", str(QP["crf"]), "-g", "30",
            "-c:a", "aac", "-b:a", QP["audio_bitrate"], "-ar", "44100", "-ac", "2",
            "-pix_fmt", "yuv420p", "-t", f"{duration:.2f}",
            str(out_path),
        ]
        try:
            cmd_simple = apply_effects_to_cmd(cmd_simple, transition_type, sfx_file, duration)
            subprocess.run(cmd_simple, check=True, capture_output=True, timeout=60)
            return True
        except Exception:
            return False


def build_clip_with_shake(img_path, audio_path, out_path, panel_idx, effects_mgr,
                          duration=None, shake_intensity=10, shake_freq=12,
                          transition_type=None, sfx_file=None, overlay_video=None, mood=None):
    """Cria clip com camera shake — pra painéis de impacto/ação.

    O shake é aplicado via crop com offset sinusoidal nos eixos X e Y.
    O efeito diminui ao longo do clip (decay), simulando tremor de impacto.

    Args:
        shake_intensity: amplitude do tremor em pixels (default 10)
        shake_freq: frequência das oscilações (default 12 Hz)
    """
    from PIL import Image
    img = Image.open(img_path)
    pw, ph = img.size

    if duration is None:
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                 "-of", "csv=p=0", str(audio_path)],
                capture_output=True, text=True, timeout=10,
            )
            duration = float(result.stdout.strip())
        except Exception:
            duration = 4.0
    duration = max(duration, 1.5)
    frames = int(duration * FPS)

    try:
        m = hashlib.md5()
        with open(img_path, "rb") as f: m.update(f.read())
        if audio_path and Path(audio_path).exists():
            with open(audio_path, "rb") as f: m.update(f.read())
        m.update(str(duration).encode('utf-8'))
        m.update(str(mood or "").encode('utf-8'))  # 23/10: era color_filter antes de existir (cache nunca valia)
        m.update("V1_SHAKE".encode('utf-8'))
        
        clip_hash = m.hexdigest()
        cached_clip = CACHE_DIR / f"{clip_hash}.mp4"
        
        if cached_clip.exists() and cached_clip.stat().st_size > 1000:
            shutil.copy2(str(cached_clip), str(out_path))
            return duration, f"{frames} frames (CACHED)"
    except Exception as e:
        clip_hash = None


    # Escolher movimento, cor, vinheta (como build_clip normal)
    movement = effects_mgr.pick_movement(ph, pw)
    movement_filter = movement["filter"].format(frames=frames) if isinstance(movement, dict) else movement.format(frames=frames)
    if mood and mood in VIRAL_FILTERS:
        color_filter = VIRAL_FILTERS[mood]
    else:
        color = effects_mgr.pick_color()
        color_filter = color["filter"] if isinstance(color, dict) else color
    vignette = effects_mgr.pick_vignette()
    vignette_filter = vignette if isinstance(vignette, str) else (
        vignette["filter"] if isinstance(vignette, dict) else None)

    # Camera shake: crop com margem extra, offset sinusoidal com decay
    # Precisamos gerar um frame maior e depois croppar com tremor
    margin = shake_intensity + 2  # margem extra pra não cortar fora
    shake_w = W + margin * 2
    shake_h = H + margin * 2

    # Decay: o shake diminui ao longo do tempo (forte no início, sumindo)
    # decay = max(0, 1 - on/(frames*0.6))  → shake dura 60% do clip
    shake_x = f"{margin}+{shake_intensity}*sin(t*{shake_freq})*max(0,1-t/({duration*0.6:.2f}))"
    shake_y = f"{margin}+{shake_intensity}*cos(t*{shake_freq}*1.3)*max(0,1-t/({duration*0.6:.2f}))"
    shake_crop = f"crop={W}:{H}:{shake_x}:{shake_y}"

    img_ratio = ph / pw

    if img_ratio > 2.0:
        prescale = "scale=1080:-1"
        # Ajustar zoompan pra gerar frame maior (shake_w x shake_h)
        shake_movement = movement_filter.replace(f"s={W}x{H}", f"s={shake_w}x{shake_h}")
        filters = [prescale, shake_movement, shake_crop, color_filter]
    elif img_ratio > 1.2:
        shake_movement = movement_filter.replace(f"s={W}x{H}", f"s={shake_w}x{shake_h}")
        filters = [shake_movement, shake_crop, color_filter]
    else:
        # Painel largo — scale+pad maior, depois crop com shake
        fg_filter = (
            f"scale={shake_w}:{shake_h}:force_original_aspect_ratio=decrease,"
            f"pad={shake_w}:{shake_h}:(ow-iw)/2:(oh-ih)/2:color=0x0a0f1c"
        )
        filters = [fg_filter, shake_crop, color_filter]

    if vignette_filter:
        filters.append(vignette_filter)
    filters.append("format=yuv420p")
    filter_chain = ",".join(filters)
    filter_complex = f"[0:v]{filter_chain}[v]"
    filter_complex, overlay_input = _append_overlay(filter_complex, overlay_video)

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-t", f"{duration:.2f}", "-i", str(img_path),
        "-i", str(audio_path),
        *overlay_input,
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "1:a",
        "-c:v", "libx264", "-preset", QP["preset"], "-crf", str(QP["crf"]), "-g", "30",
        "-c:a", "aac", "-b:a", QP["audio_bitrate"], "-ar", "44100", "-ac", "2",
        "-pix_fmt", "yuv420p", "-t", f"{duration:.2f}",
        str(out_path),
    ]

    try:
        cmd = apply_effects_to_cmd(cmd, transition_type, sfx_file, duration)
        subprocess.run(cmd, check=True, capture_output=True, timeout=180)
        if clip_hash and Path(out_path).exists():
            try: shutil.copy2(str(out_path), str(cached_clip))
            except Exception: pass
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, Exception):
        # Fallback: build_clip sem shake (mantém transição/SFX + overlay)
        return build_clip(img_path, audio_path, out_path, panel_idx, effects_mgr,
                          duration, transition_type, sfx_file, overlay_video)


def build_flash_clip(img_path, out_path, clip_idx, effects_mgr, duration=0.8,
                     transition_type=None, sfx_file=None):
    """Cria clip rápido (sem áudio) com flash branco no final.

    Pra painéis sem narração — passam rápido e dão ritmo ao vídeo.
    """
    from PIL import Image
    img = Image.open(img_path)
    pw, ph = img.size
    img_ratio = ph / pw
    frames = int(duration * FPS)

    # Zoom rápido (mais agressivo que o normal pra dar sensação de velocidade)
    zoom_filter = f"zoompan=z='min(zoom+0.002,1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={FPS}"

    # Flash branco no final (últimos 5 frames = fade to white)
    flash = f"fade=t=out:st={max(0, duration-0.15):.2f}:d=0.15:color=white"

    if img_ratio > 2.0:
        prescale = "scale=1080:-1"
        filter_chain = f"{prescale},{zoom_filter},{flash},format=yuv420p"
    elif img_ratio > 1.2:
        filter_chain = f"{zoom_filter},{flash},format=yuv420p"
    else:
        filter_chain = (
            f"scale={W}:{H}:force_original_aspect_ratio=decrease,"
            f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=0x0a0f1c,"
            f"{flash},format=yuv420p"
        )

    # Gerar áudio: usar micro-SFX se disponível, senão tom mínimo (não silêncio puro)
    # Silêncio puro (anullsrc) corrompe stream de áudio no concat
    sfx_for_flash = pick_sfx("transition") if SFX_DIR.exists() else None
    if sfx_for_flash and Path(sfx_for_flash).exists():
        audio_input = ["-i", str(sfx_for_flash)]
        audio_filter = f"[1:a]volume=0.3,atrim=0:{duration:.2f},apad=whole_dur={duration:.2f}[a]"
        audio_map = "[a]"
    else:
        # Tom inaudível (1Hz, volume quase zero) — mantém stream válido sem silêncio
        audio_input = ["-f", "lavfi", "-t", f"{duration:.2f}", "-i", f"sine=frequency=1:sample_rate=44100:duration={duration:.2f}"]
        audio_filter = "[1:a]volume=0.001[a]"
        audio_map = "[a]"

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-t", f"{duration:.2f}", "-i", str(img_path),
        *audio_input,
        "-filter_complex", f"[0:v]{filter_chain}[v];{audio_filter}",
        "-map", "[v]", "-map", audio_map,
        "-c:v", "libx264", "-preset", QP["preset"], "-crf", str(QP["crf"]), "-g", "30",
        "-c:a", "aac", "-b:a", QP["audio_bitrate"], "-ar", "44100", "-ac", "2",
        "-pix_fmt", "yuv420p", "-t", f"{duration:.2f}",
        str(out_path),
    ]
    try:
        cmd = apply_effects_to_cmd(cmd, transition_type, sfx_file, duration)
        subprocess.run(cmd, check=True, capture_output=True, timeout=30)
        return True
    except Exception:
        return False


# --- Meme System (inserção inteligente de memes entre clips) ---
MEMES_VIDEO_DIR = Path(__file__).parent.parent / "workspace" / "assets" / "memes_img" / "memes"
_meme_counter = 0          # clips desde o último meme
_memes_inseridos = 0       # total de memes no vídeo (pra teto global)
# Cadência DINÂMICA (não fixa): o meme só pode entrar depois de MEME_GAP_MIN
# clips, é forçado depois de MEME_GAP_MAX, e entre os dois a chance depende do
# mood (cena cômica/leve puxa mais meme; neutra puxa menos). Assim fica "mais
# quando precisa, menos quando não" — com piso e teto pra não encher nem sumir.
MEME_GAP_MIN = 4           # nunca 2 memes a menos de 4 clips de distância (teto de proximidade)
MEME_GAP_MAX = 12          # se passou disso sem meme, força um (piso)
MEME_MOOD_CHANCE = {       # chance por clip, na janela [min,max], conforme o clima
    "funny_lighthearted": 0.55,
    "romantic_sexy": 0.22,
    "calm_chill": 0.18,
    "neutral_chill": 0.25,
    "action": 0.30,
}


def should_insert_meme(clip_idx, mood):
    """Cadência DINÂMICA de meme. NUNCA em cena triste/tensa.
    - antes de MEME_GAP_MIN clips desde o último: nunca (evita encher)
    - depois de MEME_GAP_MAX sem meme: força (evita sumir)
    - no meio: chance proporcional ao mood (mais em comédia, menos em neutro)"""
    global _meme_counter
    if mood in ("tense_dramatic", "sad_emotional"):
        return False
    _meme_counter += 1
    if _meme_counter < MEME_GAP_MIN:
        return False
    if _meme_counter >= MEME_GAP_MAX:
        _meme_counter = 0
        return True
    chance = MEME_MOOD_CHANCE.get(mood, 0.25)
    if random.random() < chance:
        _meme_counter = 0
        return True
    return False


def build_meme_clip(out_path, mood="neutral_chill", duration=None):
    """Constrói clip de meme. Se o meme tem áudio nativo, usa direto. Se é
    imagem/sem áudio, adiciona um SFX que COMBINA com o clima da cena (via
    pick_sfx_by_mood) em vez de um whoosh genérico — evita som que não tem
    nada a ver com o que está acontecendo.

    duration DINÂMICA por mood (None = auto): comédia segura mais tempo na tela
    (3.2s), cenas neutras/leves passam rápido (2.2s)."""
    global _memes_inseridos
    if duration is None:
        duration = {"funny_lighthearted": 3.2, "action": 2.6,
                    "romantic_sexy": 2.4}.get(mood, 2.2)
    if not MEMES_VIDEO_DIR.exists():
        return False
    memes = list(MEMES_VIDEO_DIR.glob("*.mp4"))
    if not memes:
        return False

    meme_video = random.choice(memes)
    _memes_inseridos += 1

    # Detectar se meme tem áudio
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "quiet", "-select_streams", "a", "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(meme_video)],
            capture_output=True, text=True, timeout=5)
        has_audio = "audio" in r.stdout
    except Exception:
        has_audio = False

    if has_audio:
        # Meme com áudio nativo — usar direto. Áudio FORÇADO a `duration` (apad+atrim):
        # sem isso, áudio nativo mais curto + `-shortest` encurtava o CLIP e o desalinho
        # ACUMULAVA no concat → fala saía no quadro errado (drift progressivo). Sem -shortest.
        cmd = [
            "ffmpeg", "-y", "-i", str(meme_video),
            "-t", f"{duration:.2f}",
            "-vf", f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:black",
            "-af", f"apad,atrim=0:{duration:.3f},asetpts=PTS-STARTPTS",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
            "-c:a", "aac", "-b:a", QP["audio_bitrate"], "-ar", "44100", "-ac", "2", "-pix_fmt", "yuv420p",
            str(out_path),
        ]
    else:
        # Meme sem áudio (imagem) — SFX que COMBINA com o mood da cena
        sfx = pick_sfx_by_mood(mood) or pick_sfx("transition")
        if sfx and Path(sfx).exists():
            cmd = [
                "ffmpeg", "-y",
                "-i", str(meme_video),
                "-i", str(sfx),
                "-t", f"{duration:.2f}",
                "-filter_complex",
                f"[0:v]scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:black,"
                f"tpad=stop_mode=clone:stop_duration={duration},trim=0:{duration:.3f},setpts=PTS-STARTPTS[v];"
                f"[1:a]volume=0.8,apad,atrim=0:{duration:.3f},asetpts=PTS-STARTPTS[a]",
                "-map", "[v]", "-map", "[a]",
                "-t", f"{duration:.2f}",
                "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
                "-c:a", "aac", "-b:a", QP["audio_bitrate"], "-ar", "44100", "-ac", "2", "-pix_fmt", "yuv420p",
                str(out_path),
            ]
        else:
            # Sem SFX disponível — gerar silêncio. Vídeo estendido a `duration` (tpad clone) +
            # silêncio do mesmo tamanho; sem -shortest (que encurtava e acumulava drift).
            cmd = [
                "ffmpeg", "-y", "-i", str(meme_video),
                "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=mono:d={duration}",
                "-vf", f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:black,"
                       f"tpad=stop_mode=clone:stop_duration={duration},trim=0:{duration:.3f},setpts=PTS-STARTPTS",
                "-map", "0:v", "-map", "1:a",
                "-t", f"{duration:.2f}",
                "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
                "-c:a", "aac", "-b:a", QP["audio_bitrate"], "-ar", "44100", "-ac", "2", "-pix_fmt", "yuv420p",
                str(out_path),
            ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=30)
        return Path(out_path).exists() and Path(out_path).stat().st_size > 1000
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, Exception):
        return False


# ── Vídeos de transição entre cenas (os 19 mp4 de overlays/transitions) ───────
TRANSITIONS_VIDEO_DIR = OVERLAYS_DIR / "transitions"
_transition_counter = 0
TRANSITION_VIDEO_FREQUENCY = 5  # insere um vídeo de transição a cada N clips


def should_insert_transition(clip_idx):
    """Decide se entra um vídeo de transição (a cada TRANSITION_VIDEO_FREQUENCY clips).
    Diferente do meme (que é cômico e só em cena leve), a transição é neutra e
    serve só de "respiro" visual entre cenas — pode entrar em qualquer mood."""
    global _transition_counter
    _transition_counter += 1
    if _transition_counter >= TRANSITION_VIDEO_FREQUENCY:
        _transition_counter = 0
        return True
    return False


def build_transition_clip(out_path, duration=1.0):
    """Monta um clip curto a partir de um dos 19 vídeos de transição.

    Re-encoda pros MESMOS parâmetros dos clips normais (resolução, fps, codec,
    áudio aac) — é isso que permite entrar no concat simples `-c copy` SEM
    quebrar a sincronia de áudio (o erro histórico foi mexer no xfade; aqui não
    tocamos nele, a transição é só mais um clip curtinho na fila).
    O áudio do vídeo de transição é descartado e trocado por silêncio (são
    efeitos visuais; o som fica por conta dos SFX/trilha do pipeline)."""
    if not TRANSITIONS_VIDEO_DIR.exists():
        return False
    vids = list(TRANSITIONS_VIDEO_DIR.glob("*.mp4"))
    if not vids:
        return False
    tv = random.choice(vids)
    cmd = [
        "ffmpeg", "-y", "-i", str(tv),
        "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=mono:d={duration}",
        "-vf", f"scale={W}:{H}:force_original_aspect_ratio=decrease,"
               f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:black,fps={FPS},setsar=1,"
               f"tpad=stop_mode=clone:stop_duration={duration},trim=0:{duration:.3f},setpts=PTS-STARTPTS",
        "-map", "0:v", "-map", "1:a",
        "-t", f"{duration:.2f}",
        "-c:v", "libx264", "-preset", QP["preset"], "-crf", str(QP["crf"]),
        "-c:a", "aac", "-b:a", QP["audio_bitrate"], "-ar", "44100", "-ac", "2", "-pix_fmt", "yuv420p",
        str(out_path),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=30)
        return Path(out_path).exists() and Path(out_path).stat().st_size > 1000
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, Exception):
        return False


# ── Transições xfade REAIS entre clips (1 passada, áudio em sync) ────────────
_XFADE_SUPPORTED = None


def _xfade_supported():
    """Descobre quais transições xfade existem NESTE build do ffmpeg (cacheado)."""
    global _XFADE_SUPPORTED
    if _XFADE_SUPPORTED is not None:
        return _XFADE_SUPPORTED
    supported = set()
    try:
        r = subprocess.run(["ffmpeg", "-hide_banner", "-h", "filter=xfade"],
                           capture_output=True, text=True, timeout=15)
        txt = (r.stdout or "") + (r.stderr or "")
        for line in txt.splitlines():
            m = re.match(r"\s+([a-z]+)\s+\d+\s+\.", line)  # "  fade  0  ..FV..."
            if m:
                supported.add(m.group(1))
    except Exception:
        pass
    if not supported:  # fallback mínimo garantido (presente desde ffmpeg 4.3)
        supported = {"fade", "fadeblack", "fadewhite", "dissolve", "wipeleft",
                     "wiperight", "wipeup", "wipedown", "slideleft", "slideright",
                     "slideup", "slidedown", "smoothleft", "smoothright", "smoothup",
                     "smoothdown", "circleopen", "circleclose", "diagtl", "diagtr",
                     "diagbl", "diagbr", "pixelize", "radial", "distance",
                     "hlslice", "hrslice", "vuslice", "vdslice"}
    _XFADE_SUPPORTED = supported
    return supported


def _probe_dur(path):
    try:
        r = subprocess.run(["ffprobe", "-v", "quiet", "-show_entries",
                            "format=duration", "-of", "csv=p=0", str(path)],
                           capture_output=True, text=True, timeout=15)
        return float(r.stdout.strip())
    except Exception:
        return 3.0


def _pick_xfade(desc, supported, last):
    """Escolhe transição xfade + duração pelo mood do painel (varia, não repete)."""
    impact = is_impact_panel(desc) if desc else False
    tension = is_tension_panel(desc) if desc else False
    if impact:                       # corte de ação: rápido, direcional, com "vento"
        # 01/11 dona (uJMzSnTSXIU): whip pan (hblur = chicote com borrão), zoom de soco e flash branco
        pool = ["coverleft", "coverright", "coverup", "hrwind", "vuwind",
                "hrslice", "vuslice", "zoomin", "squeezev", "slideleft",
                "slideright", "wipeleft", "diagtr", "hblur", "hblur", "zoomin", "fadewhite"]
        d = 0.22
    elif tension:                    # tensão: desfaz/rasga em tiras / revela
        pool = ["dissolve", "hlslice", "vdslice", "hlwind", "vdwind", "pixelize",
                "radial", "distance", "fadeblack", "revealdown", "diagbl", "hblur", "fadewhite"]
        d = 0.35
    else:                            # normal/calmo: suave + reveals elegantes
        pool = ["fade", "dissolve", "smoothleft", "smoothright", "smoothup",
                "smoothdown", "circleopen", "circleclose", "revealleft",
                "revealright", "revealup", "coverdown", "wipeleft", "wiperight",
                "slideup", "slidedown", "diagtl", "diagbr", "horzopen", "vertopen",
                "pixelize"]
        d = 0.42
    pool = [t for t in pool if t in supported]
    if not pool:
        pool = [t for t in ("fade", "dissolve") if t in supported] or ["fade"]
    choices = [t for t in pool if t != last] or pool
    return random.choice(choices), d


def _choose_xfade_batches(n, is_speech, max_batch):
    """Divide [0,n) em lotes de no máximo max_batch clips. Prefere cortar os
    lotes numa fronteira de CORTE SECO (k onde NÃO há xfade: respiro/meme),
    porque ali não se perde transição ao emendar os lotes via concat. Se não
    houver corte seco dentro da janela, corta no limite mesmo."""
    batches = []
    s = 0
    while s < n:
        hard_cap = min(s + max_batch, n)
        if hard_cap >= n:
            batches.append((s, n)); break
        # procura, de trás pra frente dentro da janela, uma fronteira de corte
        # seco (k tal que a transição k-1→k seria seca). soft = fala→fala.
        cut = hard_cap
        for k in range(hard_cap, s + 3, -1):
            soft = is_speech[k] and is_speech[k - 1]
            if not soft:
                cut = k; break
        batches.append((s, cut))
        s = cut
    return batches


# Posições reais (start, total) do ÚLTIMO segmento renderizado — usadas pra
# sincronizar legenda com o vídeo (o xfade comprime o tempo de forma NÃO-linear,
# só nas fronteiras fala→fala; um fator linear erra e a legenda "desanda" ~30s).
_LAST_SEG_STARTS = []
_LAST_SEG_TOTAL = 0.0
# Posições absolutas (s) de início de cada clip no vídeo final concatenado.
# A legenda usa isto pra casar exatamente com o vídeo (corrige o "desanda ~30s").
_CLIP_ABS_STARTS = []


def _render_xfade_segment(clips, durs, is_speech, gaps, descriptions,
                          supported, out_path):
    """Renderiza UM segmento (lista de clips) numa única passada de
    filter_complex: xfade+acrossfade nas fronteiras fala→fala, corte seco nas
    demais. Aplica o gap (respiro) no fim de cada clip de fala. Retorna True/False.
    Mantém o segmento pequeno o bastante pra não estourar memória.
    Efeito colateral: grava em _LAST_SEG_STARTS/_LAST_SEG_TOTAL as posições reais
    de início de cada clip no segmento e a duração total dele."""
    global _LAST_SEG_STARTS, _LAST_SEG_TOTAL
    m = len(clips)
    if m == 0:
        _LAST_SEG_STARTS, _LAST_SEG_TOTAL = [], 0.0
        return False
    if m == 1:
        gi0 = (gaps[0] if gaps else 0.0) or 0.0
        _LAST_SEG_STARTS = [0.0]
        _LAST_SEG_TOTAL = durs[0] + gi0
        # 1 clip só: aplica o gap (se houver) e re-encoda, ou copia.
        gi = gaps[0] if gaps else 0.0
        if gi and gi > 0:
            tgt1 = durs[0] + gi
            fc = (f"[0:v]format=yuv420p,fps={FPS},scale={W}:{H},setsar=1,"
                  f"tpad=stop_mode=clone:stop_duration={gi:.3f},settb=AVTB,setpts=PTS-STARTPTS[v];"
                  f"[0:a]aresample=44100,aformat=sample_fmts=fltp:channel_layouts=stereo,"
                  f"apad=whole_dur={tgt1:.4f},atrim=0:{tgt1:.4f},asetpts=PTS-STARTPTS[a]")
            cmd = ["ffmpeg", "-y", "-i", clips[0], "-filter_complex", fc,
                   "-map", "[v]", "-map", "[a]",
                   "-c:v", "libx264", "-preset", QP["preset"], "-crf", str(QP["crf"]),
                   "-c:a", "aac", "-b:a", QP["audio_bitrate"], "-ar", "44100", "-ac", "2",
                   "-movflags", "+faststart", "-pix_fmt", "yuv420p", out_path]
        else:
            import shutil
            shutil.copy2(clips[0], out_path)
            return True
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=300)
            return Path(out_path).exists()
        except Exception:
            return False

    durs_eff = [durs[i] + (gaps[i] if i < len(gaps) else 0.0) for i in range(m)]
    cmd = ["ffmpeg", "-y"]
    for c in clips:
        cmd += ["-i", c]

    vparts, aparts = [], []
    for i in range(m):
        gi = gaps[i] if i < len(gaps) else 0.0
        vtail = (f",tpad=stop_mode=clone:stop_duration={gi:.3f}" if gi > 0 else "")
        # fps= no fim (25/10): no ffmpeg 7.x o settb/tpad deixam a taxa de quadros em 1/0 e o xfade recusa a entrada
        vparts.append(f"[{i}:v]format=yuv420p,fps={FPS},scale={W}:{H},setsar=1{vtail},"
                      f"settb=AVTB,setpts=PTS-STARTPTS,fps={FPS}[v{i}]")
        # SYNC FIX: força o áudio a ter EXATAMENTE durs_eff[i] segundos (pad até
        # esse total, depois corta). Sem isso, o áudio real diverge ~4-17ms do
        # que a matemática do xfade/offset assume (que usa durs_eff do probe), e
        # esse drift ACUMULA a cada acrossfade → falas de personagem saem
        # dessincronizadas depois de ~30s (vários clips curtos somados). A
        # narração não erra porque é contínua/longa.
        tgt = durs_eff[i]
        aparts.append(f"[{i}:a]aresample=44100,"
                      f"aformat=sample_fmts=fltp:channel_layouts=stereo,"
                      f"apad=whole_dur={tgt:.4f},atrim=0:{tgt:.4f},"
                      f"asetpts=PTS-STARTPTS[a{i}]")

    chain = []
    last_trans = None
    acc = durs_eff[0]
    starts = [0.0]  # posição real de início de cada clip no segmento
    v_cur, a_cur = "v0", "a0"
    gl_cortes = []  # (k, nome): fronteiras que viram transição gl-transitions (dona 02/11)
    gl_ok = bool(realce_visual and realce_visual.disponivel("transicao"))
    for k in range(1, m):
        v_out, a_out = f"vx{k}", f"ax{k}"
        soft = is_speech[k] and is_speech[k - 1]
        if soft:
            desc = descriptions[k] if k < len(descriptions) else ""
            trans, d = _pick_xfade(desc, supported, last_trans)
            d = max(0.10, min(d, durs_eff[k] * 0.5, acc * 0.5))
            # 24/10 (dono: "vídeos terminando sem terminar a fala"): no Short o respiro é ~0 e o acrossfade
            # comia a última sílaba de cada frase. Sem silêncio do tamanho da transição = corte seco.
            gprev = gaps[k - 1] if k - 1 < len(gaps) else 0.0
            soft = gprev + 0.07 >= d
            # Transição gl (dona 02/11, ANIME_GL_TRANS_CHANCE / REALCE_TRANSICAO=0): no lugar do xfade, junta seca e o
            # começo do clip k vira a transição a partir do último quadro do k-1 (cópia temporária, mesma duração,
            # áudio intacto). Vale também onde o respiro curto tirou o xfade: não sobrepõe áudio.
            if gl_ok and is_speech[k] and is_speech[k - 1] and random.random() < GL_TRANS_CHANCE:
                gl_cortes.append((k, random.choice(realce_visual.TRANSICOES)))
                soft = False
        if soft:
            last_trans = trans
            offset = max(0.0, acc - d)
            chain.append(f"[{v_cur}][v{k}]xfade=transition={trans}:"
                         f"duration={d:.3f}:offset={offset:.3f}[{v_out}]")
            chain.append(f"[{a_cur}][a{k}]acrossfade=d={d:.3f}[{a_out}]")
            starts.append(acc - d)  # o clip k começa onde o xfade inicia
            acc = acc + durs_eff[k] - d
        else:
            # 25/10: no ffmpeg 7.x (VPS/Kaggle, Linux) a saída do concat fica sem taxa de quadros (1/0) e o xfade seguinte
            # recusa ("inputs needs to be a constant frame rate") — o lote caía no concat simples: sem transição e com a
            # legenda na estimativa (desanda ao longo do vídeo). fps= devolve a taxa fixa.
            chain.append(f"[{v_cur}][v{k}]concat=n=2:v=1:a=0,fps={FPS}[{v_out}]")
            chain.append(f"[{a_cur}][a{k}]concat=n=2:v=0:a=1[{a_out}]")
            last_trans = None
            starts.append(acc)  # corte seco: começa exatamente no fim do anterior
            acc = acc + durs_eff[k]
        v_cur, a_cur = v_out, a_out

    _LAST_SEG_STARTS = starts
    _LAST_SEG_TOTAL = acc

    gl_tmp = None
    if gl_cortes:
        import shutil
        import tempfile
        gl_tmp = tempfile.mkdtemp(prefix="gltrans_")
        fontes = list(clips)  # o k-1 já transformado é o "de" do k (mesmo último quadro)
        for k, nome in gl_cortes:
            copia = str(Path(gl_tmp) / f"c{k:03d}.mp4")
            shutil.copy2(clips[k], copia)
            if realce_visual.transicao_inicio(copia, fontes[k - 1], nome=nome, dur=0.4, semente=k):
                fontes[k] = copia
                cmd[3 + 2 * k] = copia  # cmd = ["ffmpeg", "-y", "-i", c0, "-i", c1, ...]
        print(f"[xfade seg] {sum(1 for k, _ in gl_cortes if fontes[k] != clips[k])} transições gl", flush=True)

    filter_complex = ";".join(vparts + aparts + chain)
    cmd += ["-filter_complex", filter_complex,
            "-map", f"[{v_cur}]", "-map", f"[{a_cur}]",
            # 30/10 (Fable; dona: "92% há horas"): o junta-trechos é INTERMEDIÁRIO (a legenda regrava tudo depois); no
            # Top Fighter levou 57 min. ANIME_PRESET_INTER (longo.json: veryfast, crf 20 = sem perda visível) — vazio =
            # perfil de sempre (Shorts dos Cortes não mudam).
            "-c:v", "libx264", "-preset", os.environ.get("ANIME_PRESET_INTER") or QP["preset"],
            "-crf", str(20 if os.environ.get("ANIME_PRESET_INTER") else QP["crf"]),
            "-c:a", "aac", "-b:a", QP["audio_bitrate"], "-ar", "44100", "-ac", "2",
            "-movflags", "+faststart", "-pix_fmt", "yuv420p", out_path]
    try:
        if not (_celulares and _celulares.rodar_ffmpeg(cmd, timeout=900, rotulo=f"xfade {m} clipes {Path(out_path).name}")):
            subprocess.run(cmd, check=True, capture_output=True, timeout=900)
        if gl_tmp:
            shutil.rmtree(gl_tmp, ignore_errors=True)
        return Path(out_path).exists() and Path(out_path).stat().st_size > 1000
    except (subprocess.CalledProcessError, Exception) as e:
        if gl_tmp:
            shutil.rmtree(gl_tmp, ignore_errors=True)
        try:
            err = e.stderr.decode("utf-8", "ignore") if e.stderr else ""
            with open("xfade_debug_full.txt", "w", encoding="utf-8") as _dbg:
                _dbg.write("=== CMD ===\n" + " ".join(cmd))
                _dbg.write("\n\n=== FILTER_COMPLEX ===\n" + filter_complex)
                _dbg.write("\n\n=== STDERR ===\n" + err)
            print("[xfade seg] falhou. Fim do stderr:\n", err[-500:], flush=True)
        except Exception:
            pass
        return False
    except subprocess.TimeoutExpired:
        print("[xfade seg] timeout.", flush=True)
        return False


def _concat_segments(seg_paths, out_path):
    """Junta os segmentos já renderizados via concat demuxer (-c copy). Como
    todos saíram do mesmo encoder (mesmo codec/fps/sar/taxa), o copy é seguro e
    barato. Reencoda como fallback se o copy falhar."""
    seg_paths = [str(p) for p in seg_paths]
    if len(seg_paths) == 1:
        import shutil
        shutil.copy2(seg_paths[0], str(out_path))
        return True
    list_file = Path(seg_paths[0]).parent / "_xfseg_list.txt"
    with open(list_file, "w", encoding="utf-8") as f:
        for p in seg_paths:
            # caminho ABSOLUTO: FFmpeg 8.x resolve o path do concat relativo à
            # pasta do .txt; path relativo duplicaria o diretório.
            f.write(f"file '{Path(p).resolve().as_posix()}'\n")
    base = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file)]
    # Timeouts ESCALONADOS pela qtd de segmentos: um recap de 2h tem 100+ lotes;
    # o re-encode de fallback em libx264 num PC de 4 cores leva MUITO mais que os
    # 600s fixos antigos (era o que matava o render longo com pipeline_failed na
    # concat). Piso generoso + margem por segmento; teto abaixo dos 6h do daemon.
    n_seg = len(seg_paths)
    copy_to = min(3600, max(300, n_seg * 6))
    reenc_to = min(18000, max(1800, n_seg * 90))
    try:
        subprocess.run(base + ["-c", "copy", "-movflags", "+faststart", str(out_path)],
                       check=True, capture_output=True, timeout=copy_to)
        return Path(out_path).exists()
    except Exception:
        try:
            subprocess.run(base + ["-c:v", "libx264", "-preset", QP["preset"],
                           "-crf", str(QP["crf"]), "-c:a", "aac",
                           "-b:a", QP["audio_bitrate"], "-ar", "44100", "-ac", "2",
                           "-movflags", "+faststart", "-pix_fmt", "yuv420p", str(out_path)],
                           check=True, capture_output=True, timeout=reenc_to)
            return Path(out_path).exists()
        except Exception:
            return False
    finally:
        try: list_file.unlink()
        except Exception: pass


def concat_with_xfade(clips, out_path, descriptions=None, clip_texts=None, clip_sfx_dur=None):
    """Concatena clips com transições xfade REAIS entre eles, numa ÚNICA passada
    de filter_complex: vídeo via xfade + áudio via acrossfade (mesma duração por
    fronteira) → o áudio encolhe em lockstep com o vídeo, sem o bug de corrupção
    do xfade pair-by-pair. A transição varia pelo mood de cada painel.

    `clip_texts` (alinhado com `clips`) marca quais clips são FALA (texto != "").
    Clips de "respiro" (meme/transição/intro/outro) vêm com texto vazio.
    - Fronteira FALA→FALA: xfade (vídeo) + acrossfade (áudio) suave.
    - Fronteira que toca um respiro: CORTE SECO (concat, sem overlap) — assim a
      fala termina inteira e o meme toca inteiro, sem o áudio se atropelar.

    Em qualquer falha cai no concat simples (-c copy) pra nunca perder o vídeo.
    """
    clips = [str(c) for c in clips]
    n = len(clips)
    if n < 2:
        if clips:
            import shutil
            shutil.copy2(clips[0], str(out_path))
        return bool(clips)

    supported = _xfade_supported()
    durs = [_probe_dur(c) for c in clips]
    descriptions = descriptions or []
    # is_speech[i]: True se o clip tem fala (texto não-vazio). Sem a lista, assume
    # tudo fala (comportamento antigo). Respiros (meme/transição) têm texto "".
    if clip_texts:
        is_speech = [bool((clip_texts[i] if i < len(clip_texts) else "").strip())
                     for i in range(n)]
    else:
        is_speech = [True] * n

    # GAP (respiro) entre clips de fala — HÍBRIDO fixo+dinâmico:
    #   - MÍNIMO fixo: env CLIP_GAP_S (default 0.5s) — a cadência que o usuário
    #     aprovou; garante que o vídeo nunca fique acelerado.
    #   - DINÂMICO: se o PRÓXIMO clip carrega um SFX mais longo que o mínimo, o
    #     respiro cresce pra caber o som (gap = duração do SFX), dando espaço
    #     sonoro a ele em vez de atropelá-lo.
    #   - MÁXIMO fixo: env CLIP_GAP_MAX (default 1.2s) — teto pra um SFX muito
    #     longo não esticar o vídeo com pausa morta.
    #   - CLIP_GAP_DYNAMIC=0 desliga o crescimento (usa só o mínimo fixo).
    # Cada clip de fala ganha no FIM um congela-último-frame + silêncio do tamanho
    # do seu gap — vídeo e áudio crescem igual, sem desync. Memes/transições não.
    try:
        gap_base = max(0.0, float(os.environ.get("CLIP_GAP_S", "0.5")))
    except ValueError:
        gap_base = 0.5
    try:
        gap_cap = max(gap_base, float(os.environ.get("CLIP_GAP_MAX", "1.2")))
    except ValueError:
        gap_cap = 1.2
    # TOGGLE de SFX (env SFX_MODE):
    #   "gap" (default) = o respiro entre falas CRESCE pra o SFX tocar no silêncio,
    #                     sem atropelar a narração. (= gap dinâmico ligado)
    #   "junto" = o SFX sai POR CIMA da fala (gap fica só na base fixa, não cresce).
    # CLIP_GAP_DYNAMIC continua funcionando como override de baixo nível.
    sfx_mode = os.environ.get("SFX_MODE", "gap").strip().lower()
    if sfx_mode == "junto":
        gap_dyn = False
    elif sfx_mode == "gap":
        gap_dyn = True
    else:
        gap_dyn = os.environ.get("CLIP_GAP_DYNAMIC", "1") != "0"
    sfx_durs = clip_sfx_dur or [0.0] * n

    gaps = [0.0] * n
    for i in range(n):
        if not is_speech[i]:
            continue
        g = gap_base
        if gap_dyn and i + 1 < n:
            sfx_next = sfx_durs[i + 1] if i + 1 < len(sfx_durs) else 0.0
            if sfx_next > gap_base:
                g = min(sfx_next, gap_cap)
        gaps[i] = g
    # 24/10: a última fala ganha folga no fim (imagem parada + silêncio) — sem isso o Short acabava colado na
    # última palavra e o fim soava cortado.
    try:
        cauda = max(0.0, float(os.environ.get("CLIP_CAUDA_FIM", "0.6")))
    except ValueError:
        cauda = 0.6
    if is_speech[-1]:
        gaps[-1] = max(gaps[-1], cauda)
    # Log dos gaps dinâmicos que cresceram além da base (pra dar visibilidade ao
    # respiro que abre espaço pra um SFX longo no clip seguinte).
    _grown = [(i, round(gaps[i], 2)) for i in range(n) if gaps[i] > gap_base + 0.001]
    if _grown:
        print(f"  [gap dinâmico] base={gap_base:.2f}s teto={gap_cap:.2f}s · "
              f"respiros esticados p/ SFX longo: {_grown}", flush=True)

    # ── Render em LOTES pra não estourar memória ───────────────────────────
    # Um filter_complex com TODOS os clips de uma vez estoura a RAM (ffmpeg
    # -12 "Cannot allocate memory") por volta de ~25+ clips. Solução: processar
    # em lotes de XFADE_BATCH clips, cortando os lotes em fronteiras de CORTE
    # SECO (onde não há xfade a perder) e juntando os lotes com concat demuxer.
    try:
        max_batch = max(4, int(os.environ.get("XFADE_BATCH", "16")))
    except ValueError:
        max_batch = 8

    if n <= max_batch:
        ok = _render_xfade_segment(clips, durs, is_speech, gaps, descriptions,
                                   supported, str(out_path))
        if ok and Path(out_path).exists() and Path(out_path).stat().st_size > 1000:
            # offsets absolutos = os do único segmento
            global _CLIP_ABS_STARTS
            _CLIP_ABS_STARTS = list(_LAST_SEG_STARTS)
            return True
        return concat_with_transitions(clips, out_path, descriptions=descriptions)

    batches = _choose_xfade_batches(n, is_speech, max_batch)
    print(f"  [xfade lotes] {n} clips → {len(batches)} lotes {batches}", flush=True)
    tmp_dir = Path(clips[0]).parent
    seg_paths = []
    abs_starts = []      # posição absoluta de início de cada clip no vídeo final
    seg_base = 0.0       # deslocamento acumulado dos lotes anteriores
    for bi, (s, e) in enumerate(batches):
        seg_out = tmp_dir / f"_xfseg_{bi:02d}.mp4"
        ok = _render_xfade_segment(
            clips[s:e], durs[s:e], is_speech[s:e], gaps[s:e],
            descriptions[s:e] if descriptions else [],
            supported, str(seg_out))
        if not ok or not seg_out.exists():
            print(f"  [xfade lotes] lote {bi} falhou — fallback concat geral.", flush=True)
            return concat_with_transitions(clips, out_path, descriptions=descriptions)
        # acumula as posições reais deste lote, deslocadas pelo total dos anteriores.
        # lotes são unidos por corte seco (concat demuxer), então somam direto.
        for st in _LAST_SEG_STARTS:
            abs_starts.append(seg_base + st)
        # DESYNC FIX: avança seg_base pela duração REAL do segmento renderizado
        # (ffprobe), não pelo total MATEMÁTICO (_LAST_SEG_TOTAL/acc). O encoder
        # arredonda a duração final por causa de fps/keyframes, então o acc teórico
        # diverge alguns centésimos por lote — e como os lotes são concatenados pelos
        # arquivos reais, esse erro escalona A CADA lote e desloca a legenda dos
        # lotes seguintes (o "some/desanda a partir do meio"). Medir o real corrige.
        seg_real = _probe_dur(seg_out)
        seg_base += seg_real if seg_real and seg_real > 0 else _LAST_SEG_TOTAL
        seg_paths.append(seg_out)

    ok = _concat_segments(seg_paths, out_path)
    for p in seg_paths:
        try: p.unlink()
        except Exception: pass
    if ok and Path(out_path).exists() and Path(out_path).stat().st_size > 1000:
        _CLIP_ABS_STARTS = abs_starts
        return True
    return concat_with_transitions(clips, out_path, descriptions=descriptions)


def concat_with_transitions(clips, out_path, transition_dur=TRANSITION_DURATION,
                            descriptions=None):
    """Concatena clips com concat simples (-c copy).

    O xfade pair-by-pair corrompia o áudio depois de ~20 pares em vídeos longos.
    Transições visuais já estão embutidas em cada clip (fade-out + apply_effects_to_cmd),
    então concat simples mantém sincronia perfeita.
    """
    if len(clips) < 2:
        if clips:
            import shutil
            shutil.copy2(str(clips[0]), str(out_path))
        return bool(clips)

    tmp_dir = Path(clips[0]).parent
    list_file = tmp_dir / "_concat_final.txt"
    with open(list_file, "w") as f:
        for c in clips:
            # caminho ABSOLUTO: o FFmpeg 8.x resolve paths do concat list relativo
            # à pasta do .txt, então path relativo duplicaria o diretório.
            f.write(f"file '{Path(c).resolve().as_posix()}'\n")

    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(list_file), "-c", "copy",
        "-movflags", "+faststart", str(out_path),
    ]
    # Timeouts ESCALONADOS pela qtd de clips (fallback deste caminho concatena
    # TODOS os clips de uma vez: 2000+ num recap de 2h). Os 120s/300s fixos
    # antigos matavam o render longo (pipeline_failed na concat). Piso generoso
    # + margem por clip; teto abaixo dos 6h do daemon.
    n_clips = len(clips)
    copy_to = min(3600, max(300, n_clips * 2))
    reenc_to = min(18000, max(1800, n_clips * 12))
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=copy_to)
    except (subprocess.CalledProcessError, Exception):
        cmd_reenc = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file),
            "-c:v", "libx264", "-preset", QP["preset"], "-crf", str(QP["crf"]),
            "-c:a", "aac", "-b:a", QP["audio_bitrate"], "-ar", "44100", "-ac", "2",
            "-movflags", "+faststart", "-pix_fmt", "yuv420p",
            str(out_path),
        ]
        subprocess.run(cmd_reenc, check=True, capture_output=True, timeout=reenc_to)

    try:
        list_file.unlink()
    except Exception:
        pass

    ok = Path(out_path).exists() and Path(out_path).stat().st_size > 1000
    if ok:
        # 03/11 dona (KbLv rtQ6e-xzXuI "legenda dessincronizada desde o 1º meme"): o xfade em lotes falhou com o disco
        # cheio e caiu AQUI, que não gravava o início de cada clipe — a legenda foi pela estimativa, sem os memes, e
        # desandou no 1º meme. Concat simples = os clipes um atrás do outro: o início é a soma exata das durações.
        global _CLIP_ABS_STARTS
        acc, starts = 0.0, []
        for c in clips:
            starts.append(acc)
            acc += _probe_dur(str(c)) or 0.0
        _CLIP_ABS_STARTS = starts
    return ok


# Resolução final de entrega (1080x1920 Full HD vertical)


# Resolução final de entrega (1080x1920 Full HD vertical)
W_FINAL, H_FINAL = 1080, 1920


def upscale_to_fullhd(video_in, video_out):
    """Upscala o vídeo de 720x1280 → 1080x1920 (lanczos, 1 passada rápida).

    Clips são renderizados em 720p pra velocidade. Upscale só no final,
    uma única vez, com qualidade boa (lanczos + CRF 20).
    """
    cmd = [
        "ffmpeg", "-y", "-i", str(video_in),
        "-vf", f"scale={W_FINAL}:{H_FINAL}:flags=lanczos",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-g", "30",
        "-c:a", "copy",
        "-movflags", "+faststart", "-pix_fmt", "yuv420p",
        str(video_out),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=600)
        return Path(video_out).exists() and Path(video_out).stat().st_size > 0
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, Exception):
        return False


def build_clip_animated(img_path, audio_path, out_path, panel_idx, effects_mgr, duration=None,
                        transition_type=None, sfx_file=None):
    """Cria clip animado de um painel manga — simula movimento sutil dos personagens.

    Técnicas aplicadas via FFmpeg:
    1. Breathing effect — zoom sinusoidal sutil (1.0→1.02) simulando respiração
    2. Parallax/Ken Burns com leve rotação — drift x/y + rotação (-0.5° a 0.5°)
    3. Hair/cloth flutter — deslocamento horizontal variável (mais no topo, menos na base)

    Para painéis altos (manhwa strips): pan vertical com breathing sobreposto.
    Para painéis médios/quadrados: background blur + animação no foreground.

    Fallback: se falhar/timeout, chama build_clip normal.
    """
    from PIL import Image
    img = Image.open(img_path)
    pw, ph = img.size

    if duration is None:
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                 "-of", "csv=p=0", str(audio_path)],
                capture_output=True, text=True, timeout=10,
            )
            duration = float(result.stdout.strip())
        except Exception:
            duration = 4.0
    duration = max(duration, 1.5)
    frames = int(duration * FPS)

    try:
        m = hashlib.md5()
        with open(img_path, "rb") as f: m.update(f.read())
        if audio_path and Path(audio_path).exists():
            with open(audio_path, "rb") as f: m.update(f.read())
        m.update(str(duration).encode('utf-8'))
        m.update("V1_ANIMATED".encode('utf-8'))  # 23/10: tirado o color_filter usado antes de existir (cache nunca valia)
        
        clip_hash = m.hexdigest()
        cached_clip = CACHE_DIR / f"{clip_hash}.mp4"
        
        if cached_clip.exists() and cached_clip.stat().st_size > 1000:
            shutil.copy2(str(cached_clip), str(out_path))
            return duration, f"{frames} frames (CACHED)"
    except Exception as e:
        clip_hash = None


    # Escolher cor e vinheta
    color = effects_mgr.pick_color()
    color_filter = color["filter"] if isinstance(color, dict) else color
    vignette = effects_mgr.pick_vignette()
    vignette_filter = vignette if isinstance(vignette, str) else (
        vignette["filter"] if isinstance(vignette, dict) else None)

    # Ratio da imagem vs canvas
    img_ratio = ph / pw

    # Animated zoompan: breathing + drift (sinusoidal)
    # Breathing cycle ~3s, drift cycle ~4s
    # z oscila entre 1.0 e 1.02 (sutil)
    # x drift: ±2 pixels sinusoidal
    # y drift: ±1 pixel sinusoidal (mais lento)
    animated_zoom_filter = (
        f"zoompan="
        f"z='1+0.02*sin(2*PI*on/({FPS}*3))':"
        f"x='iw/2-(iw/zoom/2)+2*sin(2*PI*on/({FPS}*4))':"
        f"y='ih/2-(ih/zoom/2)+1*sin(2*PI*on/({FPS}*5))':"
        f"d={frames}:s={W}x{H}:fps={FPS}"
    )

    # Para painéis altos: pan vertical com breathing sobreposto
    animated_tall_filter = (
        f"zoompan="
        f"z='1.25+0.02*sin(2*PI*on/({FPS}*3))':"
        f"x='iw/2-(iw/zoom/2)+2*sin(2*PI*on/({FPS}*4))':"
        f"y='if(lte(on,{FPS}),0,min(ih-ih/zoom,(on-{FPS})*3))+1*sin(2*PI*on/({FPS}*5))':"
        f"d={frames}:s={W}x{H}:fps={FPS}"
    )

    if img_ratio > 2.0:
        # Painel ALTO — pan vertical animado
        prescale = "scale=1080:-1"
        filters = [prescale, animated_tall_filter, color_filter]
        if vignette_filter:
            filters.append(vignette_filter)
        filters.append("format=yuv420p")
        filter_chain = ",".join(filters)
        filter_complex = f"[0:v]{filter_chain}[v]"
        extra_inputs = []
    else:
        # Painel médio/quadrado — background blur + foreground animado
        bg_path = Path(str(out_path) + "_bg.jpg")
        from PIL import ImageFilter, ImageEnhance

        # Cover-crop pro background
        scale_w = W / pw
        scale_h = H / ph
        scale = max(scale_w, scale_h)
        new_w = int(pw * scale)
        new_h = int(ph * scale)
        bg = img.resize((new_w, new_h), Image.LANCZOS)
        left = (new_w - W) // 2
        top = (new_h - H) // 2
        bg = bg.crop((left, top, left + W, top + H))
        bg = bg.filter(ImageFilter.GaussianBlur(radius=40))
        bg = ImageEnhance.Brightness(bg).enhance(0.35)
        bg.save(str(bg_path), quality=70)

        # Foreground com animação: scale to fit + color + animated zoompan
        # Para o foreground, usamos zoompan no input original pra criar animação
        # depois overlay no background
        fg_filter = (
            f"scale={W}:{H}:force_original_aspect_ratio=decrease,"
            f"{color_filter}"
        )
        if vignette_filter:
            fg_filter += f",{vignette_filter}"

        # O zoompan é aplicado na imagem foreground antes do overlay
        # Precisamos redimensionar pro tamanho que cabe no canvas
        fit_w = min(W, int(pw * (H / ph))) if img_ratio > (H / W) else W
        fit_h = min(H, int(ph * (W / pw))) if img_ratio <= (H / W) else H

        fg_animated_filter = (
            f"zoompan="
            f"z='1+0.02*sin(2*PI*on/({FPS}*3))':"
            f"x='iw/2-(iw/zoom/2)+2*sin(2*PI*on/({FPS}*4))':"
            f"y='ih/2-(ih/zoom/2)+1*sin(2*PI*on/({FPS}*5))':"
            f"d={frames}:s={fit_w}x{fit_h}:fps={FPS}"
        )

        filter_complex = (
            f"[0:v]scale={W}:{H}[bg];"
            f"[1:v]{fg_animated_filter},{color_filter}"
            f"{',' + vignette_filter if vignette_filter else ''}[fg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]"
        )
        extra_inputs = ["-r", str(FPS), "-loop", "1", "-t", f"{duration:.2f}", "-i", str(bg_path)]

    if extra_inputs:
        cmd = [
            "ffmpeg", "-y",
            *extra_inputs,
            "-r", str(FPS), "-loop", "1", "-t", f"{duration:.2f}", "-i", str(img_path),
            "-i", str(audio_path),
            "-filter_complex", filter_complex,
            "-map", "[v]", "-map", "2:a",
            "-r", str(FPS),
            "-c:v", "libx264", "-preset", QP["preset"], "-crf", str(QP["crf"]), "-g", "30",
            "-c:a", "aac", "-b:a", QP["audio_bitrate"], "-ar", "44100", "-ac", "2",
            "-pix_fmt", "yuv420p", "-t", f"{duration:.2f}",
            str(out_path),
        ]
    else:
        cmd = [
            "ffmpeg", "-y",
            "-r", str(FPS), "-loop", "1", "-t", f"{duration:.2f}", "-i", str(img_path),
            "-i", str(audio_path),
            "-filter_complex", filter_complex,
            "-map", "[v]", "-map", "1:a",
            "-r", str(FPS),
            "-c:v", "libx264", "-preset", QP["preset"], "-crf", str(QP["crf"]), "-g", "30",
            "-c:a", "aac", "-b:a", QP["audio_bitrate"], "-ar", "44100", "-ac", "2",
            "-pix_fmt", "yuv420p", "-t", f"{duration:.2f}",
            str(out_path),
        ]

    try:
        cmd = apply_effects_to_cmd(cmd, transition_type, sfx_file, duration)
        subprocess.run(cmd, check=True, capture_output=True, timeout=180)
        if extra_inputs:
            bg_path.unlink(missing_ok=True)
        if clip_hash and Path(out_path).exists():
            try: shutil.copy2(str(out_path), str(cached_clip))
            except Exception: pass
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, Exception) as e:
        if extra_inputs:
            bg_path.unlink(missing_ok=True)
        # Fallback: tentar build_clip normal
        return build_clip(img_path, audio_path, out_path, panel_idx, effects_mgr, duration, transition_type, sfx_file)



# 30/10 (Fable; dona: "o hipercool tem muitos efeitos bons, os que não acrescentam muito tempo podem ir pros longos"):
# CLOSE NO ROSTO do hipercool (fx_parallax.rostos: YOLOv8 de rosto de anime, ONNX na CPU, ~0,3 s por quadro). No longo
# o zoom ia pro centro / terço de cima às cegas; com ANIME_FX_ROSTO=1 o zoom-in/zoom-out MIRA o rosto do quadro do meio
# do trecho. Sem modelo, sem rosto ou qualquer erro = movimento de sempre. Custo: 1 quadro lido + 1 inferência por trecho.
MODELO_ROSTO = Path(os.environ.get("ANIME_ROSTO_MODELO", r"D:\hipercool-materiais\models\anime_face_yolov8s.onnx"))
_ROSTO = {"sess": None, "falhou": False}


def _rosto_no_trecho(video, t, flip):
    """(cx, cy) do maior rosto (fração do quadro DEPOIS do corte de 10% e do espelho do descaracterizador) ou None."""
    if os.environ.get("ANIME_FX_ROSTO") != "1" or _ROSTO["falhou"] or not MODELO_ROSTO.exists():
        return None
    try:
        import cv2
        import numpy as np
        with _CARGA:  # 02/11: clipes em paralelo — o modelo carrega 1 vez só
            if _ROSTO["sess"] is None:
                import onnxruntime as ort
                # 02/11 (pesquisa H6): GPU quando houver (Kaggle T4); o onnxruntime cai pra CPU se não tiver CUDA
                _ROSTO["sess"] = ort.InferenceSession(str(MODELO_ROSTO), providers=[
                    p for p in ("CUDAExecutionProvider", "CPUExecutionProvider") if p in ort.get_available_providers()])
        cap = cv2.VideoCapture(str(video))
        cap.set(cv2.CAP_PROP_POS_MSEC, max(0.0, float(t)) * 1000)
        ok, img = cap.read()
        cap.release()
        if not ok or img is None:
            return None
        h, w = img.shape[:2]
        s = 640 / max(h, w)
        nw, nh = int(round(w * s)), int(round(h * s))
        pad = np.full((640, 640, 3), 114, np.uint8)
        pad[:nh, :nw] = cv2.resize(img, (nw, nh))
        sess = _ROSTO["sess"]
        out = sess.run(None, {sess.get_inputs()[0].name: pad[:, :, ::-1].astype(np.float32).transpose(2, 0, 1)[None] / 255.0})[0][0].T
        out = out[(out[:, 4] >= 0.5) & (out[:, 2] / s / w >= 0.04) & (out[:, 2] / s / w <= 0.6)]
        if not len(out):
            return None
        cx, cy, bw, bh, _c = max(out, key=lambda r: r[2] * r[3])
        fx, fy = float(cx / s / w), float(cy / s / h)
        fx, fy = (fx - 0.05) / 0.9, (fy - 0.05) / 0.9  # corte de 10% centrado do descaracterizador
        if flip:
            fx = 1 - fx
        return (min(max(fx, 0.0), 1.0), min(max(fy, 0.0), 1.0))
    except Exception as e:  # noqa: BLE001 — efeito nunca derruba o trecho
        _ROSTO["falhou"] = True
        logging.warning(f"[rosto] detector indisponível ({type(e).__name__}: {e}) — zoom como antes")
        return None


# 30/10 (Fable; dona: "muito importante mirar no rosto no zoom; pode ser em objetos importantes naquela hora, como uma
# poção de cura ou espada, coisa que tenha ganhado ênfase naquele quadro"): quando a FRASE cita um objeto, o Gemini
# (visão, pelo gateway) diz onde ele está no quadro e o trecho faz zoom-in nele. Máx. ANIME_FX_OBJETO_MAX por vídeo,
# 1 a cada 3 trechos no mínimo; sem objeto achado = rosto/movimento de sempre. ANIME_FX_OBJETO=1.
_OBJETO_RX = re.compile(
    r"\b(espadas?|l[aâ]minas?|adagas?|punhal|facas?|lan[çc]as?|arcos?|flechas?|machados?|martelos?|escudos?|cajados?|"
    r"varinhas?|po[çc][aãõ]o|po[çc][oõ]es|frascos?|elixir|p[ií]lulas?|an[ée]is|anel|colar|amuletos?|cristal|cristais|"
    r"pedras?|gemas?|joias?|coroas?|livros?|grim[oó]rio|pergaminhos?|mapas?|cartas?|chaves?|celular|telefone|pistolas?|"
    r"rev[oó]lver|armas?|moedas?|ba[uú]s?|tesouro|sementes?|frutas?|ovos?|n[uú]cleo|orbes?|selos?|m[aá]scaras?|"
    r"ampulheta|rel[oó]gio|bolsa|caixa|garrafa)\b", re.I)
_OBJ = {"n": 0, "ultimo": -100, "falhou": 0}


def _visao_rapida(b, pergunta, gateway, modelo, prazo=30):
    import base64
    import json as _json
    import urllib.request
    base, tok = gateway
    corpo = {"model": modelo, "max_tokens": 600, "temperature": 0.1, "messages": [{"role": "user", "content": [
        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode(b).decode()}},
        {"type": "text", "text": pergunta}]}]}
    req = urllib.request.Request(base + "/v1/chat/completions", data=_json.dumps(corpo).encode(),
                                 headers={"Content-Type": "application/json", "Authorization": "Bearer " + tok})
    with urllib.request.urlopen(req, timeout=prazo) as r:
        c = _json.loads(r.read())["choices"][0]["message"]["content"]
    return c if isinstance(c, str) else "".join(p.get("text", "") for p in c)


def _objeto_no_trecho(video, t, texto, idx, flip):
    """(cx, cy) do objeto citado na frase (fração do quadro depois do corte de 10%/espelho) ou None."""
    if os.environ.get("ANIME_FX_OBJETO") != "1" or not texto or _OBJ["falhou"] >= 5:
        return None
    m = _OBJETO_RX.search(texto)
    if not m or _OBJ["n"] >= int(os.environ.get("ANIME_FX_OBJETO_MAX", "40")) or idx - _OBJ["ultimo"] < 3:
        return None
    try:
        import cv2
        import json as _json
        cap = cv2.VideoCapture(str(video))
        cap.set(cv2.CAP_PROP_POS_MSEC, max(0.0, float(t)) * 1000)
        ok, img = cap.read()
        cap.release()
        if not ok or img is None:
            return None
        h, w = img.shape[:2]
        s = 640 / max(h, w)
        ok, jpg = cv2.imencode(".jpg", cv2.resize(img, (int(w * s), int(h * s))), [cv2.IMWRITE_JPEG_QUALITY, 85])
        import visao_capa
        import capa_ia_anime
        obj = m.group(0)
        pergunta = (f'This is a frame from a manhwa/anime recap. The narration now says: "{texto[:200]}". Find the '
                    f'"{obj}" mentioned (the object being emphasized). Reply ONLY JSON: {{"achou": true/false, '
                    '"caixa": [ymin, xmin, ymax, xmax]}} with coordinates normalized 0-1000; achou=false if it is not '
                    'clearly visible.')
        # 30/10: visao_capa.perguntar tenta antes o Gemini direto (429 + novas tentativas) = 2-4 MIN por quadro no teste;
        # aqui só o modelo rápido do gateway com prazo curto (render não pode esperar)
        r = None
        g = capa_ia_anime._gateway()
        for modelo in ("antigravity/gemini-3-flash", "gemini-fila"):
            try:
                txt = _visao_rapida(jpg.tobytes(), pergunta, g, modelo)
                r = _json.loads(re.search(r"\{.*\}", txt or "", re.S).group(0))
                break
            except Exception:  # noqa: BLE001
                continue
        _OBJ["ultimo"] = idx
        if not r:
            _OBJ["falhou"] += 1
            return None
        _OBJ["n"] += 1
        cx = cy = None
        if r.get("achou") and isinstance(r.get("caixa"), list) and len(r["caixa"]) == 4:
            y0, x0, y1, x1 = (float(v) / 1000 for v in r["caixa"])
            if 0.005 < (x1 - x0) * (y1 - y0) < 0.6:  # caixa que é a tela inteira não é "o objeto"
                cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        if cx is None:
            return None
        cx, cy = (cx - 0.05) / 0.9, (cy - 0.05) / 0.9
        if flip:
            cx = 1 - cx
        logging.info(f"[objeto] trecho {idx}: '{obj}' em {cx:.2f},{cy:.2f}")
        return (min(max(cx, 0.0), 1.0), min(max(cy, 0.0), 1.0))
    except Exception as e:  # noqa: BLE001
        _OBJ["falhou"] += 1
        logging.warning(f"[objeto] visão indisponível ({type(e).__name__}: {str(e)[:80]}) — zoom como antes")
        return None


def _movimento(idx, dur, out_w, out_h, impacto=False, cy=None, rosto=None, forcar_zoom=False):
    """Câmera por trecho (dono 17/10: "manhwa-react e hipercool adicionam muitos efeitos, temos que adicionar pra ficar
    no mínimo diferente além do áudio e trilha"). Só com ANIME_FX_MOV=1 (o anime_auto liga no parceiro).
    Ciclo zoom-in / pan esq / zoom-out / pan dir. Zoom/pan ancorado no terço superior (~0.30) para priorizar rostos e
    evitar decapitação de personagens no crop 16:9. Frase de impacto (curva de narração): tremida que some em ~0,6 s
    + flash curto.
    12/11 (melhorador do recap longo): GANCHO = primeiros ANIME_FX_GANCHO_N trechos (padrão 2, ~6 s) têm câmera
    dinâmica OBRIGATÓRIA (zoom punch a cada 1,5 s + pan contínuo vai-e-volta), mesmo sem ANIME_FX_MOV — ganchos
    estáticos (8m6TEKqvxfY 5,4%, GMuCrqDRe9A 4,2% de movimento) derrubavam o tempo assistido. ANIME_FX_GANCHO=0 desliga."""
    try:
        n_gancho = int(os.environ.get("ANIME_FX_GANCHO_N", "2") or 2)
    except ValueError:
        n_gancho = 2
    gancho = os.environ.get("ANIME_FX_GANCHO", "1") != "0" and idx < n_gancho
    if os.environ.get("ANIME_FX_MOV", "0") != "1" and not gancho:
        return ""
    try:
        anchor_default = float(os.environ.get("ANIME_FX_ANCHOR_Y", "0.30"))
    except ValueError:
        anchor_default = 0.30
    # Priorizar topo/rostos no terço superior (limite de segurança 0.35 para evitar decapitação)
    cy = min(max(float(cy if cy is not None else anchor_default), 0.0), 0.35)
    n = max(1, int(float(dur or 3) * 30))
    tipo = 0 if forcar_zoom else idx % 4  # 30/10: objeto citado = sempre zoom-in nele
    # 28/10 dona (item 1 aprovado, "câmera dentro da imagem"): ANIME_FX_ZOOM = quanto a câmera anda (0,12 antes; o
    # longo usa 0,25) e ANIME_FX_DERIVA=1 = sobe/desce junto, parece 2.5D. Medido: custo ~0 (bench_efeitos v3).
    try:
        zz = min(max(float(os.environ.get("ANIME_FX_ZOOM", "0.12")), 0.0), 0.4)
    except ValueError:
        zz = 0.12
    # 31/10 dona: movimento SUAVE nas imagens paradas (paisagem) — a câmera acelera e freia (cosseno) em vez de andar
    # em linha reta, e flutua de leve. ANIME_FX_SUAVE=1.
    suave = os.environ.get("ANIME_FX_SUAVE") == "1" and not rosto and not impacto and not gancho
    prog = f"(1-cos(PI*min(on/{n},1)))/2" if suave else f"min(on/{n},1)"
    # 31/10 dona: ZOOM MÚLTIPLO — 3 zooms secos seguidos até o alvo (rosto/objeto), 1 a cada ANIME_FX_MULTIZOOM_CADA
    # trechos com alvo. Cada degrau sobe em 3 quadros e segura 5.
    multi = (os.environ.get("ANIME_FX_MULTIZOOM") == "1" and rosto and n > 30 and not gancho
             and idx % max(1, int(os.environ.get("ANIME_FX_MULTIZOOM_CADA", "6") or 6)) == 0)
    if gancho:
        # punch: entra em 1,34x e assenta em 1,18x em ~0,3 s, repete a cada 45 quadros (1,5 s);
        # pan contínuo de borda a borda da folga, ida e volta a cada 3 s (~7 px/quadro no 1280)
        z = "1.18+0.16*exp(-mod(on,45)/5)"
        x = "(iw-iw/zoom)*(0.5-0.5*cos(2*PI*on/90))"
        logging.info(f"[gancho] trecho {idx}: zoom punch + pan contínuo")
    elif multi:
        # 31/10 dona aprovou o de 3 degraus e pediu variações: (degraus, tamanho do degrau, quadros entre degraus)
        passos, deg, esp = [(3, 0.22, 8), (2, 0.35, 10), (4, 0.15, 7), (3, 0.12, 6), (5, 0.12, 6)][
            (idx // max(1, int(os.environ.get("ANIME_FX_MULTIZOOM_CADA", "6") or 6))) % 5]
        tipo = 0
        zz = passos * deg
        z, x = (f"1+{deg:.2f}*min(floor(on/{esp})+min(mod(on,{esp})/3,1),{passos})", "(iw-iw/zoom)/2")
    elif tipo == 0:
        z, x = "min(1+%.3f*%s,%.3f)" % (zz, prog, 1 + zz), "(iw-iw/zoom)/2"
    elif tipo == 2:
        z, x = "max(%.3f-%.3f*%s,1)" % (1 + zz, zz, prog), "(iw-iw/zoom)/2"
    else:
        z = "%.3f" % (1 + zz * 0.85)
        x = "(iw-iw/zoom)*%s" % prog if tipo == 1 else "(iw-iw/zoom)*(1-%s)" % prog
    y = f"{cy:.2f}*(ih-ih/zoom)"
    mira = None
    if rosto and tipo in (0, 2) and not gancho:  # no gancho o pan contínuo manda (mira fixa = câmera parada)
        # janela de zoom com o rosto no centro: canto = (rosto − metade da janela) / folga, por eixo, entre 0 e 1
        zf = 1 + zz
        fx, fy = rosto
        mira = (min(max((fx - 0.5 / zf) / (1 - 1 / zf), 0.0), 1.0), min(max((fy - 0.5 / zf) / (1 - 1 / zf), 0.0), 1.0))
        x, y = f"{mira[0]:.3f}*(iw-iw/zoom)", f"{mira[1]:.3f}*(ih-ih/zoom)"
    # 28/10 dona: "não é tremida em todo trecho, é um BALANÇO nas lutas" — câmera balança devagar nas frases de
    # impacto (ANIME_FX_BALANCO=1). Medido: custo ~0 (bench 11_balanco_desloca).
    if impacto and os.environ.get("ANIME_FX_BALANCO") == "1":
        x = f"({x})+min((iw-iw/zoom)/2,18)*sin(on/9)"
    if os.environ.get("ANIME_FX_DERIVA") == "1" and mira is None:  # mirando o rosto, a deriva não puxa pra fora dele
        # Deriva 2.5D com offset Y inicial ancorado no terço superior (~0.25 a 0.35),
        # oscilando suavemente sem descer para a zona de corte/decapitação (antigo 0.70 cortava cabeças).
        y0 = max(0.05, cy - 0.05)
        y1 = min(0.36, cy + 0.05)
        dy = y1 - y0
        y = "(ih-ih/zoom)*(%s)" % (
            f"{y0:.2f}+{dy:.2f}*on/{n}" if idx % 2 == 0 else f"{y1:.2f}-{dy:.2f}*on/{n}"
        )
    if suave:  # flutuação leve por cima do caminho (some sozinha se a folga do zoom for pequena)
        x = f"min(max(({x})+min((iw-iw/zoom)/4,14)*sin(on/41),0),iw-iw/zoom)"
        y = f"min(max(({y})+min((ih-ih/zoom)/4,9)*sin(on/53),0),ih-ih/zoom)"
    if multi:
        logging.info(f"[multizoom] trecho {idx}: {passos} zooms de {deg:.2f} no alvo")
    # sem ampliar antes (2x pesava demais com o PC cheio do hipercool; 12% de zoom quase não perde nitidez)
    f = (f",fps=30,zoompan=z='{z}':x='{x}':y='{y}'"
         f":d=1:s={out_w}x{out_h}:fps=30")
    if impacto:
        f += (f",crop={out_w - 28}:{out_h - 28}:x='14+12*exp(-5*t)*sin(t*47)':y='14+12*exp(-5*t)*cos(t*43)'"
              f",scale={out_w}:{out_h},eq=brightness=0.28:enable='lt(t,0.10)'")
        # 28/10 dona (aprovado): balanço com leve ROTAÇÃO nas lutas (+3,8% no longo; só nas frases de impacto)
        if os.environ.get("ANIME_FX_BALANCO_ROT") == "1":
            f += (f",rotate=0.022*sin(2*PI*t/1.6):fillcolor=black,crop={out_w - 56}:{out_h - 32},"
                  f"scale={out_w}:{out_h}")
        # 28/10 dona (item 6 aprovado): glitch de cor no golpe, só nas frases de impacto (~10%: +5% na montagem)
        if os.environ.get("ANIME_FX_GLITCH") == "1":
            f += ",rgbashift=rh=-6:bh=6:gv=3:enable='lt(t,0.35)'"
    elif os.environ.get("ANIME_FX_TREMIDA_TODOS") == "1":
        # 28/10 dona (aprovado): tremida + clarão em todo trecho — versão LEVE (metade da do impacto), pra não cansar
        f += (f",crop={out_w - 14}:{out_h - 14}:x='7+6*exp(-6*t)*sin(t*47)':y='7+6*exp(-6*t)*cos(t*43)'"
              f",scale={out_w}:{out_h},eq=brightness=0.12:enable='lt(t,0.06)'")
    return f


# 29/10 dona: "as transições de fogo/gelo/água são antigas; as boas são os EFEITOS da divisão de tela do manhwa-react —
# não só uma linha, algo encorpado caminhando na transição". Faixa animada (bin/gera_divisoria.py, gerada com o código
# do manhwa-react: raios ramificados, línguas de fogo, glitch; 300 px de largura, 1 s) ATRAVESSA a tela no começo do
# trecho, de fora a fora: atrás dela a cena nova, na frente a mesma cena borrada e escura.
# 1 a cada ANIME_FX_DIVISORIA_CADA trechos (ANIME_FX_DIVISORIA=1).
_DIV = {"ultimo": -100, "n": 0}
DIVISORIA_S = 0.8
LARG_FAIXA = 300  # largura da faixa gerada (gera_divisoria.LARGURA_FAIXA), em px na altura 720


def _quer_divisoria(idx):
    if os.environ.get("ANIME_FX_DIVISORIA") != "1":
        return None
    if idx - _DIV["ultimo"] < int(os.environ.get("ANIME_FX_DIVISORIA_CADA", "6") or 6):
        return None
    pasta = Path(__file__).resolve().parent.parent / "workspace" / "assets" / "overlays_leves"
    estilos = sorted(pasta.glob("_divisoria_*.webm"))
    if not estilos:
        return None
    _DIV["ultimo"] = idx
    _DIV["n"] += 1
    return str(estilos[_DIV["n"] % len(estilos)]), _DIV["n"] % 2 == 0


def _com_divisoria(cmd, div, out_w, out_h):
    try:
        arq, da_esquerda = div
        k = cmd.index("-filter_complex")
        fc = cmd[k + 1]
        if fc.count("[vout]") != 1:
            return cmd
        n = sum(1 for x in cmd[:k] if x == "-i")
        T = DIVISORIA_S
        # centro da faixa vai de fora da tela (−w/2) até o outro lado (W + w/2): entra e sai inteira
        frente = f"(W+w)*t/{T}-w/2" if da_esquerda else f"W+w/2-(W+w)*t/{T}"
        # a parte borrada (cena antiga) anda junto com o centro do feixe: some quando ele sai da tela
        borr_x = f"(W+{LARG_FAIXA})*t/{T}-{LARG_FAIXA // 2}" if da_esquerda else \
            f"-(W+{LARG_FAIXA})*t/{T}+{LARG_FAIXA // 2}"
        fc = (fc.replace("[vout]", "[dvb]") + f";[dvb]split[dva][dvc];[dvc]gblur=sigma=28,eq=brightness=-0.22[dvd];"
              f"[dva][dvd]overlay=x='{borr_x}':y=0:enable='lt(t,{T})'[dve];"
              f"[{n}:v]scale=-2:{out_h},format=yuva420p[dvs];"
              f"[dve][dvs]overlay=x='{frente}-w/2':y=0:enable='lt(t,{T})':eof_action=pass:shortest=0[vout]")
        novo = list(cmd)
        novo[k + 1] = fc
        return novo[:k] + ["-c:v", "libvpx-vp9", "-i", arq] + novo[k:]
    except (ValueError, IndexError):
        return cmd


# 29/10 dona: "não vi nenhum meme visual como os do hipercool (vídeos, memes, figurinhas na tela)". Figurinha =
# meme estampado por cima do trecho (sem som) quando a frase tem gatilho de emoção (bin/memes_visuais.py, copiado do
# fx_memes do hipercool); 1 a cada ANIME_MEMES_FIG_CADA trechos (ANIME_MEMES_FIGURINHA=1).
_FIG = {"ultimo": -100, "usados": set()}


def _quer_figurinha(texto, idx, dur):
    if os.environ.get("ANIME_MEMES_FIGURINHA") != "1" or not texto or (dur or 0) < 2.0:
        return None
    if idx - _FIG["ultimo"] < int(os.environ.get("ANIME_MEMES_FIG_CADA", "5") or 5):
        return None
    try:
        import memes_visuais as mv
    except Exception:  # noqa: BLE001
        return None
    emo = mv.emocao(texto)
    m = mv.escolher(emo, _FIG["usados"]) if emo else None
    if not m:
        return None
    _FIG["ultimo"] = idx
    return m["file"]


def _com_figurinha(cmd, arq, out_w, out_h, dur):
    try:
        k = cmd.index("-filter_complex")
        fc = cmd[k + 1]
        if fc.count("[vout]") != 1:
            return cmd
        n = sum(1 for x in cmd[:k] if x == "-i")
        ext = Path(arq).suffix.lower()
        entrada = (["-loop", "1", "-t", f"{dur:.2f}", "-i", arq] if ext in (".jpg", ".jpeg", ".png") else
                   ["-ignore_loop", "0", "-i", arq] if ext == ".gif" else ["-stream_loop", "-1", "-i", arq])
        ini, fim = 0.3, min(dur - 0.2, 2.8)
        alt = int(out_h * 0.46) // 2 * 2
        # pop-in: cresce de 70% a 100% em 0,15 s; canto de cima à direita (a legenda fica embaixo, no meio)
        fc = (fc.replace("[vout]", "[fgb]") + f";[{n}:v]fps=30,scale=-2:{alt},format=rgba,setpts=PTS-STARTPTS+{ini}/TB,"
              f"scale=w='iw*min(1,0.7+2*max(0,t-{ini}))':h=-2:eval=frame[fgm];"
              f"[fgb][fgm]overlay=x=W-w-{int(out_w * 0.04)}:y={int(out_h * 0.06)}:"
              f"enable='between(t,{ini},{fim:.2f})':eof_action=pass:shortest=0[vout]")
        novo = list(cmd)
        novo[k + 1] = fc
        return novo[:k] + entrada + novo[k:]
    except (ValueError, IndexError):
        return cmd


# 28/10 dona: brilho (bloom) e paralaxe "5x menos" — em vez de todo trecho (+23% e +18%), só ~1 em 5, nos que
# combinam. Brilho: frase com luz/fogo/magia/golpe, no máximo 1 a cada ANIME_FX_BLOOM_CADA trechos.
_LUZ = re.compile(r"\b(fogo|chama|queim|explo|brilh|luz|lumin|raio|trov|rel[aâ]mpag|magia|m[aá]gic|feiti|poder|"
                  r"energia|aura|sol\b|estrela|lâmina|espada|golpe|ataque|desperta|transform)", re.I)
_BLOOM = {"ultimo": -100}


def _quer_bloom(texto, idx, impacto):
    if os.environ.get("ANIME_FX_BLOOM") != "1" or not (impacto or (texto and _LUZ.search(texto))):
        return False
    if idx - _BLOOM["ultimo"] < int(os.environ.get("ANIME_FX_BLOOM_CADA", "5") or 5):
        return False
    _BLOOM["ultimo"] = idx
    return True


def _com_bloom(cmd, out_w, out_h):
    """Halo nas partes claras (a mesma receita medida no bench 5_bloom_brilho), por cima do [vout]."""
    try:
        k = cmd.index("-filter_complex")
        if cmd[k + 1].count("[vout]") != 1:
            return cmd
        novo = list(cmd)
        novo[k + 1] = (cmd[k + 1].replace("[vout]", "[blb]") + f";[blb]split[bla][blc];[blc]scale={out_w // 4}:"
                       f"{out_h // 4},gblur=sigma=6,scale={out_w}:{out_h},curves=all='0/0 0.6/0.15 1/1'[blg];"
                       f"[bla][blg]blend=all_mode=screen:all_opacity=0.5[vout]")
        return novo
    except (ValueError, IndexError):
        return cmd


# Paralaxe 2.5D de verdade (profundidade por IA, bin\parallax25d.py) só nos MOMENTOS-CHAVE: os trechos do resumo de
# abertura e 1 em ANIME_FX_25D_CADA frases de impacto. O quadro do meio do trecho vira a cena 2.5D e segue o mesmo
# caminho dos outros trechos (espelho, câmera, overlays, legenda).
_DEPTH = {}
_CARGA = __import__("threading").Lock()  # 02/11: carga dos modelos com clipes em paralelo
_P25 = {"impactos": 0}


def _quer_25d(idx, impacto):
    if os.environ.get("ANIME_FX_25D") != "1":
        return False
    if idx < int(os.environ.get("ANIME_RESUMO_N", "0") or 0):
        return True
    if impacto:
        _P25["impactos"] += 1
        return _P25["impactos"] % int(os.environ.get("ANIME_FX_25D_CADA", "5") or 5) == 1
    return False


def _cena_25d(video_source, t, dur, out_path, idx):
    """mp4 (sem áudio, tamanho da fonte) com a câmera entrando no quadro em 2.5D, ou None se não deu."""
    import numpy as np
    import parallax25d as p25
    from PIL import Image
    try:
        bruto = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", video_source, "-frames:v", "1",
                                "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True, timeout=60).stdout
        import io
        img = Image.open(io.BytesIO(bruto)).convert("RGB")
        with _CARGA:  # 02/11: clipes em paralelo — o modelo carrega 1 vez só
            if "pipe" not in _DEPTH:
                from transformers import pipeline
                try:  # 02/11 (pesquisa H6): GPU quando houver (no Kaggle a T4 ficava parada aqui)
                    import torch
                    _dev = 0 if torch.cuda.is_available() else -1
                except Exception:  # noqa: BLE001
                    _dev = -1
                _DEPTH["pipe"] = pipeline("depth-estimation", model="depth-anything/Depth-Anything-V2-Small-hf",
                                          device=_dev)
        d = np.array(_DEPTH["pipe"](img)["depth"].resize(img.size), dtype=np.float32)
        import cv2
        d = cv2.GaussianBlur((d - d.min()) / (d.max() - d.min() + 1e-6), (0, 0), 3)
        quadro = np.array(img)[:, :, ::-1].copy()
        w, h = img.size
        n = max(2, int(dur * 30))
        mov = ("push_in", "orbit", "float")[idx % 3]
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{w}x{h}",
                                "-r", "30", "-i", "-", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18",
                                "-pix_fmt", "yuv420p", out_path], stdin=subprocess.PIPE)
        for i in range(n):
            dx, dy, zoom = p25.camera_path(mov, i / (n - 1), 14.0)
            enc.stdin.write(p25.warp(quadro, d, dx, dy, zoom).tobytes())
        enc.stdin.close()
        enc.wait(timeout=300)
        return out_path if enc.returncode == 0 and Path(out_path).exists() else None
    except Exception as e:  # noqa: BLE001 — efeito extra nunca derruba o trecho
        logging.warning(f"[2.5D] trecho {idx} sem paralaxe ({type(e).__name__}: {e})")
        return None


# 28/10 dona (aprovados): PARTÍCULAS nas cenas que combinam (ANIME_FX_PARTICULAS=1) e TRANSIÇÕES de elemento (fogo,
# água, raio, rasgar...; ANIME_FX_TRANSICAO=1, no máximo 1 a cada ANIME_FX_TRANSICAO_CADA trechos). Escolha pela
# frase narrada (elemental_transitions.detect_element: categoria 1 = transição no começo do trecho, 2 = partícula o
# trecho todo). Overlays LEVES deitados (hipercool-materiais\bin\overlays_leves.py, VP9 com alfa).
_OV = {"ultima_trans": -100}


def _overlay_do_trecho(texto, idx):
    part, trans = os.environ.get("ANIME_FX_PARTICULAS") == "1", os.environ.get("ANIME_FX_TRANSICAO") == "1"
    if not (part or trans) or not texto:
        return None
    try:
        import elemental_transitions as el
        elem = el.detect_element(texto)
    except Exception:  # noqa: BLE001
        return None
    if not elem or elem == "blood":
        return None
    arq = Path(__file__).resolve().parent.parent / "workspace" / "assets" / "overlays_leves" / f"{el._norm(elem)}.webm"
    if not arq.exists():
        return None
    cat = el.effect_cat(elem)
    cada = int(os.environ.get("ANIME_FX_TRANSICAO_CADA", "8") or 8)
    if cat == 1 and trans and idx - _OV["ultima_trans"] >= cada:
        _OV["ultima_trans"] = idx
        return str(arq), "transicao"
    if cat == 2 and part:
        return str(arq), "particula"
    return None


def decidir_trecho(panel_idx, impacto, subtitles):
    """A parte do clipe que depende da ORDEM (contadores de 2.5D e de transição de elemento): chamada em ordem pelo
    anime_segments antes de mandar o clipe pro pool (02/11). Barata: só lê env e o texto."""
    orient = os.environ.get("ANIME_ORIENT", "landscape").strip().lower()
    return {"25d": orient != "vertical" and _quer_25d(panel_idx, impacto),
            "ov": (_overlay_do_trecho(subtitles if isinstance(subtitles, str) else "", panel_idx)
                   if orient != "vertical" else None),
            "bloom": orient != "vertical" and _quer_bloom(subtitles if isinstance(subtitles, str) else "",
                                                         panel_idx, impacto)}


def _com_overlay(cmd, ov, dur, out_w, out_h):
    """Põe o overlay (VP9 alfa) por cima do [vout] do trecho: transição toca 1x no começo; partícula repete o trecho
    todo. Entrada nova no FIM (depois do SFX), saída continua [vout]. Qualquer coisa estranha = cmd como estava."""
    try:
        k = cmd.index("-filter_complex")
        fc = cmd[k + 1]
        if fc.count("[vout]") != 1:
            return cmd
        n = sum(1 for x in cmd[:k] if x == "-i")  # a entrada nova entra logo antes do -filter_complex
        laco = ["-stream_loop", "-1"] if ov[1] == "particula" else []
        entrada = laco + ["-c:v", "libvpx-vp9", "-i", ov[0]]
        fc = (fc.replace("[vout]", "[vbase]") + f";[{n}:v]scale={out_w}:{out_h},format=yuva420p,"
              f"trim=duration={float(dur):.2f},setpts=PTS-STARTPTS[ovl];"
              f"[vbase][ovl]overlay=0:0:eof_action=pass:shortest=0[vout]")
        novo = list(cmd)
        novo[k + 1] = fc
        return novo[:k] + entrada + novo[k:]
    except (ValueError, IndexError):
        return cmd


def build_clip_from_video(video_source, audio_path, out_path, panel_idx, effects_mgr, duration=None,
                          global_start_t=0.0,
                          has_name_tags=False, current_tag=None, next_tag=None,
                          name_tags_dict=None, character_roles=None, is_dialog=False,
                          subtitles=None, bgm=None, sfx=None,
                          clip_duration=None,   # duracao do clipe no timeline original (usado no clip recortado)
                          add_karaoke=False, add_watermark=True, impacto=False, decisao=None):
    '''
    Constrói um clipe animado tirando uma fatia de um arquivo de vídeo original.
    Serve para descaracterizar animes removendo o copyright e criando blocos.
    O vídeo é cortado usando -ss e -t, e depois é aplicado o filtro de descaracterização (hflip, eq, crop).
    '''
    import os
    import subprocess
    from effects_engine import W_FINAL, H_FINAL, FPS
    from fx_subtitles import _FONT_CANDIDATES_FALLBACK
    
    if clip_duration is None:
        if duration is not None:
             clip_duration = duration
        else:
             clip_duration = 3.0 # fallback default
             
    # Tempo inicial do corte no arquivo de video
    cut_start = global_start_t
    _janela_fonte = [None]  # 30/10: quanto ler da fonte (None = a duração do trecho; o sprint do resumo lê 2x)
    # 02/11: com clipes em paralelo, a escolha (2.5D / transição de elemento) vem PRONTA do loop em ordem (decidir_trecho):
    # os contadores _P25/_OV dependem da ordem e com threads ficavam aleatórios
    if decisao is None:
        decisao = decidir_trecho(panel_idx, impacto, subtitles)
    if decisao["25d"]:
        cena = _cena_25d(video_source, cut_start + clip_duration / 2, clip_duration, str(out_path) + ".25d.mp4", panel_idx)
        if cena:
            video_source, cut_start = cena, 0.0
            logging.info(f"[2.5D] trecho {panel_idx}: momento-chave em paralaxe")

    # Filtro descaracterizador mestre
    # Inverte horizontamente, corta 5% nas bordas (zoom in de 10%), satura 10%
    descaracterizador = "hflip,crop=in_w*0.90:in_h*0.90:in_w*0.05:in_h*0.05,eq=saturation=1.1:brightness=0.03"
    # ANIME_DESCARACT_FLIP=0 (Short de parceiro de MANHWA, 16/10): sem espelho — espelhar inverte o texto dos painéis
    # e dos balões ("FANGIRL NUMBERS HERE" de trás pra frente). Crop/zoom e cor continuam.
    if os.environ.get("ANIME_DESCARACT_FLIP", "1") == "0":
        descaracterizador = descaracterizador.replace("hflip,", "", 1)

    # Orientacao de saida:
    #  - "landscape" (16:9, DEITADO): formato PRINCIPAL do recap de anime.
    #    Anime ja e deitado → preenche a tela sem barra preta.
    #  - "vertical" (9:16, EM PE): formato de Shorts (derivado). Aqui o deitado
    #    nao preenche, entao usa cover (zoom pra encher) em vez de barra preta.
    # W/H vêm do fx_assets (decididos por ANIME_ORIENT no import): landscape=1280x720,
    # vertical=720x1280. Usa o MESMO tamanho do resto do motor (xfade/overlays), pra
    # não haver reescala surpresa depois. Upscale final leva pra 1080p.
    from fx_assets import W as out_w, H as out_h
    orient = os.environ.get("ANIME_ORIENT", "landscape").strip().lower()
    
    # Cobertura da legenda ORIGINAL queimada (hard-sub): o descaracterizador aplica
    # hflip, que ESPELHA a legenda velha (fica de trás pra frente). A dona pediu tarja
    # FOSCA (blur, não preta) sobre as faixas de TOPO e RODAPÉ (a fonte pode ter texto
    # em qualquer uma), com a nossa legenda PT queimada por cima depois
    # (anime_captions.burn_captions). Liga com ANIME_HARDSUB_COVER=1.
    hardsub_cover = os.environ.get("ANIME_HARDSUB_COVER", "0").strip() == "1"
    try:
        band_h = float(os.environ.get("ANIME_HARDSUB_BAND", "0.16"))
    except ValueError:
        band_h = 0.16
    band_h = min(max(band_h, 0.05), 0.30)
    # Faixa da legenda velha (anime_legenda_fonte, fração da altura da FONTE) passada
    # como "y_frac,h_frac" — só existe quando a fonte TEM legenda. COVER=1 (faixa fixa
    # do rodapé) só vem do --cover-hardsub explícito.
    rect_env = os.environ.get("ANIME_HARDSUB_RECT", "").strip()
    hardsub_rect = None
    if rect_env:
        try:
            ry, rh = (float(x) for x in rect_env.split(",")[:2])
            ry = min(max(ry, 0.0), 0.95)
            rh = min(max(rh, 0.03), 1.0 - ry)
            hardsub_rect = (round(ry, 4), round(rh, 4))
        except (ValueError, TypeError):
            logging.warning(f"[hardsub] ANIME_HARDSUB_RECT inválido: {rect_env!r}")
    do_cover = hardsub_cover and hardsub_rect is None  # faixa fixa: só com --cover-hardsub (nunca automática)
    _out = "[pre]" if do_cover else "[vout]"

    if orient == "vertical":
        short_source = os.environ.get("ANIME_SHORT_SOURCE", "reframe").strip().lower()
        if short_source == "native":
            # Native vertical source: scale directly to fill the frame (1280x720 sideways context)
            # We use force_original_aspect_ratio=decrease and pad just in case it's not EXACTLY 9:16
            scale_filter = (f"scale={out_w}:{out_h}:force_original_aspect_ratio=decrease,"
                            f"pad={out_w}:{out_h}:(ow-iw)/2:(oh-ih)/2:color=black")
            vf_mestre = f"[0:v]{descaracterizador},{scale_filter}{_movimento(panel_idx, clip_duration, out_w, out_h, impacto)}{_out}"
        else:
            # Reframe fallback (16:9 source): use anime_compose (blurred background layout)
            from anime_compose import get_vertical_filtergraph

            # Como o get_vertical_filtergraph gera um grafo *complexo* (com multiplos pads),
            # nao podemos apenas concatenar em cadeia com virgula.
            # [0:v] -> descaracterizador -> [desc]; [desc] -> vertical_filtergraph -> [vout]
            vf_mestre = (
                f"[0:v]{descaracterizador}[desc];" +
                get_vertical_filtergraph(in_pad="[desc]", out_pad=_out, out_w=out_w, out_h=out_h)
            )
    else:
        # deitado casa com a fonte 16:9 → decrease+pad quase nunca gera barra
        scale_filter = (f"scale={out_w}:{out_h}:force_original_aspect_ratio=decrease,"
                        f"pad={out_w}:{out_h}:(ow-iw)/2:(oh-ih)/2")
        # Priorizar topo/rostos no crop vertical 16:9 (terço superior ~0.30) para evitar decapitação.
        # Ancorar o zoom no terço superior em vez do rodapé (0.9+) que cortava olhos/testa/queixo (júri OLYsz-zu7Rs / YZNYmnqVZWI).
        try:
            ancora = float(os.environ.get("ANIME_FX_ANCHOR_Y", "0.30"))
        except ValueError:
            ancora = 0.30
        objeto = _objeto_no_trecho(video_source, cut_start + clip_duration / 2,
                                   subtitles if isinstance(subtitles, str) else "", panel_idx, "hflip" in descaracterizador)
        rosto = objeto or (_rosto_no_trecho(video_source, cut_start + clip_duration / 2, "hflip" in descaracterizador)
                           if panel_idx % 4 in (0, 2) else None)  # só os trechos de zoom-in/zoom-out usam a mira
        if rosto and not objeto:
            logging.info(f"[rosto] trecho {panel_idx}: zoom mirando o rosto em {rosto[0]:.2f},{rosto[1]:.2f}")
        # 30/10 (Fable; engenharia reversa: os de 450k-2,1M têm 25-51 cortes no 1º minuto e 12-18 depois; o Pastor teve
        # 17 no 1º e 41-45 depois): nas frases do RESUMO de abertura, corte seco a cada 2 s andando pra frente no mesmo
        # momento (lê 2x a duração da fonte e mostra 2 s de cada 4). ANIME_SPRINT_RESUMO=1 (longo.json).
        sprint = ""
        try:
            n_res = int(os.environ.get("ANIME_RESUMO_N") or 0)
        except ValueError:
            n_res = 0
        # L-06 (LONGOS_MELHORIAS, 01/11): 1º MINUTO acelerado (25-35 trocas; antes 2 s = ~15/min) e o resto normal
        # (~12-15/min). Vale no resumo E nas frases que começam no 1º minuto do longo (global_start_t só é da fonte, então
        # conta pelo índice: ~1 frase a cada 4-5 s -> as 13 primeiras). Corte seco a cada 1,2 s andando pra frente
        # no mesmo momento (lê 2x a duração, mostra 1,2 s de cada 2,4 s).
        no_1o_min = panel_idx < max(n_res, 13)
        if (os.environ.get("ANIME_SPRINT_RESUMO") == "1" and no_1o_min and clip_duration and clip_duration > 2.6
                and not str(video_source).endswith(".25d.mp4")):  # a cena 2.5D tem só a duração do trecho
            sprint = "fps=30,select='lt(mod(t,2.4),1.2)',setpts=N/30/TB,tpad=stop_mode=clone:stop_duration=10,"
            _janela_fonte[0] = clip_duration * 2 + 0.2
            logging.info(f"[sprint] trecho {panel_idx} (1º minuto): corte a cada 1,2 s")
        vf_mestre = (f"[0:v]{sprint}{descaracterizador},{scale_filter}"
                     f"{_movimento(panel_idx, clip_duration, out_w, out_h, impacto, ancora, rosto, bool(objeto))}{_out}")

    if hardsub_rect is not None:
        # Faixa DETECTADA (anime_legenda_fonte, só quando a fonte TEM legenda): borra SÓ a faixa da legenda velha, na
        # FONTE, antes do espelho/corte/escala — a fração é da altura da fonte e vale igual no deitado e no Short.
        # 25/10: era aplicada no quadro já cortado (crop de 90%) e caía ~4% acima da legenda deles.
        # A nossa legenda (e no longo a tarja de capítulo) entra por cima depois (anime_captions.burn_captions).
        ry, rh = hardsub_rect
        vf_mestre = (
            f"[0:v]split=2[hsbase][hsband];"
            f"[hsband]crop=iw:ih*{rh}:0:ih*{ry},gblur=sigma=20,"
            f"eq=brightness=0.10:saturation=0.55[hsblur];"
            f"[hsbase][hsblur]overlay=0:H*{ry}[hsrc];"
            + vf_mestre.replace("[0:v]", "[hsrc]", 1)
        )
    elif hardsub_cover:
        # Fallback: faixa fosca (blur pesado + leve clareada/dessaturada) cobrindo a
        # legenda velha SÓ no RODAPÉ. A legenda queimada de anime fica quase sempre
        # embaixo; borrar o TOPO só sujava o vídeo sem motivo (a dona pediu pra não
        # borrar em cima). Damos FOLGA: a faixa é um pouco mais alta que band_h e
        # começa um tico acima do rodapé, garantindo cobrir a legenda velha (e a
        # nossa PT entra por cima depois). band_h = altura base (fração da altura).
        band_h_fb = min(0.30, band_h + 0.04)  # folga vertical
        band_y = round(1.0 - band_h_fb, 4)
        vf_mestre += (
            f";[pre]split=2[cvbase][cvbot];"
            f"[cvbot]crop=iw:ih*{band_h_fb}:0:ih*{band_y},gblur=sigma=20,"
            f"eq=brightness=0.10:saturation=0.55[cvbblur];"
            f"[cvbase][cvbblur]overlay=0:H*{band_y}[vout]"
        )

    # Legenda NAO entra aqui: e queimada depois no video ja concatenado, via
    # anime_captions.burn_captions (PNG overlay do motor hipercool). drawtext no
    # ffmpeg do Windows crasha por fontfile, entao nem tentamos aqui.

    # Trilha de audio original e substituida pela gerada por TTS (audio_path)
    # Exata duracao do TTS = `-t {clip_duration}`
    # 0 = video_source (fatia), 1 = audio_path
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(cut_start),
        "-t", str(_janela_fonte[0] or clip_duration),  # 30/10: o sprint do resumo lê 2x a fonte
        "-i", video_source,
        "-i", audio_path,
        "-filter_complex", f"{vf_mestre}",
        "-map", "[vout]",
        "-map", "1:a",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k",
        "-t", str(clip_duration),
        out_path
    ]

    # Injeta o SFX/Meme no áudio via apply_effects_to_cmd (mesma passada do ffmpeg).
    # Só se `sfx` for um path de arquivo válido — pick_sfx_for_text pode devolver
    # (None, None); passar tupla/None viraria "-i (None, None)" e quebraria o ffmpeg.
    if isinstance(sfx, str) and sfx and os.path.exists(sfx):
        cmd = apply_effects_to_cmd(cmd, None, sfx, clip_duration)

    ov = decisao["ov"]
    if ov:
        cmd = _com_overlay(cmd, ov, clip_duration, out_w, out_h)
    if decisao["bloom"]:
        cmd = _com_bloom(cmd, out_w, out_h)
    div = _quer_divisoria(panel_idx) if orient != "vertical" else None
    if div:
        cmd = _com_divisoria(cmd, div, out_w, out_h)
        logging.info(f"[divisoria] trecho {panel_idx}: {Path(div[0]).stem}")
    fig = _quer_figurinha(subtitles if isinstance(subtitles, str) else "", panel_idx, clip_duration) \
        if orient != "vertical" else None
    if fig:
        cmd = _com_figurinha(cmd, fig, out_w, out_h, clip_duration)
        logging.info(f"[meme] figurinha no trecho {panel_idx}: {Path(fig).name}")

    logging.info(f"[build_clip_from_video] clipe {panel_idx} ({orient}) Start={cut_start:.2f}s Dur={clip_duration:.2f}s"
                 + (f" + {ov[1]} {Path(ov[0]).stem}" if ov else ""))

    # FFmpeg no Windows crasha de forma intermitente sob pressão de RAM/CPU
    # (access violation → returncode gigante tipo 4294967284/3752568763),
    # gerando um mp4 truncado ("moov atom not found") que depois quebra o concat.
    # Retentamos até 3x; a 2ª tentativa em diante cai pra preset mais leve de RAM.
    import time as _time
    for attempt in range(3):
        # Espera a RAM abrir ANTES de disparar o ffmpeg — se outro render pesado
        # está comendo memória, o clipe aguarda a janela em vez de crashar por OOM.
        _wait_for_ram()
        cmd_try = list(cmd)
        if attempt >= 1:
            # preset menos agressivo em memória/threads → menos chance de crash.
            cmd_try = _relax_encode(cmd_try)
            # Backoff crescente: o crash costuma ser OOM TRANSITÓRIO (outro render
            # comendo RAM no mesmo instante). Retentar em rajada bate na mesma
            # parede; esperar dá tempo do pico de memória passar antes de tentar de novo.
            _time.sleep(3.0 * attempt)
        try:
            subprocess.run(cmd_try, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            # 25/10: um longo no Kaggle teve os 582 clipes com rc=254 e o motivo sumia (stderr ia pro lixo)
            motivo = " | ".join(l.strip() for l in (e.stderr or b"").decode("utf-8", "replace").splitlines()[-3:] if l.strip())
            logging.warning(f"[build_clip_from_video] clipe {panel_idx} falhou (tentativa {attempt+1}/3, rc={e.returncode})"
                            f"{': ' + motivo[-400:] if motivo else ''}")
            if not os.path.exists(video_source):
                logging.error(f"[build_clip_from_video] o vídeo de origem SUMIU: {video_source}")
                return False
            continue
        # Só considera sucesso se o mp4 é REPRODUZÍVEL (tem stream de vídeo com duração).
        if _clip_is_valid(out_path):
            return True
        logging.warning(f"[build_clip_from_video] clipe {panel_idx} saiu corrompido (tentativa {attempt+1}/3)")
    logging.error(f"[build_clip_from_video] clipe {panel_idx} falhou após 3 tentativas")
    return False


def _relax_encode(cmd):
    """Troca preset ultrafast por veryfast e limita threads (menos RAM/CPU → menos crash)."""
    out = list(cmd)
    for i, tok in enumerate(out):
        if tok == "ultrafast":
            out[i] = "veryfast"
    if "-threads" not in out:
        # insere -threads 2 logo após "ffmpeg" "-y"
        out[2:2] = ["-threads", "2"]
    return out


def _free_ram_mb():
    """RAM física livre em MB (Windows, via ctypes — sem dependência nova).
    Retorna None se não der pra medir (aí o caller não espera)."""
    try:
        import ctypes
        class _MS(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong),
                        ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong),
                        ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong),
                        ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong),
                        ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
        st = _MS()
        st.dwLength = ctypes.sizeof(_MS)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st)):
            return st.ullAvailPhys / (1024 * 1024)
    except Exception:
        pass
    return None


def _cpu_load_pct():
    """Uso de CPU em % (média rápida via GetSystemTimes, sem psutil).
    Retorna None se não der pra medir (aí o caller não espera por CPU)."""
    import ctypes, time as _time
    try:
        k = ctypes.windll.kernel32

        class _FT(ctypes.Structure):
            _fields_ = [("dwLowDateTime", ctypes.c_ulong),
                        ("dwHighDateTime", ctypes.c_ulong)]

        def _snap():
            idle, kern, usr = _FT(), _FT(), _FT()
            if not k.GetSystemTimes(ctypes.byref(idle), ctypes.byref(kern), ctypes.byref(usr)):
                return None
            to_i = lambda f: (f.dwHighDateTime << 32) | f.dwLowDateTime
            return to_i(idle), to_i(kern), to_i(usr)

        a = _snap()
        if a is None:
            return None
        _time.sleep(0.25)
        b = _snap()
        if b is None:
            return None
        idle_d = b[0] - a[0]
        total_d = (b[1] - a[1]) + (b[2] - a[2])  # kernel já inclui idle
        if total_d <= 0:
            return None
        return max(0.0, min(100.0, (1.0 - idle_d / total_d) * 100.0))
    except Exception:
        return None


def _wait_for_ram(min_mb=1200, max_wait_s=1800):
    """Espera abrir janela de RAM E CPU antes de disparar um render pesado.

    Motivo: o ffmpeg do Windows crasha (OOM/access violation) e a máquina
    engasga quando outro app de vídeo (veo3/hipercool/outro ffmpeg) está
    comendo memória/CPU no mesmo instante. Em vez de brigar por recurso e
    falhar, o clipe ESPERA a janela abrir — assim o render "cabe" sozinho
    mesmo com outro projeto rodando em paralelo.

    Ao contrário da versão antiga (que desistia em 120s e seguia mesmo sem
    RAM, arriscando OOM), esta espera de verdade até `max_wait_s` (default
    30min) e avisa no log a cada ciclo. Se estourar o teto, segue mesmo
    assim (melhor tentar do que travar pra sempre), mas loga o aviso.

    Envs:
      ANIME_MIN_FREE_MB  RAM mínima livre em MB (0 desliga a espera). Default 1200.
      ANIME_MAX_CPU_PCT  CPU máxima tolerada em % (0/desativado ignora CPU). Default 85.
      ANIME_WAIT_MAX_S   teto de espera em s. Default 1800."""
    import time as _time
    try:
        min_mb = float(os.environ.get("ANIME_MIN_FREE_MB", str(min_mb)))
    except ValueError:
        pass
    try:
        max_wait_s = float(os.environ.get("ANIME_WAIT_MAX_S", str(max_wait_s)))
    except ValueError:
        pass
    try:
        max_cpu = float(os.environ.get("ANIME_MAX_CPU_PCT", "85"))
    except ValueError:
        max_cpu = 85.0

    if min_mb <= 0 and max_cpu <= 0:
        return
    waited = 0.0
    step = 5.0
    while waited < max_wait_s:
        free = _free_ram_mb()
        cpu = _cpu_load_pct() if max_cpu > 0 else None
        ram_ok = (min_mb <= 0) or (free is None) or (free >= min_mb)
        cpu_ok = (max_cpu <= 0) or (cpu is None) or (cpu <= max_cpu)
        if ram_ok and cpu_ok:
            return
        motivo = []
        if not ram_ok:
            motivo.append(f"RAM {free:.0f}MB < {min_mb:.0f}")
        if not cpu_ok:
            motivo.append(f"CPU {cpu:.0f}% > {max_cpu:.0f}")
        logging.info(f"[guarda] {' e '.join(motivo)} — outro app de vídeo ocupando "
                     f"recurso; esperando {step:.0f}s (aguardado {waited:.0f}/{max_wait_s:.0f}s)")
        _time.sleep(step)
        waited += step
    logging.warning(f"[guarda] recurso não liberou em {max_wait_s:.0f}s — seguindo assim mesmo "
                    f"(pode engasgar). Feche apps de vídeo em paralelo se falhar.")


def _clip_is_valid(path):
    """True se o mp4 existe e tem stream de vídeo com duração > 0 (não truncado)."""
    import os as _os
    if not (_os.path.exists(path) and _os.path.getsize(path) > 1024):
        return False
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=duration", "-of", "csv=p=0", path],
            capture_output=True, text=True, timeout=30)
        return float(r.stdout.strip()) > 0
    except Exception:
        return False