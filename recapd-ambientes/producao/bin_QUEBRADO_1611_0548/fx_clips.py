# -*- coding: utf-8 -*-
"""fx_clips.py — MONTAGEM DOS CLIPS (ffmpeg). O coração do render.
build_clip*, intro/outro, memes/transições, concat_with_xfade/transitions, upscale_to_fullhd.

Parte do motor de efeitos — mapa completo na fachada effects_engine.py.
Split mecânico verbatim do _PRE_SPLIT_effects_engine.py.bak (2026-07-04).
"""
import hashlib
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
        # loudnorm nivela cada SFX a um volume parelho e audível — resolve os
        # arquivos quase mudos (new_transition_1 -77dB, swoosh_light -68dB) que
        # sumiam no mix. Aplicado ANTES do volume/trim. SFX_LOUDNORM=0 desliga.
        norm = ("loudnorm=I=-16:TP=-1.5,"
                if os.environ.get("SFX_LOUDNORM", "1") != "0" else "")
        audio_mix_filter = (
            f";[{sfx_idx}:a]{norm}volume={sfx_vol},atrim=0:{play:.2f},apad=whole_dur={play:.2f}[sfx_temp];"
            f"[{orig_audio_map}][sfx_temp]amix=inputs=2:duration=first:dropout_transition=0.3[aout]"
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
        m.update(str(color_filter if hasattr(effects_mgr, 'pick_color') else "").encode('utf-8'))
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
        m.update(str(color_filter if hasattr(effects_mgr, 'pick_color') else "").encode('utf-8'))
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
        pool = ["coverleft", "coverright", "coverup", "hrwind", "vuwind",
                "hrslice", "vuslice", "zoomin", "squeezev", "slideleft",
                "slideright", "wipeleft", "diagtr"]
        d = 0.22
    elif tension:                    # tensão: desfaz/rasga em tiras / revela
        pool = ["dissolve", "hlslice", "vdslice", "hlwind", "vdwind", "pixelize",
                "radial", "distance", "fadeblack", "revealdown", "diagbl"]
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
        vparts.append(f"[{i}:v]format=yuv420p,fps={FPS},scale={W}:{H},setsar=1{vtail},"
                      f"settb=AVTB,setpts=PTS-STARTPTS[v{i}]")
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
    for k in range(1, m):
        v_out, a_out = f"vx{k}", f"ax{k}"
        soft = is_speech[k] and is_speech[k - 1]
        if soft:
            desc = descriptions[k] if k < len(descriptions) else ""
            trans, d = _pick_xfade(desc, supported, last_trans)
            last_trans = trans
            d = max(0.10, min(d, durs_eff[k] * 0.5, acc * 0.5))
            offset = max(0.0, acc - d)
            chain.append(f"[{v_cur}][v{k}]xfade=transition={trans}:"
                         f"duration={d:.3f}:offset={offset:.3f}[{v_out}]")
            chain.append(f"[{a_cur}][a{k}]acrossfade=d={d:.3f}[{a_out}]")
            starts.append(acc - d)  # o clip k começa onde o xfade inicia
            acc = acc + durs_eff[k] - d
        else:
            chain.append(f"[{v_cur}][v{k}]concat=n=2:v=1:a=0[{v_out}]")
            chain.append(f"[{a_cur}][a{k}]concat=n=2:v=0:a=1[{a_out}]")
            last_trans = None
            starts.append(acc)  # corte seco: começa exatamente no fim do anterior
            acc = acc + durs_eff[k]
        v_cur, a_cur = v_out, a_out

    _LAST_SEG_STARTS = starts
    _LAST_SEG_TOTAL = acc

    filter_complex = ";".join(vparts + aparts + chain)
    cmd += ["-filter_complex", filter_complex,
            "-map", f"[{v_cur}]", "-map", f"[{a_cur}]",
            "-c:v", "libx264", "-preset", QP["preset"], "-crf", str(QP["crf"]),
            "-c:a", "aac", "-b:a", QP["audio_bitrate"], "-ar", "44100", "-ac", "2",
            "-movflags", "+faststart", "-pix_fmt", "yuv420p", out_path]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=900)
        return Path(out_path).exists() and Path(out_path).stat().st_size > 1000
    except (subprocess.CalledProcessError, Exception) as e:
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
    try:
        subprocess.run(base + ["-c", "copy", "-movflags", "+faststart", str(out_path)],
                       check=True, capture_output=True, timeout=180)
        return Path(out_path).exists()
    except Exception:
        try:
            subprocess.run(base + ["-c:v", "libx264", "-preset", QP["preset"],
                           "-crf", str(QP["crf"]), "-c:a", "aac",
                           "-b:a", QP["audio_bitrate"], "-ar", "44100", "-ac", "2",
                           "-movflags", "+faststart", "-pix_fmt", "yuv420p", str(out_path)],
                           check=True, capture_output=True, timeout=600)
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
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=120)
    except (subprocess.CalledProcessError, Exception):
        cmd_reenc = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file),
            "-c:v", "libx264", "-preset", QP["preset"], "-crf", str(QP["crf"]),
            "-c:a", "aac", "-b:a", QP["audio_bitrate"], "-ar", "44100", "-ac", "2",
            "-movflags", "+faststart", "-pix_fmt", "yuv420p",
            str(out_path),
        ]
        subprocess.run(cmd_reenc, check=True, capture_output=True, timeout=300)

    try:
        list_file.unlink()
    except Exception:
        pass

    return Path(out_path).exists() and Path(out_path).stat().st_size > 1000


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
        m.update(str(color_filter if hasattr(effects_mgr, 'pick_color') else "").encode('utf-8'))
        m.update("V1_ANIMATED".encode('utf-8'))
        
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



