# -*- coding: utf-8 -*-
"""fx_clips.py — MONTAGEM DOS CLIPS de vídeo (ffmpeg). O coração do render.

Parte do motor de efeitos (ver mapa completo em effects_engine.py).
Este é o arquivo MAIOR: pega imagem + áudio e produz cada clip .mp4, depois
concatena tudo. É aqui que o ffmpeg roda de verdade.

  build_clip(img, audio, out, ...)      clip padrão (Ken Burns + cor + overlay).
  build_clip_with_shake(...)            variante com camera shake (impacto/tensão).
  build_flash_clip(...)                 clip curto de painel sem narração.
  build_clip_animated(...)              variante animada.
  build_intro_clip / build_outro_clip   abertura (título) e CTA final.
  concat_with_transitions(clips, out)   junta os clips com xfade.
  upscale_to_fullhd(v_in, v_out)        720p -> 1080x1920 no fim (lanczos).
  apply_effects_to_cmd(...)             injeta filtros no comando ffmpeg.
  build_glitch/letterbox/rewind/_pagetear_filter   filtros procedurais.
  _append_overlay / _append_luma_transition        overlays por cima do clip.

Importa: fx_assets (W,H,FPS,TRANSITION_DURATION) e fx_subtitles (fontes).
Mexa aqui pra: como o clip é montado, ordem de filtros, concat, upscale.
"""
import random
import shutil
import subprocess
import os
import re
from pathlib import Path
from fx_assets import W, H, FPS, TRANSITION_DURATION, PAN_PX_POR_QUADRO
from fx_subtitles import _load_font, _wrap_lines

# Resolução final de entrega (upscale no fim do pipeline). Render roda em W×H (720p).
W_FINAL, H_FINAL = 1080, 1920
# Qualidade dos clips intermediários. Com o acabamento só há mais 1 encode depois
# (passe final), então dá pra gastar um pouco mais aqui (era 23).
CLIP_CRF = os.environ.get("HIPER_CLIP_CRF", "20")


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

        sfx_vol = "0.7" if transition_type == "flash" or "impact" in str(sfx_file) else "0.45"
        # SFX com cauda de 1s e fade (antes: corte seco em 0.35s). amix sem normalize:
        # o normalize padrão dividia a VOZ pela metade em todo clip com SFX.
        audio_mix_filter = (
            f";[{sfx_idx}:a]volume={sfx_vol},atrim=0:1.0,afade=t=out:st=0.7:d=0.3[sfx_temp];"
            f"[{orig_audio_map}][sfx_temp]amix=inputs=2:duration=first:dropout_transition=0.3:normalize=0[aout]"
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
        "flash":     "fade=t=in:st=0:d=0.12:color=white",
        "flashred":  "fade=t=in:st=0:d=0.14:color=0xCC1111",
        "flashgold": "fade=t=in:st=0:d=0.16:color=0xE8B500",
        "flashblue": "fade=t=in:st=0:d=0.16:color=0x2244CC",
        "fade":      "fade=t=in:st=0:d=0.22:color=black",
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


def build_intro_clip(titulo, first_panel, out_path, duration=1.8, sfx_file=None):
    """Gera um clip de abertura: 1º painel borrado/escuro + título + zoom lento."""
    from PIL import Image, ImageFilter, ImageEnhance
    tmp = Path(str(out_path) + "_introbg.jpg")
    try:
        img = Image.open(first_panel).convert("RGB")
        sw, sh = W / img.width, H / img.height
        sc = max(sw, sh)
        img = img.resize((int(img.width * sc), int(img.height * sc)), Image.LANCZOS)
        left = (img.width - W) // 2; top = (img.height - H) // 2
        img = img.crop((left, top, left + W, top + H))
        img = img.filter(ImageFilter.GaussianBlur(6))
        img = ImageEnhance.Brightness(img).enhance(0.72)
        img.save(tmp, quality=85)
    except Exception:
        Image.new("RGB", (W, H), (10, 12, 24)).save(tmp)
    txt_png = Path(str(out_path) + "_introtxt.png")
    _text_block_png(txt_png, [(titulo, 96, (255, 255, 255))], y_center_frac=0.46)

    frames = int(duration * FPS)
    zoom = f"zoompan=z='min(zoom+0.0015,1.12)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={FPS}"
    audio_in = ["-i", str(sfx_file)] if sfx_file and Path(sfx_file).exists() else \
               ["-f", "lavfi", "-t", f"{duration:.2f}", "-i", "anullsrc=r=44100:cl=stereo"]
    fc = (f"[0:v]{zoom},format=yuv420p[bg];"
          f"[bg][1:v]overlay=0:0:format=auto,"
          f"fade=t=in:st=0:d=0.2:color=black,fade=t=out:st={duration-0.2:.2f}:d=0.2[v];"
          f"[2:a]apad=whole_dur={duration:.2f},atrim=0:{duration:.2f}[a]")
    cmd = ["ffmpeg", "-y",
           "-loop", "1", "-t", f"{duration:.2f}", "-i", str(tmp),
           "-i", str(txt_png), *audio_in,
           "-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-t", f"{duration:.2f}",
           "-c:v", "libx264", "-preset", "fast", "-crf", CLIP_CRF, "-g", "30",
           "-c:a", "aac", "-b:a", "192k", "-pix_fmt", "yuv420p", str(out_path)]
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
               ["-f", "lavfi", "-t", f"{duration:.2f}", "-i", "anullsrc=r=44100:cl=stereo"]
    fc = (f"color=c=0x0a0e1a:s={W}x{H}:d={duration:.2f}:r={FPS}[bg0];"
          f"[bg0]{pulse}[bg];"
          f"[bg][0:v]overlay=0:0,fade=t=in:st=0:d=0.2:color=black[v];"
          f"[1:a]apad=whole_dur={duration:.2f},atrim=0:{duration:.2f}[a]")
    cmd = ["ffmpeg", "-y", "-loop", "1", "-t", f"{duration:.2f}", "-i", str(txt_png),
           *audio_in,
           "-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-t", f"{duration:.2f}",
           "-c:v", "libx264", "-preset", "fast", "-crf", CLIP_CRF, "-g", "30",
           "-c:a", "aac", "-b:a", "192k", "-pix_fmt", "yuv420p", str(out_path)]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=90)
        ok = True
    except Exception:
        ok = False
    try: txt_png.unlink()
    except Exception: pass
    return ok


