# -*- coding: utf-8 -*-
"""cta_builder: monta o CTA no video, em 2 formatos, com cache por produto.

Formato A (slide): anexa um slide de ~6s no FINAL do video, com o card premium
                   (cta_card) + narracao ElevenLabs (cta_longo). Nao cobre o
                   conteudo; o video principal fica intacto.

Formato B (overlay): sobrepoe um card MENOR no rodape nos ultimos ~4s do video,
                     com a narracao ElevenLabs mixada por cima do audio original
                     (audio original abaixado). Mais moderno, menos "propaganda".

CACHE por produto:
  - audio: cta_cache_audio/<produto>_<voz>.wav  (gera 1x via ElevenLabs)
  - card:  cta_cache_cards/<hash>_<produto>.png (gera 1x via cta_card)

Uso:
    from cta_builder import montar_cta
    montar_cta(video_in, video_out, produto, formato="slide"|"overlay", voz="sarah")
"""
import json
import subprocess
import sys
from pathlib import Path

_BASE = Path(__file__).resolve().parent.parent            # D:\veo\beta
_FFMPEG = r"D:\hipercool-materiais\bin\ffmpeg.exe"
_FFPROBE = r"D:\hipercool-materiais\bin\ffprobe.exe"
_AUDIO_CACHE = _BASE / "pos_producao" / "cta_cache_audio"
_AUDIO_CACHE.mkdir(parents=True, exist_ok=True)
_TMP = _BASE / "pos_producao" / "tmp"
_TMP.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(_BASE / "pos_producao"))

_PRODUTOS_JSON = _BASE / "pos_producao" / "assets" / "produtos.json"
_catalogo_cache = None


def _catalogo():
    global _catalogo_cache
    if _catalogo_cache is None:
        try:
            _catalogo_cache = json.loads(_PRODUTOS_JSON.read_text(encoding="utf-8"))
        except Exception:
            _catalogo_cache = {"produtos": [], "_mapeamento_tema_video": {}}
    return _catalogo_cache


def escolher_produto(tema=None, canal=None, stem=None):
    """Escolhe o produto do CTA CASANDO com o tema do video.

    1) Se o tema/canal casa uma chave de _mapeamento_tema_video -> usa esse produto.
    2) Senao, sorteio ponderado por 'peso' (top=5x, secundario=2x), deterministico
       por stem pra nao repetir o mesmo produto seguido no mesmo video.
    3) Fallback: hermes_call (default do mapeamento) ou 1o produto.
    """
    cat = _catalogo()
    produtos = cat.get("produtos", [])
    if not produtos:
        return None
    by_id = {p.get("id"): p for p in produtos}
    mapa = cat.get("_mapeamento_tema_video", {})

    # 1) casamento por palavra-chave no tema/canal
    alvo = f"{tema or ''} {canal or ''}".lower()
    for chave, pid in mapa.items():
        if chave.startswith("_"):
            continue
        gancho = chave.replace("_", " ")
        if gancho in alvo and pid in by_id:
            return by_id[pid]

    # 2) sorteio ponderado deterministico.
    # md5 (NAO hash() nativo — este e randomizado por processo, quebraria a
    # reprodutibilidade: mesmo video daria produtos diferentes a cada execucao).
    pool = []
    for p in produtos:
        pool.extend([p] * int(p.get("peso", 1)))
    if pool:
        import hashlib as _hl
        chave = (stem or tema or "").encode("utf-8")
        h = int(_hl.md5(chave).hexdigest(), 16) % len(pool)
        return pool[h]

    # 3) fallback
    default = mapa.get("default")
    return by_id.get(default) or produtos[0]


