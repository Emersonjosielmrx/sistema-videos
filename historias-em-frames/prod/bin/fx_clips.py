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

import os
import word_pop
import advanced_parallax

# Filtros ffmpeg puros extraídos p/ fx_filters.py (2026-07-11). Re-exportados
# aqui pra fachada: quem faz `from fx_clips import *` continua enxergando tudo.
from fx_filters import (MOOD_PACING, DEFAULT_GAP, get_gap_for_mood,
                        build_glitch_filter, build_letterbox_filter,
                        build_rewind_filter, _build_pagetear_filter)
# Clips de branding/texto extraídos p/ fx_branding.py (2026-07-11). Re-exportados
# aqui pra fachada (story_pipeline importa build_intro_clip etc. de fx_clips).
from fx_branding import (build_intro_clip, build_outro_clip, build_cold_open,
                         build_narrative_transition, NARRATIVE_TRANSITIONS)


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

    # -- ADVANCED PARALLAX (feature exclusiva) — 2.5D depth por mood --
    # Substitui o movimento padrão por um zoom/pan cinematográfico guiado pela emoção.
    # Só usa os estilos "fragmento" (encadeáveis); dynamic_tilt tem labels próprios
    # e quebraria a chain [0:v]...[v], então cai no zoom_in seguro.
    if os.environ.get("ADVANCED_PARALLAX", "0") == "1":
        try:
            _pstyle = advanced_parallax.get_style_for_mood(mood or "neutral_chill")
            if _pstyle == "dynamic_tilt":
                _pstyle = "zoom_in"
            _pfrag = advanced_parallax.build_parallax_filter(_pstyle, duration, W, H)
            if _pfrag and "[" not in _pfrag:  # garante que é fragmento encadeável
                movement_filter = _pfrag
        except Exception:
            pass

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

    # -- WORD POP (feature exclusiva) — palavras de impacto saltam na tela --
    # Só quando WORD_POP=1 e a cena tem texto de narração com power-word.
    if os.environ.get("WORD_POP", "0") == "1" and narr_text:
        try:
            pops = word_pop.get_word_pop_filters([narr_text], [0.0])
            if pops and filter_complex.rstrip().endswith("[v]"):
                # injeta os drawtext antes do label final [v].
                # CRÍTICO: força fps={FPS} no fim — sem isto o drawtext deixa o
                # output cair pro default 25fps (o -loop 1 da imagem não fixa taxa),
                # gerando clips a 25fps que dessincronizam o xfade no concat (o
                # vídeo final colapsa: 8s de frames num container de 59s).
                idx = filter_complex.rstrip().rfind("[v]")
                filter_complex = filter_complex[:idx] + "," + pops + f",fps={FPS}[v]"
        except Exception as _e:
            pass

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
        "-pix_fmt", "yuv420p", "-r", str(FPS), "-t", f"{duration:.2f}",
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


def shake_clip(clip_in, clip_out, intensity=12, freq=12, decay_s=0.9):
    """Tremor de camera num clip JA renderizado (impacto no inicio, sumindo em decay_s).

    O render paralelo gera o clip por panel_effects/recorte/parallax e so depois
    decide o tremor; build_clip_with_shake gera a partir da IMAGEM, entao aqui o
    tremor e aplicado no video pronto: amplia `m` px e recorta com offset senoidal.
    Mesma resolucao de saida (vale para 720p e 1080p); audio copiado."""
    m = int(intensity) + 2
    decay = f"max(0,1-t/{max(decay_s, 0.2):.2f})"
    sx = f"{m}+{intensity}*sin(t*{freq})*{decay}"
    sy = f"{m}+{intensity}*cos(t*{freq}*1.3)*{decay}"
    vf = f"scale=iw+{2 * m}:ih+{2 * m},crop=iw-{2 * m}:ih-{2 * m}:{sx}:{sy},format=yuv420p"
    cmd = ["ffmpeg", "-y", "-i", str(clip_in), "-vf", vf,
           "-c:v", "libx264", "-preset", QP["preset"], "-crf", str(QP["crf"]), "-g", "30",
           "-c:a", "copy", str(clip_out)]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=120)
        return Path(clip_out).exists() and Path(clip_out).stat().st_size > 5000
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
        "-pix_fmt", "yuv420p", "-r", str(FPS), "-t", f"{duration:.2f}",
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