def _append_overlay(filter_complex, overlay_video, input_idx=2, opacity=0.55):
    """Anexa um blend de overlay atmosférico (clip inteiro) ao filter_complex.

    Blenda em RGB (gbrp) com modo screen: fundo preto do overlay = base intacta,
    e a partícula (pétala/fagulha) mantém a cor original. Troca o [v] final.
    Retorna (novo_filter_complex, args_input). Overlay entra como input_idx (loop).
    """
    if not overlay_video or not Path(overlay_video).exists():
        return filter_complex, []
    if not filter_complex.endswith("[v]"):
        return filter_complex, []
    base = filter_complex[:-3] + "[vbase]"
    base += (
        f";[vbase]format=gbrp[vb]"
        f";[{input_idx}:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
        f"crop={W}:{H},setsar=1,format=gbrp[ovl];"
        f"[vb][ovl]blend=all_mode=screen:all_opacity={opacity},format=yuv420p[v]"
    )
    return base, ["-stream_loop", "-1", "-i", str(overlay_video)]


def _append_luma_transition(filter_complex, luma_video, input_idx, duration):
    """Anexa um vídeo de luma (fumaça/fogo) SÓ no início do clip — o evento no corte.

    O luma toca uma vez em t=0 e some. Padding preto na cauda (tpad) torna o resto
    invisível sob o blend screen (sem congelar o último frame). Não usa loop.
    Troca o [v] final. Retorna (novo_filter_complex, args_input).
    """
    if not luma_video or not Path(luma_video).exists():
        return filter_complex, []
    if not filter_complex.endswith("[v]"):
        return filter_complex, []
    base = filter_complex[:-3] + "[vprev]"
    base += (
        f";[{input_idx}:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
        f"crop={W}:{H},setsar=1,"
        f"tpad=stop_mode=add:stop_duration={duration:.2f}:color=black,format=gbrp[ltr]"
        f";[vprev]format=gbrp[vp];"
        f"[vp][ltr]blend=all_mode=screen:all_opacity=1.0,format=yuv420p[v]"
    )
    return base, ["-i", str(luma_video)]