def _dur(path):
    try:
        r = subprocess.run(
            [_FFPROBE, "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, timeout=20)
        return float(r.stdout.strip())
    except Exception:
        return None


import re as _re


def _tts_normalizar(txt: str) -> str:
    """Expande abreviacoes que o TTS le errado (24h -> 24 horas, R$ -> reais...).

    So pra VOZ; o card visual continua com a forma curta ('24h', 'R$').
    """
    t = txt or ""
    # horas/dias colados: 24h -> 24 horas, 7d -> 7 dias (com limite de palavra)
    t = _re.sub(r"(?<![\w])(\d+)\s*[hH](?![\w])", r"\1 horas", t)
    t = _re.sub(r"(?<![\w])(\d+)\s*[dD](?![\w])", r"\1 dias", t)
    t = _re.sub(r"(?<![\w])(\d+)\s*min(?![\w])", r"\1 minutos", t)
    # dinheiro: R$ 199 -> 199 reais ; 199 reais fica igual
    t = _re.sub(r"R\$\s*([\d\.]+)", r"\1 reais", t)
    # 24/7 -> 24 horas por 7 dias
    t = t.replace("24/7", "24 horas por 7 dias").replace("24x7", "24 horas por 7 dias")
    # simbolos que a voz tropeca
    t = t.replace("&", " e ").replace("+", " mais ").replace("%", " por cento")
    t = _re.sub(r"\s{2,}", " ", t).strip()
    return t


# Pool de vozes que rotaciona por stem (mesma chamada, voz diferente).
# Grava 1x cada par (produto, voz) e reusa — sem regravar TTS toda vez.
# Pra forcar uma voz, passe voz="sarah" no caller.
_VOES_POOL = ["sarah", "bella", "matilda", "adam", "eric"]


def _escolher_voz(stem: str = "") -> str:
    """Escolhe a voz do CTA de forma estavel por stem (md5) dentro do pool."""
    import hashlib as _hl
    return _VOES_POOL[int(_hl.md5((stem or "x").encode("utf-8")).hexdigest(), 16)
                      % len(_VOES_POOL)]


def _narracao_cta(produto: dict, voz: str = "", stem: str = "") -> Path | None:
    """Gera (ou reusa) a narracao do CTA. Cache por (produto, voz, TEXTO).

    voz="" ou "auto" — escolhe do pool rotativo pelo STEM do video (a voz muda
      de video pra video, mas cada par (produto, voz) grava so 1x e vira BANCO).
    voz explicita (ex 'sarah') — grava 1x e reusa sempre a mesma.
    Banco de vozes: evita regravar o mesmo audio 671x.

    16/10/2026 (item IM-01 do plano): a fala NAO manda mais a pessoa para o
    WhatsApp. Dizia "Chama no WhatsApp que ta na tela" — mandar sair do YouTube
    pela fala conta igual a mandar pelo texto na politica de spam, e desde que o
    card perdeu o numero a frase nem fazia sentido. O TEXTO agora entra na chave
    do cache: antes era so (produto, voz), entao mudar a frase nao adiantava
    nada — os 38 audios ja gravados continuariam falando o numero.
    """
    pid = produto.get("id", "generico")
    if not voz or voz == "auto":
        # gira pelo video (stem), nao pelo produto: variedade de voz por video
        voz = _escolher_voz(stem=stem or pid)
    # CTA curta (~4-5s): o gancho do produto + um convite sem contato.
    texto = produto.get("cta_curto") or produto.get("nome", "")
    convite = produto.get("convite_voz") or "O link ta no perfil."
    texto_full = _tts_normalizar(f"{texto}. {convite}")
    import hashlib as _hl
    _h = _hl.md5(f"{texto_full}|{voz}".encode("utf-8")).hexdigest()[:8]
    out = _AUDIO_CACHE / f"{pid}_{voz}_{_h}.wav"
    if out.exists() and out.stat().st_size > 1000:
        return out
    try:
        from elevenlabs_veo import speak, disponivel
        if not disponivel():
            return _narracao_edge(texto_full, out)
        if speak(texto_full, out, voz=voz):
            return out
    except Exception:
        pass
    return _narracao_edge(texto_full, out)


def _narracao_edge(texto: str, out: Path) -> Path | None:
    """Fallback keyless: Edge-TTS voz PT-BR (se ElevenLabs esgotou)."""
    try:
        from edge_tts_veo import speak as edge_speak
        if edge_speak(texto, out_wav=str(out)):
            return out
    except Exception:
        pass
    return None


def _card(produto: dict, stem: str = "") -> Path:
    # stem escolhe a VARIANTE visual do banco (alterna de video pra video;
    # cada (produto, variante) gera 1x e fica cacheado).
    from cta_card import gerar_card
    return gerar_card(produto, stem=stem)


# ---------------------------------------------------------------------------
# Formato A: slide no final
# ---------------------------------------------------------------------------
def _slide_clip(card_png: Path, audio_wav: Path | None, saida: Path,
                w: int, h: int, fps=30) -> bool:
    """Cria o clip do slide: card animado (fade+zoom leve) + narracao."""
    dur = (_dur(audio_wav) + 0.6) if audio_wav else 6.0
    dur = max(4.0, min(dur, 12.0))
    vf = (
        f"scale={w}:{h}:force_original_aspect_ratio=increase,"
        f"crop={w}:{h},"
        f"zoompan=z='min(zoom+0.0006,1.08)':d={int(dur*fps)}:s={w}x{h}:fps={fps},"
        f"fade=t=in:st=0:d=0.4,fade=t=out:st={dur-0.4:.2f}:d=0.4,format=yuv420p"
    )
    cmd = [_FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
           "-loop", "1", "-t", f"{dur:.2f}", "-r", str(fps), "-i", str(card_png)]
    if audio_wav:
        cmd += ["-i", str(audio_wav)]
    cmd += ["-vf", vf]
    if audio_wav:
        # -14 LUFS / -1 dBTP como o limpo (AT-10, 16/10): em -16 o volume caia na hora da propaganda
        cmd += ["-af", "apad,loudnorm=I=-14:TP=-1:LRA=11",
                "-map", "0:v", "-map", "1:a", "-t", f"{dur:.2f}"]
    else:
        cmd += ["-f", "lavfi", "-t", f"{dur:.2f}",
                "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
                "-map", "0:v", "-map", "2:a"]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-ac", "2",
            "-pix_fmt", "yuv420p", "-r", str(fps), str(saida)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
    if r.returncode != 0:
        print(f"[cta_builder] slide_clip err: {r.stderr[-300:]}", flush=True)
    return r.returncode == 0 and saida.exists()


def _norm_video(video_in: Path, saida: Path, w: int, h: int, fps=30) -> bool:
    """Normaliza o video principal (mesmo codec/params) pra concat casar."""
    cmd = [_FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
           "-i", str(video_in),
           "-vf", f"scale={w}:{h},fps={fps},format=yuv420p",
           "-c:v", "libx264", "-preset", "medium", "-crf", "20",
           "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-ac", "2",
           "-pix_fmt", "yuv420p", str(saida)]
    # garante audio mesmo se o veo veio mudo
    probe = subprocess.run([_FFPROBE, "-v", "error", "-select_streams", "a",
                            "-show_entries", "stream=index", "-of", "csv=p=0",
                            str(video_in)], capture_output=True, text=True)
    if not probe.stdout.strip():
        d = _dur(video_in) or 8.0
        cmd = [_FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
               "-i", str(video_in),
               "-f", "lavfi", "-t", f"{d:.2f}",
               "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
               "-vf", f"scale={w}:{h},fps={fps},format=yuv420p",
               "-map", "0:v", "-map", "1:a",
               "-c:v", "libx264", "-preset", "medium", "-crf", "20",
               "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-ac", "2",
               "-pix_fmt", "yuv420p", str(saida)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return r.returncode == 0 and saida.exists()


def _montar_slide(video_in, video_out, produto, voz, w, h, fps=30) -> bool:
    stem = Path(video_in).stem
    card = _card(produto)
    audio = _narracao_cta(produto, voz)
    slide = _TMP / f"{stem}_slide.mp4"
    main = _TMP / f"{stem}_main.mp4"
    if not _slide_clip(card, audio, slide, w, h, fps):
        return False
    if not _norm_video(Path(video_in), main, w, h, fps):
        return False
    lista = _TMP / f"{stem}_concat.txt"
    lista.write_text(f"file '{main.as_posix()}'\nfile '{slide.as_posix()}'\n", encoding="utf-8")
    cmd = [_FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
           "-f", "concat", "-safe", "0", "-i", str(lista),
           "-c", "copy", "-movflags", "+faststart", str(video_out)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        print(f"[cta_builder] concat err: {r.stderr[-300:]}", flush=True)
    for p in (slide, main, lista):
        try: p.unlink(missing_ok=True)
        except Exception: pass
    return r.returncode == 0 and Path(video_out).exists()


# ---------------------------------------------------------------------------
# Formato B: overlay nos ultimos segundos
# ---------------------------------------------------------------------------
def _card_faixa(produto: dict, w: int) -> Path:
    """Gera uma faixa horizontal compacta (card_faixa) pro overlay no rodape."""
    from PIL import Image, ImageDraw
    from subtitles_veo import _load_font
    import hashlib, textwrap
    pid = produto.get("id", "generico")
    fw, fh = w, int(w * 0.42)
    chave = f"faixa|{pid}|{fw}x{fh}|v3"
    out = _BASE / "pos_producao" / "cta_cache_cards" / f"faixa_{hashlib.md5(chave.encode()).hexdigest()[:12]}_{pid}.png"
    if out.exists() and out.stat().st_size > 3000:
        return out

    def hexrgb(hh, d=(37, 211, 102)):
        try:
            hh = hh.lstrip("#"); return tuple(int(hh[i:i+2], 16) for i in (0, 2, 4))
        except Exception: return d
    cor = hexrgb(produto.get("cor", "#25D366"))
    nome = produto.get("nome", "Inovare IA")
    copy = produto.get("cta_curto") or nome
    zap = "WhatsApp {whatsapp}"

    img = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # painel arredondado semi-translucido escuro
    pad = int(fw * 0.04)
    d.rounded_rectangle([pad, pad, fw - pad, fh - pad], radius=int(fh * 0.16),
                        fill=(15, 15, 20, 235))
    # barra de cor lateral (identidade)
    d.rounded_rectangle([pad, pad, pad + int(fw * 0.025), fh - pad],
                        radius=8, fill=cor + (255,))
    x = pad + int(fw * 0.06)
    # nome
    fn = _load_font(int(fh * 0.24))
    d.text((x, int(fh * 0.16)), nome, font=fn, fill=(255, 255, 255), stroke_width=3, stroke_fill=(0, 0, 0))
    # copy
    fc = _load_font(int(fh * 0.15))
    linha = textwrap.wrap(copy, width=34)[:1]
    if linha:
        d.text((x, int(fh * 0.44)), linha[0], font=fc, fill=cor)
    # badge zap
    fz = _load_font(int(fh * 0.16))
    zb = d.textbbox((0, 0), zap, font=fz)
    zw, zh = zb[2] - zb[0], zb[3] - zb[1]
    bx0, by0 = x, int(fh * 0.66)
    bx1, by1 = x + zw + int(fh * 0.5), by0 + zh + int(fh * 0.16)
    d.rounded_rectangle([bx0, by0, bx1, by1], radius=(by1 - by0) // 2, fill=(37, 211, 102, 255))
    ir = (by1 - by0) // 2 - 6
    icx, icy = bx0 + ir + 10, (by0 + by1) // 2
    d.ellipse([icx - ir, icy - ir, icx + ir, icy + ir], fill=(255, 255, 255))
    d.text((bx0 + ir * 2 + 20, by0 + int(fh * 0.06)), zap, font=fz, fill=(255, 255, 255))
    img.save(out, "PNG")
    return out


def _montar_overlay(video_in, video_out, produto, voz, w, h, fps=30,
                    dur_cta=5.0) -> bool:
    stem = Path(video_in).stem
    faixa = _card_faixa(produto, w)
    audio = _narracao_cta(produto, voz)
    vdur = _dur(video_in) or 8.0
    start = max(0.0, vdur - dur_cta)
    fdur = _dur(faixa) if False else dur_cta
    a_dur = _dur(audio) if audio else 0
    # se a narracao for maior que a janela, estende a janela do overlay
    if a_dur and a_dur > dur_cta:
        start = max(0.0, vdur - a_dur - 0.3)

    # overlay do PNG no rodape a partir de 'start' com slide-in
    y_expr = f"'if(lt(t,{start}),H, H-h-{int(h*0.04)})'"
    inputs = ["-i", str(video_in), "-loop", "1", "-i", str(faixa)]
    if audio:
        inputs += ["-i", str(audio)]
    fc = (
        f"[1:v]format=rgba,fade=t=in:st={start:.2f}:d=0.4:alpha=1[ov];"
        f"[0:v][ov]overlay=(W-w)/2:{y_expr}:enable='gte(t,{start:.2f})'[v]"
    )
    cmd = [_FFMPEG, "-y", "-hide_banner", "-loglevel", "error"] + inputs
    if audio:
        # mixa narracao (comeca em 'start') com audio original abaixado no fim
        fc += (
            f";[2:a]adelay={int(start*1000)}|{int(start*1000)},"
            f"loudnorm=I=-16:TP=-1.5:LRA=11[cta];"
            f"[0:a]volume='if(gte(t,{start:.2f}),0.25,1.0)':eval=frame[bg];"
            f"[bg][cta]amix=inputs=2:duration=first:dropout_transition=0[a]"
        )
        cmd += ["-filter_complex", fc, "-map", "[v]", "-map", "[a]"]
    else:
        cmd += ["-filter_complex", fc, "-map", "[v]", "-map", "0:a?"]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-c:a", "aac", "-b:a", "160k", "-ar", "44100",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            "-t", f"{max(vdur, start + (a_dur or dur_cta) + 0.3):.2f}",
            str(video_out)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if r.returncode != 0:
        print(f"[cta_builder] overlay err: {r.stderr[-400:]}", flush=True)
    return r.returncode == 0 and Path(video_out).exists()


def montar_cta(video_in, video_out, produto, formato="slide", voz="sarah") -> bool:
    """Monta o CTA no video. formato: 'slide' | 'overlay'."""
    probe = subprocess.run(
        [_FFPROBE, "-v", "error", "-select_streams", "v", "-show_entries",
         "stream=width,height", "-of", "csv=p=0:s=x", str(video_in)],
        capture_output=True, text=True)
    try:
        w, h = [int(x) for x in probe.stdout.strip().split("x")[:2]]
    except Exception:
        w, h = 720, 1280
    if formato == "overlay":
        return _montar_overlay(video_in, video_out, produto, voz, w, h)
    return _montar_slide(video_in, video_out, produto, voz, w, h)


if __name__ == "__main__":
    import sys
    video = sys.argv[1]
    voz = sys.argv[2] if len(sys.argv) > 2 else "sarah"
    cat = json.loads((_BASE / "pos_producao" / "assets" / "produtos.json").read_text(encoding="utf-8"))
    produto = cat["produtos"][0]  # hermes_call
    stem = Path(video).stem
    outdir = _BASE / "pos_producao" / "tmp" / "amostras_cta"
    outdir.mkdir(parents=True, exist_ok=True)
    for fmt in ("slide", "overlay"):
        out = outdir / f"{stem}_{fmt}_{voz}.mp4"
        ok = montar_cta(video, out, produto, formato=fmt, voz=voz)
        print(f"  {fmt:8} {'OK' if ok else 'FALHOU'} -> {out}")