def build_meme_clip(out_path, mood="neutral_chill", duration=None, meme_video=None, sfx_file=None):
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
    if meme_video:
        # meme escolhido pelo catalogo (memes_catalogo.escolher): video, gif ou imagem
        meme_video = Path(meme_video)
        if not meme_video.exists():
            return False
    else:
        if not MEMES_VIDEO_DIR.exists():
            return False
        memes = list(MEMES_VIDEO_DIR.glob("*.mp4"))
        if not memes:
            return False
        meme_video = random.choice(memes)
    _memes_inseridos += 1
    # meme fora de 9:16: fundo desfocado do proprio meme (antes: faixas pretas)
    _FILL = (f"split=2[mbg][mfg];[mbg]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
             f"boxblur=24:2,eq=brightness=-0.15[mbgb];[mfg]scale={W}:{H}:force_original_aspect_ratio=decrease[mfgs];"
             f"[mbgb][mfgs]overlay=(W-w)/2:(H-h)/2")
    # imagem parada vira video (loop pela duracao); gif/mp4 entram direto
    _img_in = (["-loop", "1", "-t", f"{duration:.2f}"]
               if meme_video.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp", ".avif") else [])

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
            "ffmpeg", "-y", *_img_in, "-i", str(meme_video),
            "-t", f"{duration:.2f}",
            "-vf", f"{_FILL}",
            "-af", f"apad,atrim=0:{duration:.3f},asetpts=PTS-STARTPTS",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
            "-c:a", "aac", "-b:a", QP["audio_bitrate"], "-ar", "44100", "-ac", "2", "-pix_fmt", "yuv420p",
            str(out_path),
        ]
    else:
        # Meme sem áudio (imagem) — SFX que COMBINA com o mood da cena
        sfx = sfx_file or pick_sfx_by_mood(mood) or pick_sfx("transition")
        if sfx and Path(sfx).exists():
            cmd = [
                "ffmpeg", "-y",
                *_img_in, "-i", str(meme_video),
                "-i", str(sfx),
                "-t", f"{duration:.2f}",
                "-filter_complex",
                f"[0:v]{_FILL},"
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
                "ffmpeg", "-y", *_img_in, "-i", str(meme_video),
                "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=mono:d={duration}",
                "-vf", f"{_FILL},"
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
    # FFMPEG_THREADS limita threads do encoder/filtro. Cada thread do ffmpeg
    # pré-aloca buffers; com N inputs no xfade isso multiplica e estoura a RAM
    # quando outro processo pesado (outro render) já ocupa memória. 2 threads
    # cabe em ~6GB livres sem parar o outro job. 0 = deixa o ffmpeg decidir.
    _thr = os.environ.get("FFMPEG_THREADS", "2")
    cmd = ["ffmpeg", "-y"]
    if _thr and _thr != "0":
        cmd += ["-threads", _thr, "-filter_threads", _thr]
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
            "-movflags", "+faststart", "-pix_fmt", "yuv420p"]
    if _thr and _thr != "0":
        cmd += ["-threads", _thr]  # limita o encoder libx264 (output option)
    cmd += [out_path]
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
            f.write(f"file '{p}'\n")
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


def _ram_disponivel_gb():
    """RAM disponível em GB (available = livre + cache reclamável). Retorna None
    se não der pra medir (psutil ausente)."""
    try:
        import psutil
        return psutil.virtual_memory().available / (1024 ** 3)
    except Exception:
        return None


def _auto_xfade_batch():
    """Escolhe o tamanho do lote de xfade pela RAM disponível. Cada clip com
    parallax custa ~0.5GB de pico no filter_complex. Deixa ~1.5GB de folga pro
    resto do sistema. Também fixa FFMPEG_THREADS (se não setado) pra casar: menos
    RAM → menos threads (cada thread do ffmpeg pré-aloca buffer).
      sozinho (>10GB): lote 8, 4 threads
      apertado (4-10GB): lote 3-6, 2 threads
      crítico (<4GB): lote 3, 1 thread
    Assim roda folgado quando a máquina é nossa e cabe sem parar outro render."""
    ram = _ram_disponivel_gb()
    if ram is None:
        return 8  # sem psutil: usa o default seguro de sempre
    if ram >= 10:
        batch, thr = 8, "4"
    elif ram >= 6:
        batch, thr = 6, "2"
    elif ram >= 4:
        batch, thr = 4, "2"
    else:
        batch, thr = 3, "1"
    os.environ.setdefault("FFMPEG_THREADS", thr)
    print(f"  [auto-tune] RAM disponível {ram:.1f}GB -> xfade lote={batch} "
          f"ffmpeg_threads={os.environ.get('FFMPEG_THREADS')}", flush=True)
    return batch


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
        # Pacing dinamico: ajusta gap base pelo mood da cena
        mood_gap = gap_base
        if gap_dyn and descriptions and i < len(descriptions):
            from fx_detect import detect_mood_from_text
            clip_mood = detect_mood_from_text(descriptions[i] if descriptions[i] else "")
            mood_gap = max(get_gap_for_mood(clip_mood), gap_base * 0.5)
            mood_gap = min(mood_gap, gap_cap)
        g = mood_gap if gap_dyn else gap_base
        if gap_dyn and i + 1 < n:
            sfx_next = sfx_durs[i + 1] if i + 1 < len(sfx_durs) else 0.0
            if sfx_next > g:
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
    # Default 8 (não 16): com PARALLAX ligado os clips são pesados de decodificar
    # e 16 numa passada só estoura a RAM (ffmpeg -12 "Cannot allocate memory") →
    # caía no fallback de corte seco, perdendo as transições xfade. 8 cabe.
    # AUTO-TUNE por RAM disponível: se XFADE_BATCH não for setado à mão, mede a
    # memória livre e escolhe o lote sozinho — roda folgado quando a máquina está
    # só nossa, e cabe apertado quando outro render pesado compete (sem parar o
    # outro). Cada clip com parallax custa ~0.5GB de pico no xfade.
    _env_batch = os.environ.get("XFADE_BATCH")
    if _env_batch:
        try:
            max_batch = max(3, int(_env_batch))
        except ValueError:
            max_batch = 8
    else:
        max_batch = _auto_xfade_batch()

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
            f.write(f"file '{c}'\n")

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