# ══════════════════════════════════════════════════════════════════════════
# ENQUADRAMENTO 9:16 SEM DEFORMAR (16/10)
# ══════════════════════════════════════════════════════════════════════════
# O zoompan do ffmpeg recorta uma janela iw/zoom x ih/zoom — SEMPRE na proporção do
# painel — e espreme essa janela no s=720x1280. Painel que não é 9:16 saía deformado:
#   cap 10 panel_003 (720x2320): quadrado medido 0,55 de altura/largura -> 1,83x
#     achatado; o 푸확 vermelho ficava gordo e baixo (no painel ele é alto e fino);
#   cap 10 panel_058 (720x1087): 1,14 -> 14% esticado, o balão redondo virava ovo em pé;
#   painel 1,31:1: 1,36 -> 36% esticado.
# Era ~30-40 clips por capítulo (os que não pegam 2.5D), incluindo impacto/tensão e os
# rápidos — por isso o vídeo alternava rosto certo (caminho OpenCV do fx_parallax, que
# escala uniforme) e rosto achatado.
# Agora: painel ALTO escala pela LARGURA e passeia por crop (uniforme, tela cheia);
# o resto vai pro zoompan numa CAIXA com a proporção do painel e é composto sobre o
# fundo borrado do próprio painel (como o fx_parallax faz), nunca sobre barra chapada.


