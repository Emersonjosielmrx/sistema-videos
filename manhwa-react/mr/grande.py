"""React grande (video longo deitado, webcam no canto) para postar INTEIRO.

Nada e cortado: o video vai como foi gravado (stream copiado), so o audio e nivelado em -14 LUFS (sem RNNoise, que
estragaria a trilha do video reagido). O editorial gera titulo, descricao com credito ao video original e capitulos,
tags, comentario fixado e o texto da thumb (1280x720: painel do manhwa + rosto do criador).
Saida em hipercool-materiais/manhwa-react/grandes/<canal>/ - separado dos Shorts (shorts/) e dos cortes deste react (cortes/).
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from .common import log, load_json, save_json, ffmpeg
from . import probe as P, audio as A, transcribe as T, editorial as ED, thumb as TH
from .llm import ask_json


def eh_grande(cfg, info):
    """Gravacao deitada e longa -> vira video inteiro + cortes."""
    return info.get("width", 0) > info.get("height", 0) and info.get("duration", 0) > float(cfg["editorial"].get("long_threshold", 240))


INSTRUCOES = """Voce e o editor de um canal de react de manhwa no YouTube. Este e um video LONGO e HORIZONTAL ({dur_min:.0f} min) que vai
ser postado INTEIRO. Linhas CRIADOR = fala do criador; linhas CONTEUDO = narracao do video reagido.
{base}
Canais disponiveis (slug - nicho):
{canais}

