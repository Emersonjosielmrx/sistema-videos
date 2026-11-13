"""propaganda_inteligente: slide de propaganda (estilo mini-historia).

Diferencas vs versao anterior (card verde estatico):
  - Fundo gerado por IA (OmniRoute Image -> fallback Pollinations) com cache
    por hash do prompt; se tudo falhar cai no gradiente PIL.
  - Layout centralizado: icone/logo + nome + copy + WhatsApp em colunas
  - Animacao: fade in + zoom sutil + leve pan (estilo fx_intro do historias-em-frames)
  - Fonte PIL com stroke (legendas_veo.py), nao drawtext cru
  - Pode usar imagem do produto (assets/produtos/<id>.png) se existir

Quando voce tem uma imagem de referencia do produto, fica no estilo:
  [LOGO CENTRAL]
  Nome do Produto
  - Copy curta -
  WhatsApp {whatsapp}

CPU-only no fallback; IA opcional (rede)."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

SUFFIX = "prop"
_BASE = Path(__file__).resolve().parent.parent.parent  # D:\veo\beta
_ASSETS = _BASE / "pos_producao" / "assets"
_LOGOS = _BASE / "pos_producao" / "logos"
_FFMPEG = r"D:\hipercool-materiais\bin\ffmpeg.exe"
_PRODUTOS = _ASSETS / "produtos.json"
_FUNDO_CACHE = _BASE / "pos_producao" / "propaganda_cache_fundo"
_FUNDO_CACHE.mkdir(parents=True, exist_ok=True)

_DURACAO_PROP_S = 6.0  # aumentado pra cobrir o TTS da CTA (TTS ~6-8s)
# se OMNIROUTE_DISABLED=1, pula direto pro gradiente PIL
_OMNIROUTE_DISABLED = os.environ.get("OMNIROUTE_DISABLED", "0") == "1"


def _carregar_catalogo():
    if not _PRODUTOS.exists():
        return {"_meta": {}, "produtos": [], "_mapeamento_tema_video": {"default": None}}
    try:
        with open(_PRODUTOS, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"_meta": {}, "produtos": [], "_mapeamento_tema_video": {"default": None}}


def _escolher_produto_inteligente(stem, tema_video, catalogo):
    """Mesmo algoritmo da versao antiga: pool + peso, mas só retorna."""
    produtos = catalogo.get("produtos") or []
    if not produtos:
        return None
    pool = []
    for p in produtos:
        peso = int(p.get("peso", 1))
        pool.extend([p] * peso)
    if not pool:
        return None
    # md5, nao hash(): o hash() de string muda a cada processo e o mesmo video pegava produto diferente a cada
    # rodada (BX-05, 16/10)
    import hashlib
    h = int(hashlib.md5((stem or "").encode("utf-8")).hexdigest(), 16)
    return pool[h % len(pool)]


def _copy_curta(produto: dict) -> str:
    """Copy sem numero (zap eh destaque separado)."""
    return produto.get("cta_curto") or produto.get("nome") or "Inovare IA"


def _gerar_fundo_ia(cor_rgb: tuple, tema: str, w=1080, h=1920) -> Path | None:
    """Tenta gerar fundo artistico via OmniRoute Image (FREE, com cache).
    Retorna Path do PNG ou None se tudo falhou.

    Usa o cliente do historias-em-frames (omniroute_image._generate) que ja
    tem failover: OmniRoute 3 modelos -> Pollinations. Cache por hash do
    prompt em propaganda_cache_fundo/<hash>.png.
    """
    if _OMNIROUTE_DISABLED:
        return None
    # chave do cache = tema + cor (prompts identicos reusam o mesmo fundo)
    import hashlib
    chave = f"{tema}|{cor_rgb}|{w}x{h}"
    h_hash = hashlib.md5(chave.encode()).hexdigest()[:16]
    cache = _FUNDO_CACHE / f"{h_hash}.png"
    if cache.exists() and cache.stat().st_size > 5000:
        return cache

    # monta prompt em ingles (modelos respondem melhor assim)
    cor_nome = {
        (37, 211, 102): "vibrant green",
        (29, 161, 242): "sky blue",
        (255, 0, 80): "magenta pink",
        (255, 165, 0): "warm orange",
        (120, 81, 169): "deep purple",
        (255, 215, 0): "golden yellow",
    }.get(cor_rgb, "dark teal")

    prompt = (
        f"Vertical {w}x{h} abstract cinematic background, {cor_nome} color palette, "
        f"subtle neon glow, soft particles, minimalist tech aesthetic, "
        f"high quality, no text, no characters, no logos, suitable as a video slide background. "
        f"Mood: {tema}."
    )

    try:
        sys.path.insert(0, r"D:\historias-em-frames\bin")
        from omniroute_image import _generate  # type: ignore
    except Exception:
        return None

    ok = False
    try:
        ok = _generate(prompt, cache)
    except Exception:
        ok = False
    if ok and cache.exists() and cache.stat().st_size > 5000:
        return cache
    try:
        cache.unlink()
    except Exception:
        pass
    return None


def _gerar_slide_png(produto: dict, copy: str, out_png: Path,
                    w=1080, h=1920):
    """Gera slide de propaganda como PNG 1080x1920.

    Layout (de cima pra baixo):
        [LOGO grande se existir, senao circulo com letra]
        [nome do produto, fontsize 110, bold]
        [copy, fontsize 60]
        [WhatsApp, fontsize 70, box preto]
        [handle @InovareStories, fontsize 45, base]

    Fundo: tenta gerar imagem IA (OmniRoute/Pollinations). Se falhar,
    cai no gradiente PIL da cor do produto.
    """
    from PIL import Image, ImageDraw, ImageFont

    cor_hex = produto.get("cor", "#25D366").lstrip("#")
    try:
        cor_rgb = tuple(int(cor_hex[i:i+2], 16) for i in (0, 2, 4))
    except Exception:
        cor_rgb = (37, 211, 102)

    tema = produto.get("nome", "tech")
    fundo_ia = _gerar_fundo_ia(cor_rgb, tema, w, h)

    if fundo_ia is not None:
        try:
            img = Image.open(fundo_ia).convert("RGB").resize((w, h), Image.LANCZOS)
        except Exception:
            img = Image.new("RGB", (w, h), cor_rgb)
    else:
        img = Image.new("RGB", (w, h), cor_rgb)
        draw_grad = ImageDraw.Draw(img)
        for y in range(h):
            fator = 0.7 + 0.3 * (1 - y / h)
            cor = tuple(int(c * fator) for c in cor_rgb)
            draw_grad.line([(0, y), (w, y)], fill=cor)

    # overlay escuro sutil pra copy ficar legivel sobre qualquer fundo IA
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 90))
    img = img.convert("RGBA")
    img.alpha_composite(overlay)
    img = img.convert("RGB")
    draw = ImageDraw.Draw(img)

    # fontes (reusa o do subtitles_veo)
    import sys
    sys.path.insert(0, str(_BASE / "pos_producao"))
    from subtitles_veo import _load_font

    fs_nome = 120
    fs_copy = 60
    fs_zap = 75
    fs_handle = 45

    nome = produto.get("nome", "Inovare IA")
    # 16/10/2026 (item IM-01 do plano): nada de telefone nem @ escritos aqui.
    # O contato so aparece se o PRODUTO trouxer 'contato_na_tela' (usado fora do
    # YouTube); o rodape fica com o convite, sem numero. Este plugin saiu do
    # pipeline (pos_producao/config.yaml), mas nao pode voltar a estampar contato
    # se alguem religar: foi uma das causas apontadas da suspensao de 04/09/2026.
    whatsapp = (produto.get("contato_na_tela") or "").strip()
    rodape = whatsapp or (produto.get("convite") or "LINK NO PERFIL")
    handle = ""

    # centralizado vertical em colunas
    cx = w // 2

    # LOGO / icone (circulo com primeira letra)
    raio = 220
    cy_logo = int(h * 0.18)
    draw.ellipse([cx - raio, cy_logo - raio, cx + raio, cy_logo + raio],
                 fill=(255, 255, 255))
    draw.ellipse([cx - raio, cy_logo - raio, cx + raio, cy_logo + raio],
                 outline=(0, 0, 0), width=4)
    letra = (nome[0] if nome else "I").upper()
    fnt_letra = _load_font(int(raio * 1.1))
    bbox = draw.textbbox((0, 0), letra, font=fnt_letra, stroke_width=6)
    lw = bbox[2] - bbox[0]
    lh = bbox[3] - bbox[1]
    draw.text((cx - lw // 2 - bbox[0], cy_logo - lh // 2 - bbox[1]),
              letra, font=fnt_letra, fill=cor_rgb,
              stroke_width=6, stroke_fill=(0, 0, 0, 0))

    # NOME (y ~38% da altura)
    fnt_nome = _load_font(fs_nome)
    bbox = draw.textbbox((0, 0), nome, font=fnt_nome, stroke_width=10)
    nw = bbox[2] - bbox[0]
    nh = bbox[3] - bbox[1]
    y_nome = int(h * 0.38) - nh // 2
    draw.text((cx - nw // 2 - bbox[0], y_nome - bbox[1]), nome,
              font=fnt_nome, fill=(255, 255, 255),
              stroke_width=10, stroke_fill=(0, 0, 0))

    # COPY (y ~52%)
    fnt_copy = _load_font(fs_copy)
    bbox = draw.textbbox((0, 0), copy, font=fnt_copy, stroke_width=6)
    cw = bbox[2] - bbox[0]
    ch = bbox[3] - bbox[1]
    y_copy = int(h * 0.52) - ch // 2
    draw.text((cx - cw // 2 - bbox[0], y_copy - bbox[1]), copy,
              font=fnt_copy, fill=(255, 255, 255),
              stroke_width=6, stroke_fill=(0, 0, 0))

    # RODAPE (y ~72%, com box preto): convite por padrao; contato so se o produto
    # pedir de proposito em 'contato_na_tela' (nunca no corte do YouTube).
    fnt_zap = _load_font(fs_zap)
    bbox = draw.textbbox((0, 0), rodape, font=fnt_zap, stroke_width=6)
    zw = bbox[2] - bbox[0]
    zh = bbox[3] - bbox[1]
    y_zap = int(h * 0.72) - zh // 2
    box_pad_x = 50
    box_pad_y = 20
    draw.rectangle(
        [cx - zw // 2 - box_pad_x - bbox[0], y_zap - box_pad_y - bbox[1],
         cx + zw // 2 + box_pad_x - bbox[0], y_zap + zh + box_pad_y - bbox[1]],
        fill=(0, 0, 0, 200))
    draw.text((cx - zw // 2 - bbox[0], y_zap - bbox[1]), rodape,
              font=fnt_zap, fill=(255, 255, 255),
              stroke_width=6, stroke_fill=(0, 0, 0))

    # HANDLE (base) — so desenha se vier algum; hoje fica vazio de proposito:
    # a marca do canal de destino e gravada na hora de postar (rede::rebrand).
    if handle:
        fnt_h = _load_font(fs_handle)
        bbox = draw.textbbox((0, 0), handle, font=fnt_h, stroke_width=3)
        hw = bbox[2] - bbox[0]
        draw.text((cx - hw // 2 - bbox[0], int(h * 0.92) - bbox[1]),
                  handle, font=fnt_h, fill=(255, 255, 255, 200),
                  stroke_width=3, stroke_fill=(0, 0, 0))

    img.save(out_png, "PNG")
    return out_png


def _gerar_clip_animado(png_path: Path, saida: Path, duracao=_DURACAO_PROP_S,
                       w=1080, h=1920, fps=30):
    """PNG -> mp4 estatico com duracao EXATA = duracao segundos.

    Antes usava zoompan mas o filter eh problematico (inconsistente,
    timeoutavel quando a source tem 1 frame). Agora: PNG estica + fade
    in/out, duracao via -t (ffmpeg trunca com precisao de frame).
    Imagem parada eh aceitavel pro slide de propaganda - o foco eh texto.
    """
    cmd = [
        _FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
        "-loop", "1", "-t", f"{duracao:.3f}", "-r", str(fps),
        "-i", str(png_path),
        # escala e centraliza, depois fade in/out
        "-vf",
        f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
        f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black,"
        f"fade=t=in:st=0:d=0.3,"
        f"fade=t=out:st={duracao-0.3:.3f}:d=0.3,"
        f"format=yuv420p",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-r", str(fps),
        "-movflags", "+faststart",
        str(saida),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        print(f"[propaganda_inteligente] _gerar_clip_animado rc={r.returncode} stderr={r.stderr[:300]}", flush=True)
    return r.returncode == 0 and saida.exists()


def _gerar_clip_parallax(png_path: Path, fala_wav, saida: Path,
                          duracao=_DURACAO_PROP_S, w=1080, h=1920, fps=30):
    """Gera clip de propaganda com parallax 2.5D (depth + 3 camadas + terror)
    usando o parallax_engine do hipercool-videos. Se fala_wav for None,
    gera silencio com mesma duracao. Retorna True/False (False = cai no fallback).
    """
    import sys as _sys
    _sys.path.insert(0, r"D:\hipercool-videos\ambientes\3-exp\bin")
    try:
        import parallax_engine  # type: ignore
    except Exception as e:
        print(f"[propaganda_inteligente] parallax_engine nao importou: {e}", flush=True)
        return False

    # se nao tiver TTS, gera silencio temporario com mesma duracao
    if not fala_wav or not Path(fala_wav).exists():
        sil = saida.with_suffix(".silence.wav")
        cmd = [
            _FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi", "-i", f"anullsrc=channel_layout=mono:sample_rate=44100",
            "-t", f"{duracao:.3f}",
            "-c:a", "pcm_s16le",
            str(sil),
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        if r.returncode != 0 or not sil.exists():
            return False
        fala_wav = str(sil)

    try:
        ok = parallax_engine.build_parallax_clip(
            str(png_path),
            fala_wav,
            str(saida),
            duration=duracao,
            W=w, H=h, fps=fps,
            terror=True,
        )
        if ok:
            print(f"[propaganda_inteligente] parallax OK -> {saida}", flush=True)
        else:
            print(f"[propaganda_inteligente] parallax falhou, fallback", flush=True)
        return ok
    except Exception as e:
        print(f"[propaganda_inteligente] parallax excecao {e}", flush=True)
        return False
    finally:
        sil = saida.with_suffix(".silence.wav")
        try:
            sil.unlink()
        except Exception:
            pass


def _concat(lista_mp4, saida: Path) -> bool:
    """Wrapper do _concat_safe (3-passos com normalizacao de audio)."""
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).parent))
    from _concat_safe import _concat_safe
    return _concat_safe(lista_mp4, saida)


def _concat_xfade(lista_mp4, saida: Path, fade_dur: float = 0.3, w=1080, h=1920) -> bool:
    """Concatena segmentos com xfade (transicao cruzada) entre cada par.
    Usa filter_complex xfade + acrossfade. Requer re-encode (CPU),
    entao eh mais lento que _concat (copy) - use so no final do pipeline.

    Args:
      lista_mp4: lista de paths (str ou Path)
      saida: Path do arquivo final
      fade_dur: duracao do xfade em segundos entre cada par de segmentos
    """
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).parent))
    from _concat_safe import _ffprobe_dur, _ffprobe_has_audio
    n = len(lista_mp4)
    if n == 0:
        return False
    if n == 1:
        # sem transicao, copia simples
        import shutil
        shutil.copyfile(str(lista_mp4[0]), str(saida))
        return True

    inputs = []
    for p in lista_mp4:
        inputs += ["-i", str(p)]

    # monta filter_complex: xfade entre v0-v1, v0v1-v2, ... + acrossfade audio
    # primeiro normaliza todos videos pra w x h com scale+pad (garante mesmo size/timebase pro xfade)
    parts = []
    for i, p in enumerate(lista_mp4):
        parts.append(
            f"[{i}:v]scale={w}:{h}:force_original_aspect_ratio=decrease,"
            f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black,"
            f"format=yuv420p,fps=30,setpts=PTS-STARTPTS[v{i}]"
        )
    last_v = "v0"
    audio_idx_with = []
    for i, p in enumerate(lista_mp4):
        if _ffprobe_has_audio(p):
            audio_idx_with.append(i)

    # xfade encadeado
    for i in range(1, n):
        # offset = onde a transicao i comeca, na timeline JA fundida.
        # = soma das duracoes 0..i-1 menos i fades (um por transicao ate aqui,
        #   incluindo a atual, que precisa comecar fade_dur ANTES do fim).
        # Bug antigo subtraia so (i-1) fades -> offset ficava um fade grande
        # demais e o xfade descartava o segmento seguinte (video ficava so 8s).
        offset = 0.0
        for k in range(i):
            offset += _ffprobe_dur(lista_mp4[k])
        for k in range(i):
            offset -= fade_dur
        out_v = f"vx{i}" if i < n - 1 else "vout"
        parts.append(
            f"[{last_v}][v{i}]xfade=transition=fade:duration={fade_dur}:offset={max(0, offset):.3f}[{out_v}]"
        )
        last_v = out_v

    # duracao total do video apos a cadeia de xfade:
    # soma de todos os segmentos menos um fade_dur por transicao (n-1 transicoes)
    total_dur = sum(_ffprobe_dur(p) for p in lista_mp4) - (n - 1) * fade_dur

    # acrossfade encadeado entre audios (cada label eh o indice real do input)
    if audio_idx_with:
        if len(audio_idx_with) == 1:
            idx = audio_idx_with[0]
            # apad ATE a duracao total do video (nao infinito) -> audio e video
            # terminam juntos. Antes era apad puro (silencio infinito) que sem
            # -shortest travava, e com -shortest cortava o video nos 8s do audio.
            parts.append(f"[{idx}:a]aresample=44100,apad=whole_dur={total_dur:.3f}[aout]")
        else:
            last_a = f"[{audio_idx_with[0]}:a]"
            for j in range(1, len(audio_idx_with)):
                idx = audio_idx_with[j]
                out_a = f"a{j}" if j < len(audio_idx_with) - 1 else "aout"
                parts.append(
                    f"{last_a}[{idx}:a]acrossfade=d={fade_dur}[{out_a}]"
                )
                last_a = f"[{out_a}]"
        filter_complex = ";".join(parts)
        vmap = ["-map", "[vout]"]
        amap = ["-map", "[aout]"]
    else:
        # sem audio nenhum: gera anullsrc e concatena com video
        filter_complex = ";".join(parts) + ";anullsrc=channel_layout=mono:sample_rate=44100[asil]"
        vmap = ["-map", "[vout]"]
        amap = ["-map", "[asil]"]

    cmd = [
        _FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
        *inputs,
        "-filter_complex", filter_complex,
        *vmap, *amap,
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
        "-pix_fmt", "yuv420p", "-r", "30",
        "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
        "-movflags", "+faststart",
        "-shortest",  # apad gera silencio infinito; -shortest corta no fim do video (senao trava)
        str(saida),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        print(f"[propaganda_inteligente] _concat_xfade rc={r.returncode} stderr={r.stderr[:400]}", flush=True)
        # fallback: concat sem xfade
        return _concat(lista_mp4, saida)
    return r.returncode == 0 and saida.exists()


def processar(input_mp4: str, output_mp4: str, meta: dict) -> bool:
    """Anexa slide de propaganda no final do video.

    A partir de 2026-07-27 v2, o slide vem COM TTS da CTA (copy + whatsapp)
    via helper _tts_helper (Edge-TTS ou Gemini). O video principal fica
    com audio original do Veo intacto.
    """
    if not Path(_FFMPEG).exists() or not Path(input_mp4).exists():
        return False
    catalogo = _carregar_catalogo()
    stem = meta.get("stem", "")
    tema_video = meta.get("tema")
    produto = _escolher_produto_inteligente(stem, tema_video, catalogo)
    if not produto:
        return False
    copy = _copy_curta(produto)
    nome = produto.get("nome", "Inovare IA")
    # 16/10/2026: a fala NAO diz mais o numero de telefone. Dois motivos: o TTS
    # erra numero falado, e "chama no WhatsApp <numero>" e exatamente o tipo de
    # redirecionamento que a politica de spam do YouTube pune (vale para a fala,
    # nao so para o texto na tela).
    extra = produto.get("cta_gancho") or "Atendimento 24 horas e a primeira semana eh por nossa conta"
    fala_cta = f"{nome}. {copy}. {extra}."

    # gera PNG e clip animado em tmp
    tmp_png = Path(output_mp4).with_suffix(".prop.png")
    tmp_clip_video = Path(output_mp4).with_suffix(".prop_clip_video.mp4")
    tmp_clip_final = Path(output_mp4).with_suffix(".prop_clip_final.mp4")
    try:
        # Gera TTS da CTA (Edge-TTS keyless, cache por produto)
        produto_id = produto.get("id") or produto.get("nome", "default")
        import sys as _sys
        _sys.path.insert(0, str(Path(__file__).parent))
        from _tts_helper import gerar_tts_cta
        fala_wav = gerar_tts_cta(fala_cta, produto_id)

        # gera PNG do slide
        _gerar_slide_png(produto, copy, tmp_png)
        if not tmp_png.exists():
            return False

        # Tenta parallax 2.5D (depth + 3 camadas + terror). Cai no fallback
        # estatico se falhar (modelo HF indisponivel, depth demorar demais, etc).
        clip_ok = _gerar_clip_parallax(
            tmp_png, fala_wav, tmp_clip_final,
            duracao=_DURACAO_PROP_S,
        )
        if not clip_ok:
            # fallback: PNG estatico + TTS mixado (mesmo do v2)
            if not _gerar_clip_animado(tmp_png, tmp_clip_video):
                return False
            if fala_wav:
                ok = _mixar_audio_no_clip(tmp_clip_video, str(fala_wav), tmp_clip_final)
                if not ok:
                    tmp_clip_final = _clip_com_silencio(tmp_clip_video)
            else:
                tmp_clip_final = _clip_com_silencio(tmp_clip_video)

        # concat final com xfade 0.3s entre main e propaganda (transicao suave)
        ok = _concat_xfade([input_mp4, str(tmp_clip_final)], Path(output_mp4), fade_dur=0.3)
        return ok
    finally:
        for f in (tmp_png, tmp_clip_video, tmp_clip_final):
            try:
                f.unlink()
            except Exception:
                pass


def _clip_com_silencio(clip_video: Path) -> Path:
    """Adiciona trilha de audio silenciosa com mesma duracao do clip_video.
    Usado como fallback quando TTS nao gera audio.
    """
    saida = clip_video.with_suffix(".silent.mp4")
    try:
        r = subprocess.run(
            [_FFMPEG, "-i", str(clip_video)],
            capture_output=True, text=True, timeout=30,
        )
        import re
        m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", r.stderr)
        if m:
            hh, mm, ss = m.groups()
            dur = int(hh) * 3600 + int(mm) * 60 + float(ss)
        else:
            dur = _DURACAO_PROP_S
    except Exception:
        dur = _DURACAO_PROP_S
    cmd = [
        _FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(clip_video),
        "-f", "lavfi", "-t", f"{dur:.3f}", "-i", f"anullsrc=channel_layout=mono:sample_rate=44100",
        "-map", "0:v", "-map", "1:a",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
        "-shortest",
        "-movflags", "+faststart",
        str(saida),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return saida if (r.returncode == 0 and saida.exists()) else clip_video


def _mixar_audio_no_clip(clip_video: Path, fala_wav: str, saida: Path) -> bool:
    """Substitui o audio (silencio) do clip_video pelo fala_wav, esticando
    o fala pra duracao do clip (apad) e aplicando loudnorm EBU R128.

    O clip_video vem do _gerar_clip_animado - ainda nao tem audio, entao
    pegamos a duracao do clip via ffprobe e geramos audio com apad.
    """
    try:
        r = subprocess.run(
            [_FFMPEG, "-i", str(clip_video)],
            capture_output=True, text=True, timeout=30,
        )
        import re
        m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", r.stderr)
        if m:
            hh, mm, ss = m.groups()
            dur = int(hh) * 3600 + int(mm) * 60 + float(ss)
        else:
            dur = _DURACAO_PROP_S
    except Exception:
        dur = _DURACAO_PROP_S

    afilt = (
        f"apad=whole_dur={dur:.3f},"
        f"atrim=0:{dur:.3f},"
        f"loudnorm=I=-16:TP=-1.5:LRA=11"
    )
    cmd = [
        _FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(clip_video),
        "-i", fala_wav,
        "-map", "0:v", "-map", "1:a",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
        "-af", afilt,
        # trunca AMBOS streams no dur (mais confiavel que -shortest)
        "-t", f"{dur:.3f}",
        "-movflags", "+faststart",
        str(saida),
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            print(f"[propaganda_inteligente] _mixar_audio_no_clip stderr={r.stderr[:300]}", flush=True)
        return r.returncode == 0 and saida.exists()
    except Exception:
        return False