def _caixa_proporcional(pw, ph, w=W, h=H):
    """Maior caixa COM A PROPORÇÃO DO PAINEL que cabe no canvas (lados pares p/ libx264)."""
    if ph * w >= pw * h:        # painel mais "alto" que o canvas -> encosta em cima/embaixo
        bh, bw = h, int(round(h * pw / ph))
    else:                       # mais largo -> encosta nas laterais
        bw, bh = w, int(round(w * ph / pw))
    return max(2, (bw // 2) * 2), max(2, (bh // 2) * 2)


def _fundo_borrado(w=W, h=H):
    """Fundo de tela: o PRÓPRIO painel cobrindo o canvas, borrado e escuro.

    É o que o fx_parallax faz (fx_parallax.py ~531: cover + GaussianBlur 22 + 0,42 de
    brilho) e o que o docstring do build_clip sempre prometeu — o painel largo saía com
    barra chapada 0x0a0f1c (quadro p72, a cidade ao pôr do sol: faixa parada no meio da
    tela com 360 px de azul-escuro em cima e embaixo).
    O desfoque é feito em 1/8 da resolução e devolvido com scale: num i5 sem GPU um
    gblur a 720x1280 em 150 quadros não cabe no orçamento de render.
    """
    return (f"scale={w // 8}:{h // 8}:force_original_aspect_ratio=increase,"
            f"crop={w // 8}:{h // 8},gblur=sigma=6,eq=brightness=-0.28:saturation=0.75,"
            f"scale={w}:{h},setsar=1")


def _pan_vertical(mov, duration, pw, ph, w=W, h=H):
    """Painel ALTO: escala pela largura (uniforme) e passeia a janela por CROP.

    Mantém a variedade do catálogo sem o zoompan: a velocidade vem do "speed" do
    movimento sorteado (PAN_PX_POR_QUADRO) e o sentido do nome ("Rev" = sobe).
    Segura 1 s no começo, igual aos filtros de MOVEMENTS_VERTICAL (em clip curto a
    espera encolhe, senão o clip rápido de 0,8 s ficaria parado).
    Se a velocidade da classe não vencer o painel dentro do clip, acelera só o
    necessário (teto de 7 px/quadro): sem isso o panel_003 (2320 px de altura, 1040 de
    percurso) acabaria o clip na metade do painel e o fim da arte nunca apareceria.
    """
    nome = mov.get("name", "") if isinstance(mov, dict) else ""
    classe = mov.get("speed") if isinstance(mov, dict) else None
    px = PAN_PX_POR_QUADRO.get(classe, PAN_PX_POR_QUADRO["slow"])
    espera = min(1.0, max(0.0, duration * 0.25))
    util = max(0.5, duration - espera)
    percurso = max(0, round(ph * (w / pw)) - h)
    # Acelera só o necessário pra não parar no meio da arte, mas NO MÁXIMO o dobro da classe
    # sorteada: sem esse teto o piso vencia sempre e os 4 ritmos do catálogo viravam um só
    # (medido no cap 1: 74 painéis de 109 andando no teto, 2,5 a 3,6 vezes mais rápido que a
    # classe pedia). Painel muito longo volta a terminar antes do fim — é o preço de ler.
    px = max(px, min(7.0, px * 2.0, percurso / (util * FPS)))
    v = px * FPS  # px por segundo na tela
    anda = f"min(ih-oh,max(0,(t-{espera:.2f})*{v:.0f}))"
    y = f"(ih-oh)-{anda}" if "Rev" in nome else anda
    return f"scale={w}:-2,crop={w}:{h}:0:'{y}'"


def _enquadrar(pw, ph, movement_filter, mov=None, duration=4.0, w=W, h=H):
    """Leva o painel pro canvas w x h SEM DEFORMAR.

    Devolve (cadeia, precisa_fundo):
      precisa_fundo=False -> a cadeia já entrega o canvas cheio (painel alto, pan);
      precisa_fundo=True  -> a cadeia entrega o painel numa caixa proporcional e quem
                             chama compõe sobre o _fundo_borrado com overlay centralizado.
    """
    if ph / pw > 2.0:
        return _pan_vertical(mov, duration, pw, ph, w, h), False
    # Proporção PERTO da do canvas: preenche a tela cortando o que sobra (o que o vídeo sempre
    # fez). Encaixar a caixa proporcional nessa faixa deixa o painel pequeno no meio, com
    # moldura borrada dos quatro lados — foi o que saiu no cap 1 refeito em 16/10 (aos 95 s).
    # Cortar aqui tira no máximo ~11% de um lado. O fundo borrado continua valendo pro painel
    # de proporção bem diferente, onde cortar comeria metade da arte.
    if abs((ph / pw) / (h / w) - 1.0) <= 0.25:
        return f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},setsar=1", False
    bw, bh = _caixa_proporcional(pw, ph, w, h)
    alvo = f"s={W}x{H}"
    if alvo in movement_filter:
        # o zoompan continua o mesmo; só o destino deixa de ser o canvas e passa a ser a
        # caixa com a proporção do painel — aí a janela do zoompan vai inteira, sem esticar
        return movement_filter.replace(alvo, f"s={bw}x{bh}"), True
    return f"scale={bw}:{bh}", True   # movimento de fora do catálogo: ao menos não deforma


def _compor(fg_chain, com_fundo, pos_filtros, w=W, h=H):
    """Monta o filter_complex final: painel (fg) sobre o fundo borrado, ou direto.

    pos_filtros = o que vem DEPOIS do enquadramento (cor, vinheta, shake, flash...).
    """
    pos = "," + ",".join(pos_filtros) if pos_filtros else ""
    if com_fundo:
        return (f"[0:v]split[bgsrc][fgsrc];"
                f"[bgsrc]{_fundo_borrado(w, h)}[bg];"
                f"[fgsrc]{fg_chain}[fg];"
                f"[bg][fg]overlay=(W-w)/2:(H-h)/2{pos}[v]")
    return f"[0:v]{fg_chain}{pos}[v]"


def build_clip(img_path, audio_path, out_path, panel_idx, effects_mgr, duration=None,
               transition_type=None, sfx_file=None, overlay_video=None,
               luma_transition=None):
    """Cria clip de um painel com efeitos visuais completos.

    Aplica: background blur + movimento (pan/zoom) + filtro de cor + vinheta.
    O background blur usa uma versão borrada e escurecida da própria imagem
    como fundo, em vez de bordas pretas — muito mais profissional.
    (Até 15/10 isso só valia no papel: o painel largo saía com barra chapada
    0x0a0f1c e parado. Agora quem decide o enquadramento é o _enquadrar.)

    Camadas (todas embutidas numa única passada, pois o concat final usa -c copy):
      - overlay_video: partícula atmosférica POR CIMA do clip inteiro (input 2, loop)
      - luma_transition: vídeo de fumaça/fogo NO corte (~1s, input dinâmico, sem loop)
      - transition_type/sfx_file: corte procedural + SFX (via apply_effects_to_cmd)
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

    # Escolher movimento baseado nas dimensões
    movement = effects_mgr.pick_movement(ph, pw)
    movement_filter = movement["filter"].format(frames=frames) if isinstance(movement, dict) else movement.format(frames=frames)

    # Escolher cor
    color = effects_mgr.pick_color()
    color_filter = color["filter"] if isinstance(color, dict) else color

    # Vinheta (opcional)
    vignette = effects_mgr.pick_vignette()
    vignette_filter = vignette if isinstance(vignette, str) else (vignette["filter"] if isinstance(vignette, dict) else None)

    # Enquadramento 9:16 sem deformar (ver _enquadrar): painel alto vira pan por crop;
    # o resto vai pro zoompan na caixa proporcional, sobre o fundo borrado do painel.
    fg_chain, com_fundo = _enquadrar(pw, ph, movement_filter, movement, duration)
    pos = [color_filter] + ([vignette_filter] if vignette_filter else []) + ["format=yuv420p"]
    filter_complex = _compor(fg_chain, com_fundo, pos)

    # Overlay atmosférico (chuva/neve/faíscas/pétalas) entra como input 2 (loop)
    filter_complex, overlay_input = _append_overlay(filter_complex, overlay_video)

    # Luma de transição (fumaça/fogo no corte) entra logo após o overlay (sem loop).
    # Índice dinâmico: img=0, audio=1, overlay=2 (se houver) -> luma = 2 ou 3.
    luma_idx = 2 + (1 if overlay_input else 0)
    filter_complex, luma_input = _append_luma_transition(
        filter_complex, luma_transition, luma_idx, duration)

    # Clip base (movimento + cor + vinheta + overlay + luma). Transição/SFX embutidos
    # na MESMA chamada (single-pass) via apply_effects_to_cmd — sem re-encode extra.
    cmd = [
        "ffmpeg", "-y",
        "-r", str(FPS), "-loop", "1", "-t", f"{duration:.2f}", "-i", str(img_path),
        "-i", str(audio_path),
        *overlay_input,
        *luma_input,
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "1:a",
        "-c:v", "libx264", "-preset", "fast", "-crf", CLIP_CRF, "-g", "30",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p", "-t", f"{duration:.2f}",
        str(out_path),
    ]

    try:
        cmd = apply_effects_to_cmd(cmd, transition_type, sfx_file, duration)
        subprocess.run(cmd, check=True, capture_output=True, timeout=180)
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        # Fallback: escala simples com padding escuro
        minimal = f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=0x0a0f1c,{color_filter},format=yuv420p"
        cmd_simple = [
            "ffmpeg", "-y",
            "-r", str(FPS), "-loop", "1", "-t", f"{duration:.2f}", "-i", str(img_path),
            "-i", str(audio_path),
            "-filter_complex", f"[0:v]{minimal}[v]",
            "-map", "[v]", "-map", "1:a",
            "-c:v", "libx264", "-preset", "fast", "-crf", CLIP_CRF, "-g", "30",
            "-c:a", "aac", "-b:a", "192k",
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
                          transition_type=None, sfx_file=None, overlay_video=None,
                          luma_transition=None, shake_dur=None):
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

    # Escolher movimento, cor, vinheta (como build_clip normal)
    movement = effects_mgr.pick_movement(ph, pw)
    movement_filter = movement["filter"].format(frames=frames) if isinstance(movement, dict) else movement.format(frames=frames)
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
    # decay = max(0, 1 - on/(frames*0.6))  -> shake dura 60% do clip
    # shake_dur: tremor só nesse começo (painel com balão: um tranco curto, depois dá pra ler)
    dur_tremor = min(duration * 0.6, shake_dur) if shake_dur else duration * 0.6
    shake_x = f"{margin}+{shake_intensity}*sin(t*{shake_freq})*max(0,1-t/({dur_tremor:.2f}))"
    shake_y = f"{margin}+{shake_intensity}*cos(t*{shake_freq}*1.3)*max(0,1-t/({dur_tremor:.2f}))"
    shake_crop = f"crop={W}:{H}:'{shake_x}':'{shake_y}'"

    # Mesmo enquadramento sem deformação do build_clip, só que mirando o canvas MAIOR
    # (shake_w x shake_h) — o shake_crop depois recorta o canvas de verdade com o tremor.
    fg_chain, com_fundo = _enquadrar(pw, ph, movement_filter, movement, duration,
                                     shake_w, shake_h)
    pos = [shake_crop, color_filter] + ([vignette_filter] if vignette_filter else []) + \
          ["format=yuv420p"]
    filter_complex = _compor(fg_chain, com_fundo, pos, shake_w, shake_h)
    filter_complex, overlay_input = _append_overlay(filter_complex, overlay_video)
    luma_idx = 2 + (1 if overlay_input else 0)
    filter_complex, luma_input = _append_luma_transition(
        filter_complex, luma_transition, luma_idx, duration)

    cmd = [
        "ffmpeg", "-y",
        "-r", str(FPS), "-loop", "1", "-t", f"{duration:.2f}", "-i", str(img_path),
        "-i", str(audio_path),
        *overlay_input,
        *luma_input,
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "1:a",
        "-c:v", "libx264", "-preset", "fast", "-crf", CLIP_CRF, "-g", "30",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p", "-t", f"{duration:.2f}",
        str(out_path),
    ]

    try:
        cmd = apply_effects_to_cmd(cmd, transition_type, sfx_file, duration)
        subprocess.run(cmd, check=True, capture_output=True, timeout=180)
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        # Fallback: build_clip sem shake (mantém transição/SFX + overlay + luma)
        return build_clip(img_path, audio_path, out_path, panel_idx, effects_mgr,
                          duration, transition_type, sfx_file, overlay_video,
                          luma_transition)


def build_flash_clip(img_path, out_path, clip_idx, effects_mgr, duration=0.8,
                     transition_type=None, sfx_file=None):
    """Cria clip rápido (sem áudio) com flash branco no final.

    Pra painéis sem narração — passam rápido e dão ritmo ao vídeo.
    """
    from PIL import Image
    img = Image.open(img_path)
    pw, ph = img.size
    frames = int(duration * FPS)

    # Zoom rápido (mais agressivo que o normal pra dar sensação de velocidade)
    zoom_filter = f"zoompan=z='min(zoom+0.002,1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={FPS}"

    # Flash branco no final (últimos 5 frames = fade to white)
    flash = f"fade=t=out:st={max(0, duration-0.15):.2f}:d=0.15:color=white"

    # Mesmo enquadramento sem deformação dos outros clips (o painel alto perde o zoom e
    # ganha um pan curto — o zoompan em cima do crop não anima, ver _pan_vertical).
    fg_chain, com_fundo = _enquadrar(pw, ph, zoom_filter, None, duration)
    filter_complex = _compor(fg_chain, com_fundo, [flash, "format=yuv420p"])

    # Gerar áudio silencioso inline
    cmd = [
        "ffmpeg", "-y",
        "-r", str(FPS), "-loop", "1", "-t", f"{duration:.2f}", "-i", str(img_path),
        "-f", "lavfi", "-t", f"{duration:.2f}", "-i", "anullsrc=r=44100:cl=stereo",
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "1:a",
        "-c:v", "libx264", "-preset", "fast", "-crf", CLIP_CRF, "-g", "30",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p", "-t", f"{duration:.2f}",
        str(out_path),
    ]
    try:
        cmd = apply_effects_to_cmd(cmd, transition_type, sfx_file, duration)
        subprocess.run(cmd, check=True, capture_output=True, timeout=30)
        return True
    except Exception:
        return False


def _igualar_audio(clips, tmp_dir):
    """O concat com `-c copy` exige o MESMO formato de áudio em todos os clips: um clip com taxa/canais
    diferentes (ex.: abertura 44.1k estéreo no meio de falas 24k mono) embaralha os tempos e o
    vídeo final sai com o áudio quebrado. Refaz só o áudio dos diferentes no formato da maioria."""
    from collections import Counter
    fmts = []
    for c in clips:
        r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries",
                            "stream=sample_rate,channels", "-of", "csv=p=0", str(c)],
                           capture_output=True, text=True, timeout=15)
        fmts.append(r.stdout.strip())
    alvo = Counter(f for f in fmts if f).most_common(1)
    if not alvo:
        return clips
    sr, ch = alvo[0][0].split(",")[:2]
    out = []
    for k, (c, f) in enumerate(zip(clips, fmts)):
        if f == alvo[0][0]:
            out.append(c)
            continue
        novo = Path(tmp_dir) / f"_aud_{k:03d}_{Path(c).name}"
        entrada = ["-i", str(c)] if f else ["-i", str(c), "-f", "lavfi", "-i", f"anullsrc=r={sr}:cl=mono"]
        # apad: sem ele o -shortest cortava o clip curto (vídeo 1,5 s, fala 0,8-1,1 s) no fim da fala e o
        # acabamento.fronteiras (medido nos clips originais) ficava até 3,5 s adiantado no fim (16/10, cap 1)
        mapa = ["-map", "0:v", "-map", "0:a" if f else "1:a", "-af", "apad", "-shortest"]
        try:
            subprocess.run(["ffmpeg", "-y", "-v", "error", *entrada, *mapa, "-c:v", "copy", "-c:a", "aac",
                            "-b:a", "192k", "-ar", sr, "-ac", ch, str(novo)],
                           check=True, capture_output=True, timeout=120)
            out.append(novo)
        except Exception:  # noqa: BLE001
            out.append(c)
    return out


def concat_with_transitions(clips, out_path, transition_dur=TRANSITION_DURATION,
                            descriptions=None):
    """Concatena os clips finais (apenas concat — SEM re-encode).

    As transições (fade/flash/glitch) e os SFX já vêm EMBUTIDOS em cada clip,
    aplicados numa única passada de FFmpeg no build_clip (via apply_effects_to_cmd).
    Aqui só juntamos os arquivos com `-c copy` -> zero re-compressão, sem perda de
    qualidade. Se o copy falhar (params divergentes), faz re-encode como fallback.
    """
    if len(clips) < 2:
        if clips:
            shutil.copy2(str(clips[0]), str(out_path))
        return bool(clips)

    tmp_dir = Path(clips[0]).parent
    clips = _igualar_audio(clips, tmp_dir)
    list_file = tmp_dir / "_concat_final.txt"
    with open(list_file, "w") as f:
        for fc in clips:
            f.write(f"file '{fc}'\n")

    # Primário: copy puro (sem re-encode) + faststart
    cmd_copy = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(list_file), "-c", "copy",
        "-movflags", "+faststart",
        str(out_path),
    ]
    try:
        subprocess.run(cmd_copy, check=True, capture_output=True, timeout=120)
    except subprocess.CalledProcessError:
        # Fallback: re-encode (caso os clips tenham params divergentes)
        cmd_reenc = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(list_file),
            "-c:v", "libx264", "-preset", "fast", "-crf", CLIP_CRF, "-g", "30",
            "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart", "-pix_fmt", "yuv420p",
            str(out_path),
        ]
        subprocess.run(cmd_reenc, check=True, capture_output=True, timeout=300)

    try:
        list_file.unlink()
    except Exception:
        pass

    return out_path.exists()


def upscale_to_fullhd(video_in, video_out):
    """Upscala o vídeo de 720x1280 -> 1080x1920 (lanczos, 1 passada rápida).

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
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False


def build_clip_animated(img_path, audio_path, out_path, panel_idx, effects_mgr, duration=None,
                        transition_type=None, sfx_file=None):
    """Cria clip animado de um painel manga — simula movimento sutil dos personagens.

    Técnicas aplicadas via FFmpeg:
    1. Breathing effect — zoom sinusoidal sutil (1.0->1.02) simulando respiração
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
        # Painel ALTO — pan vertical. Mesmo zoompan achatado dos outros clips
        # (ver _enquadrar): aqui também virou pan por crop, em escala 1:1.
        # O animated_tall_filter fica sem uso: o "breathing" dele dependia do zoompan.
        fg_chain, _ = _enquadrar(pw, ph, animated_tall_filter, None, duration)
        filters = [fg_chain, color_filter]
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
            "-c:v", "libx264", "-preset", "fast", "-crf", CLIP_CRF, "-g", "30",
            "-c:a", "aac", "-b:a", "192k",
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
            "-c:v", "libx264", "-preset", "fast", "-crf", CLIP_CRF, "-g", "30",
            "-c:a", "aac", "-b:a", "192k",
            "-pix_fmt", "yuv420p", "-t", f"{duration:.2f}",
            str(out_path),
        ]

    try:
        cmd = apply_effects_to_cmd(cmd, transition_type, sfx_file, duration)
        subprocess.run(cmd, check=True, capture_output=True, timeout=180)
        if extra_inputs:
            bg_path.unlink(missing_ok=True)
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        if extra_inputs:
            bg_path.unlink(missing_ok=True)
        # Fallback: tentar build_clip normal
        return build_clip(img_path, audio_path, out_path, panel_idx, effects_mgr, duration, transition_type, sfx_file)