Responda SOMENTE com um JSON valido:
{{
 "channel": "slug do canal",
 "obra": "nome da obra reagida (ou null)",
 "titulo": "titulo ate 90 caracteres, chamativo, com REACT e o gancho da historia (pode ter 1 emoji)",
 "titulos_alternativos": ["outro titulo", "outro titulo"],
 "descricao": "4 a 7 linhas: do que se trata a historia e o react, pergunta para o publico, chamada para se inscrever",
 "capitulos": [{{"t": 0, "titulo": "Comeco"}}],
 "tags": ["15 a 25 tags curtas sem #"],
 "hashtags": ["#manhwa", "#react", "#tema"],
 "comentario_fixado": "pergunta curta que gera resposta",
 "thumb_texto": "2 a 5 PALAVRAS de impacto",
 "thumb_t": 123.4
}}
Regras:
- "capitulos": 5 a 12, o primeiro em t=0, pelo menos 60 s entre eles, nomes curtos dos acontecimentos da historia ou das reacoes fortes.
- "thumb_t": segundos de um momento de reacao forte do CRIADOR (cara expressiva), longe do comeco.
- Seguranca de monetizacao: no titulo, descricao e tags evite matar, morte, morrer, sexo, nu, droga, arma, suicidio, sangue (use eufemismos).
- Nao invente fatos: use a transcricao."""


def _hms(t):
    t = int(round(t))
    h, m, s = t // 3600, t % 3600 // 60, t % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def _capitulos(caps, dur):
    """YouTube: comeca em 00:00, minimo 3 capitulos, >= 10 s cada."""
    out = []
    for c in sorted(caps or [], key=lambda c: float(c.get("t", 0))):
        try:
            t = max(0.0, min(float(c["t"]), dur - 15))
        except Exception:  # noqa: BLE001
            continue
        if out and t - out[-1][0] < 30:
            continue
        out.append((t, str(c.get("titulo") or "").strip()[:60] or "Parte"))
    if out:
        out[0] = (0.0, out[0][1])
    return out if len(out) >= 3 else []


def _cover(img, w, h, cx=0.5, cy=0.5):
    """Preenche w x h sem distorcer, centrando o recorte no ponto (cx, cy) dado em fracao da imagem de origem."""
    sw, sh = img.size
    esc = max(w / sw, h / sh)
    nw, nh = int(sw * esc + 0.5), int(sh * esc + 0.5)
    img = img.resize((nw, nh), Image.LANCZOS)
    x = int(min(max(cx * nw - w / 2, 0), nw - w))
    y = int(min(max(cy * nh - h / 2, 0), nh - h))
    return img.crop((x, y, x + w, y + h))


def thumb_deitada(cfg, video, t, layout, texto, out_path, cor="#FF2D55"):
    """1280x720: painel do conteudo a esquerda, rosto do criador grande a direita, texto em baixo."""
    src = TH._frame(video, t)
    if src is None:
        return None
    W, H = 1280, 720
    canvas = Image.new("RGB", (W, H), (12, 12, 16))
    wx0, wy0, wx1, wy1 = layout["webcam"]
    cont_w = 760
    # conteudo: regiao do quadro fora da janela da webcam, centrada no meio do video
    lim = wx0 if wx0 > layout["width"] / 2 else layout["width"]
    cont = src.crop((0, 0, lim, layout["height"]))
    canvas.paste(_cover(cont, cont_w, H, cx=min(1.0, (layout["width"] / 2) / lim)), (0, 0))
    cam = src.crop((wx0, wy0, wx1, wy1))
    face = _cover(cam, W - cont_w, H, cx=0.5, cy=0.35)
    canvas.paste(face, (cont_w, 0))
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([cont_w - 4, 0, cont_w + 4, H], fill=TH._hex(cor))
    fonts = Path(cfg["paths"]["assets"]) / "fonts"
    try:
        font = ImageFont.truetype(str(fonts / cfg.get("thumb", {}).get("font", "LuckiestGuy-Regular.ttf")), 96)
    except Exception:  # noqa: BLE001
        font = ImageFont.truetype("C:/Windows/Fonts/impact.ttf", 96)
    if texto:
        linhas = TH._wrap(draw, texto.upper(), font, cont_w - 60)[:3]
        lh = int(font.size * 1.08)
        y0 = H - 40 - lh * len(linhas)
        sombra = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sombra).rectangle([0, y0 - 30, cont_w, H], fill=(0, 0, 0, 120))
        canvas = Image.alpha_composite(canvas.convert("RGBA"), sombra.filter(ImageFilter.GaussianBlur(8))).convert("RGB")
        draw = ImageDraw.Draw(canvas)
        for i, ln in enumerate(linhas):
            draw.text((36, y0 + i * lh), ln, font=font, fill=TH._hex(cor), stroke_width=9, stroke_fill=(0, 0, 0))
    canvas.save(out_path, quality=92)
    log(f"thumb grande: {Path(out_path).name} (t={t:.1f}s)")
    return out_path


def empacotar(cfg, video, use_llm=True, force=False):
    from .pipeline import slugify, _cached, _channel
    from . import base as BASE
    video = Path(video)
    slug = slugify(video.stem)
    work = Path(cfg["paths"]["work"]) / slug
    work.mkdir(parents=True, exist_ok=True)
    log(f"=== GRANDE {video.name}")
    info = _cached(work / "probe.json", lambda: P.probe(cfg, video), force)
    layout = _cached(work / "layout.json", lambda: P.detect_layout(cfg, video), force)
    dur = info["duration"]

    # audio: o mesmo raw/clean do pipeline (cache compartilhado com os cortes)
    raw_wav, clean_wav = work / "raw.wav", work / "clean.wav"
    if force or not raw_wav.exists():
        A.extract_wav(cfg, video, raw_wav)
    if force or not clean_wav.exists():
        A.clean_audio(cfg, raw_wav, clean_wav)
    tx = _cached(work / "transcript.json", lambda: T.transcribe(cfg, clean_wav), force)
    words, segments = tx["words"], tx["segments"]
    for s in segments:
        s["words"] = [w for w in words if s["start"] - 0.01 <= w["s"] <= s["end"] + 0.01]
    base_info = None
    achado = BASE.achar_base(cfg, words)
    if achado:
        BASE.marcar_narracao(words, segments, achado[2]["words"])
        base_info = {"id": achado[1].get("id"), "titulo": achado[1].get("titulo"), "canal": achado[1].get("canal"), "url": achado[1].get("url")}

    # audio final: video inteiro, so nivelado
    final_wav = work / "grande_audio.wav"
    if force or not final_wav.exists():
        A.loudnorm_two_pass(cfg, raw_wav, final_wav)

    meta_path = work / "grande_meta.json"
    meta = load_json(meta_path) if meta_path.exists() and not force else None
    if meta is None and use_llm:
        chans = cfg.get("channels") or []
        base_txt = ""
        if base_info:
            base_txt = f"Video reagido: \"{base_info['titulo']}\" do canal {base_info['canal']} ({base_info['url']}).\n"
        if (cfg.get("forcar") or {}).get("contexto"):  # ex.: aula do dono (mr/temas.py)
            base_txt += cfg["forcar"]["contexto"] + "\n"
        instr = INSTRUCOES.format(dur_min=dur / 60, base=base_txt, canais="\n".join(f"- {c['slug']} - {c.get('niche', '')}" for c in chans))
        meta = ask_json(cfg, instr, "TRANSCRICAO:\n" + ED.transcript_text(segments), timeout=600)
        if meta:
            save_json(meta, meta_path)
    meta = meta or {"titulo": f"REACT {video.stem}", "descricao": "", "tags": ["react", "manhwa"], "hashtags": ["#react", "#manhwa"],
                    "capitulos": [], "thumb_texto": "", "thumb_t": dur / 3}
    channel = _channel(cfg, (cfg.get("forcar") or {}).get("canal") or meta.get("channel") or "manhwareact")

    caps = _capitulos(meta.get("capitulos"), dur)
    desc = (meta.get("descricao") or "").strip()
    if base_info:
        desc += f"\n\nVideo original: {base_info['titulo']} - {base_info['canal']}\n{base_info['url']}"
    if caps:
        desc += "\n\nCapitulos:\n" + "\n".join(f"{_hms(t)} {nome}" for t, nome in caps)
    hashtags = [h if str(h).startswith("#") else "#" + str(h) for h in (meta.get("hashtags") or [])]
    if hashtags:
        desc += "\n\n" + " ".join(hashtags)

    dest = Path(cfg["paths"].get("ready_grandes", Path(cfg["paths"]["ready"]).parent / "grandes")) / channel["slug"]
    dest.mkdir(parents=True, exist_ok=True)
    out_mp4 = dest / f"{slug}.mp4"
    log(f"grande: montando o video inteiro ({dur / 60:.1f} min, video copiado + audio nivelado)")
    ffmpeg(cfg, ["-i", str(video), "-i", str(final_wav), "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                 "-movflags", "+faststart", "-shortest", str(out_mp4)])
    thumb = None
    try:
        t_th = float(meta.get("thumb_t") or dur / 3)
        if not (5 < t_th < dur - 5):
            t_th = dur / 3
        from . import capa as CAPA
        genero = CAPA.genero_de(meta.get("titulo"), meta.get("thumb_texto"), " ".join(map(str, meta.get("tags") or [])))
        thumb = CAPA.capa_grande(cfg, video, layout, 0, dur, meta.get("thumb_texto") or "", channel.get("color", "#FF2D55"),
                                 dest / f"{slug}_thumb.jpg", work=work, genero=genero)
        if not thumb:
            thumb = thumb_deitada(cfg, video, t_th, layout, meta.get("thumb_texto") or "", dest / f"{slug}_thumb.jpg", channel.get("color", "#FF2D55"))
    except Exception as e:  # noqa: BLE001
        log(f"thumb grande falhou ({e})")
    tags = [str(t).strip().lstrip("#") for t in (meta.get("tags") or []) if str(t).strip()]
    postar = {"arquivo": out_mp4.name, "categoria": "react", "tipo": "completo", "titulo": (meta.get("titulo") or "")[:100],
              "descricao": desc[:5000], "tags": tags, "tags_texto": ", ".join(tags), "hashtags": hashtags,
              "thumb": f"{slug}_thumb.jpg" if thumb else None, "comentario_fixado": meta.get("comentario_fixado") or "",
              "thumbs_ab": [p.name for p in CAPA.caminhos_ab(thumb)] if thumb else [],
              "titulos_alternativos": meta.get("titulos_alternativos") or [], "obra": meta.get("obra"),
              "canais": [channel["name"]], "canal_slug": channel["slug"], "video_base": base_info,
              "publish_at": None, "privacy": "private", "made_for_kids": False, "pronto": True}
    if (cfg.get("forcar") or {}).get("canal"):
        postar.update({"canal_fixo": channel["slug"], "manter_texto": True})
    save_json(postar, dest / f"{slug}.postar.json")
    linhas = [f"TITULO:\n{postar['titulo']}", "", "TITULOS ALTERNATIVOS:", *[f"- {x}" for x in postar["titulos_alternativos"]], "",
              f"DESCRICAO:\n{postar['descricao']}", "", f"TAGS:\n{postar['tags_texto']}", "", f"COMENTARIO FIXADO:\n{postar['comentario_fixado']}"]
    (dest / f"{slug}_meta.txt").write_text("\n".join(linhas), encoding="utf-8")
    log(f"GRANDE pronto: {out_mp4} | {postar['titulo']}")
    return {"mp4": str(out_mp4), "titulo": postar["titulo"], "canal": channel["slug"], "capitulos": len(caps), "base": base_info}