def build_clip_from_video(video_source, audio_path, out_path, panel_idx, effects_mgr, duration=None,
                          global_start_t=0.0,
                          has_name_tags=False, current_tag=None, next_tag=None,
                          name_tags_dict=None, character_roles=None, is_dialog=False,
                          subtitles=None, bgm=None, sfx=None,
                          clip_duration=None,   # duracao do clipe no timeline original (usado no clip recortado)
                          add_karaoke=False, add_watermark=True):
    '''
    Constrói um clipe animado tirando uma fatia de um arquivo de vídeo original.
    Serve para descaracterizar animes removendo o copyright e criando blocos.
    O vídeo é cortado usando -ss e -t, e depois é aplicado o filtro de descaracterização (hflip, eq, crop).
    '''
    import os
    import subprocess
    import logging
    from effects_engine import W_FINAL, H_FINAL, FPS
    from fx_subtitles import _FONT_CANDIDATES_FALLBACK
    from fx_foley import enhance_narration_audio
    
    if clip_duration is None:
        if duration is not None:
             clip_duration = duration
        else:
             clip_duration = 3.0 # fallback default
             
    # Tempo inicial do corte no arquivo de video
    cut_start = global_start_t

    # Filtro descaracterizador mestre
    # Inverte horizontamente, corta 5% nas bordas (zoom in de 10%), satura 10%
    descaracterizador = "hflip,crop=in_w*0.90:in_h*0.90:in_w*0.05:in_h*0.05,eq=saturation=1.1:brightness=0.03"

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
    _out = "[pre]" if hardsub_cover else "[vout]"

    if orient == "vertical":
        short_source = os.environ.get("ANIME_SHORT_SOURCE", "reframe").strip().lower()
        if short_source == "native":
            # Native vertical source: scale directly to fill the frame (1280x720 sideways context)
            # We use force_original_aspect_ratio=decrease and pad just in case it's not EXACTLY 9:16
            scale_filter = (f"scale={out_w}:{out_h}:force_original_aspect_ratio=decrease,"
                            f"pad={out_w}:{out_h}:(ow-iw)/2:(oh-ih)/2:color=black")
            vf_mestre = f"[0:v]{descaracterizador},{scale_filter}{_out}"
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
        vf_mestre = f"[0:v]{descaracterizador},{scale_filter}{_out}"

    if hardsub_cover:
        # Faixa fosca (blur pesado + leve clareada/dessaturada) cobrindo a legenda
        # velha queimada na fonte. Ela pode estar no RODAPÉ *ou* no TOPO (ex: título
        # do canal-fonte), então cobrimos AMBAS as faixas. A nossa legenda PT entra
        # por cima depois. band_h = altura de cada faixa (fração da altura total).
        band_y = round(1.0 - band_h, 4)
        vf_mestre += (
            f";[pre]split=3[cvbase][cvtop][cvbot];"
            f"[cvtop]crop=iw:ih*{band_h}:0:0,boxblur=24:3,"
            f"eq=brightness=0.10:saturation=0.55[cvtblur];"
            f"[cvbot]crop=iw:ih*{band_h}:0:ih*{band_y},boxblur=24:3,"
            f"eq=brightness=0.10:saturation=0.55[cvbblur];"
            f"[cvbase][cvtblur]overlay=0:0[cvmid];"
            f"[cvmid][cvbblur]overlay=0:H*{band_y}[vout]"
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
        "-t", str(clip_duration),
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

    logging.info(f"[build_clip_from_video] clipe {panel_idx} ({orient}) Start={cut_start:.2f}s Dur={clip_duration:.2f}s")

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
            subprocess.run(cmd_try, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError as e:
            logging.warning(f"[build_clip_from_video] clipe {panel_idx} falhou (tentativa {attempt+1}/3, rc={e.returncode})")
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