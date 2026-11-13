# -*- coding: utf-8 -*-
"""promos.py — Camada de propaganda pós-produção.

Insere um CARD FINAL nos últimos N segundos do vídeo promovendo produtos da
Inovare Inteligência Artificial. O card é um PNG 1080x1920 transparente
gerado via fx_subtitles._text_block_png() (mesmo motor das legendas karaoke,
zero risco de quebrar nada) e sobreposto via ffmpeg overlay.

PRODUTOS (6 — Hermes Call é o principal e tem 2x mais chance na rotação
porque vende mais e atende o publico principal do canal @InovareStories):

  1. Hermes Call    -> principal. Liga pros leads via WhatsApp em 24h
  2. Avatar IA      -> cria seu avatar que posta sozinho nas redes
  3. SuperChat      -> atende Whats+Insta+Telegram com 1 agente só
  4. Follow-up      -> follow-up de vendas automático
  5. Agenda IA      -> agendamento com IA sem no-show
  6. Vitrine IA     -> dá ao bot o conhecimento da sua loja

COMO LIGAR/DESLIGAR (sem mexer em codigo):
  - config/settings.json: "promo_mode" =
        "off"            -> nunca aparece
        "fixed:hermes"   -> sempre Hermes Call (principal)
        "rotate"         -> rotaciona os 6 com peso (Hermes 2x)
        "rotate_pesado"  -> idem mas aparece em 100% dos videos
    default: "rotate" (80% dos videos recebem card — 20% sao "limpos" pra
    nao cansar)

  - HERMES_CTA=1 no env tambem liga o card fixo Hermes (legado).

IMPLEMENTACAO:
  - render_cta_card(produto, dur=6) -> gera o PNG e devolve path
  - promo_pick(mode, rng=random)    -> escolhe o produto do video
  - patch_story_pipeline            -> hook a ser chamado DEPOIS do watermark
"""
import os
import json
import random
from pathlib import Path

from fx_subtitles import _text_block_png

# ============================================================
# CATALOGO
# ============================================================

# peso 2 = aparece 2x mais na roleta. "frases" sao as 2 linhas do card.
PROMOS = [
    {
        "id": "hermes",
        "peso": 2,
        "titulo": "HERMES CALL",
        "tagline": "Ligue pros seus leads em 24h",
        "cta": "wa.me/5591984698653",
        "cor": (37, 211, 102),   # verde WhatsApp oficial
        "url_label": "WhatsApp",
        "screenshot": "hermes_dash.png",   # print do dashboard (assets/promo/)
    },
    {
        "id": "avatar",
        "peso": 1,
        "titulo": "AVATAR IA",
        "tagline": "Seu rosto. Postando sozinho.",
        "cta": "inovareinteligenciaartificial.com",
        "cor": (180, 70, 255),    # roxo IA
        "url_label": "Site",
    },
    {
        "id": "superchat",
        "peso": 1,
        "titulo": "SUPERCHAT",
        "tagline": "Whats + Insta + Telegram com 1 agente",
        "cta": "superchat.inovareinteligenciaartificial.com",
        "cor": (0, 180, 255),     # azul canal
        "url_label": "Site",
    },
    {
        "id": "followup",
        "peso": 1,
        "titulo": "FOLLOW-UP IA",
        "tagline": "Follow-up de vendas no automatico",
        "cta": "follow-up.inovareinteligenciaartificial.com",
        "cor": (255, 140, 0),     # laranja conversao
        "url_label": "Site",
    },
    {
        "id": "agenda",
        "peso": 1,
        "titulo": "AGENDA IA",
        "tagline": "Agendamento automatico, sem no-show",
        "cta": "agenda.inovareinteligenciaartificial.com",
        "cor": (255, 90, 90),     # vermelho compromisso
        "url_label": "Site",
    },
    {
        "id": "vitrine",
        "peso": 1,
        "titulo": "VITRINE IA",
        "tagline": "De ao bot o conhecimento da sua loja",
        "cta": "vitrine.inovareinteligenciaartificial.com",
        "cor": (255, 200, 0),     # amarelo vitrine
        "url_label": "Site",
    },
]


# ============================================================
# MODO / SELECAO
# ============================================================

def _modo():
    """Le o modo: settings.json > env > default 'rotate'."""
    try:
        cfg = Path(__file__).resolve().parent.parent / "config" / "settings.json"
        if cfg.exists():
            v = json.loads(cfg.read_text(encoding="utf-8")).get("promo_mode")
            if v:
                return v
    except Exception:
        pass
    if os.environ.get("HERMES_CTA", "0") == "1":
        return "fixed:hermes"
    return "rotate"


def promo_pick(mode=None, rng=None):
    """Escolhe o produto do video conforme o modo. None = sem propaganda.

    Modos:
      "off"            -> None sempre
      "fixed:<id>"     -> sempre o produto com esse id (ex: fixed:hermes)
      "rotate"         -> 80% tem propaganda, senao None
      "rotate_pesado"  -> 100% tem propaganda
    """
    if mode is None:
        mode = _modo()
    rng = rng or random
    if mode == "off":
        return None
    if mode.startswith("fixed:"):
        wanted = mode.split(":", 1)[1]
        for p in PROMOS:
            if p["id"] == wanted:
                return p
        return PROMOS[0]   # fallback
    # rotacao ponderada
    if mode == "rotate" and rng.random() > 0.80:
        return None
    ids = [p["id"] for p in PROMOS]
    pesos = [p["peso"] for p in PROMOS]
    return rng.choices(PROMOS, weights=pesos, k=1)[0]


# ============================================================
# CTA CONTEXTUAL (opcional, via LLM)
# ============================================================

def _cta_contextual_ligado():
    """Le config/settings.json:promo_cta_contextual (default False)."""
    try:
        cfg = Path(__file__).resolve().parent.parent / "config" / "settings.json"
        if cfg.exists():
            return bool(json.loads(cfg.read_text(encoding="utf-8"))
                        .get("promo_cta_contextual", False))
    except Exception:
        pass
    return os.environ.get("PROMO_CTA_CONTEXTUAL", "0") == "1"


def tagline_contextual(produto, genero=None, tema=None, timeout=60):
    """Gera uma tagline curta conectando a EMOCAO da historia ao produto,
    via o mesmo gateway do viral_crew. Ex: historia de reencontro + Hermes
    -> 'Nao perca o contato que importa. Hermes Call liga por voce.'

    Retorna a tagline (str) ou a tagline fixa do produto se falhar/desligado.
    Nunca levanta — a producao nao pode travar por causa disso."""
    fixa = produto["tagline"]
    if not _cta_contextual_ligado() or not (genero or tema):
        return fixa
    try:
        import viral_crew
        client = viral_crew._client()
        if client is None:
            return fixa
        sys_prompt = (
            "Voce e um copywriter de anuncios curtos. Dada a EMOCAO de uma "
            "historia e um PRODUTO, escreva UMA frase de ate 60 caracteres que "
            "conecta a emocao ao beneficio do produto, de forma natural (sem "
            "'compre ja'). Responda SO a frase, sem aspas, uma linha."
        )
        user = (
            f"Historia: genero={genero}, tema={tema}.\n"
            f"Produto: {produto['titulo']} — {produto['tagline']} "
            f"(publico: donos de negocio no WhatsApp).\n"
            "Escreva a frase."
        )
        # max_tokens alto porque o gemini-2.5-flash gasta tokens em
        # reasoning_content antes do texto — 80 truncava a frase.
        txt, _dt = viral_crew._stream_chat(client, sys_prompt, user,
                                           temperature=0.9, max_tokens=500,
                                           timeout=timeout)
        if txt:
            frase = txt.strip().strip('"').strip("'").split("\n")[0].strip()
            if 8 <= len(frase) <= 70:
                return frase
    except Exception:
        pass
    return fixa


# ============================================================
# RENDER DO CARD
# ============================================================

def render_cta_card(produto, dur=6.0, out_path=None, tagline_override=None):
    """Gera o PNG 1080x1920 com a propaganda. Retorna path do PNG.

    tagline_override: se passado, usa no lugar da tagline fixa (ex: a
    tagline contextual gerada por LLM).

    Layout:
      [fundo preto 78% ocupando todo o frame — destaca no final]
      [ HERMES CALL ]                       <- titulo, cor da marca, 130
      [espaco]
      Ligue pros seus leads em 24h          <- tagline, branco, 55
      [espaco grande]
      >>> WhatsApp: wa.me/5591984698653     <- CTA, branco, 50
      [espaco]
      @InovareStories                       <- handle, cinza, 38
    """
    from PIL import Image, ImageDraw
    from fx_assets import W, H
    from fx_subtitles import _text_block_png

    if out_path is None:
        out_path = Path(os.environ.get("TMP_DIR", ".")) / f"cta_{produto['id']}.png"
    out_path = Path(out_path)

    cor = produto["cor"]
    title = produto["titulo"]
    tagline = tagline_override or produto["tagline"]
    cta_url = produto["cta"]
    url_label = produto["url_label"]

    # screenshot do produto (opcional) — se existir em assets/promo/
    shot_path = None
    shot_name = produto.get("screenshot")
    if shot_name:
        cand = Path(__file__).resolve().parent.parent / "assets" / "promo" / shot_name
        if cand.exists():
            shot_path = cand

    # se tem screenshot, o texto sobe (0.30) pra abrir espaco embaixo; senao centra
    y_frac = 0.30 if shot_path else 0.5

    # 1) gera o bloco de texto (PNG transparente)
    tmp_text_png = out_path.with_suffix(".text.png")
    _text_block_png(
        out_png=str(tmp_text_png),
        lines_styles=[
            (title, 130, cor),
            ("", 30, (255, 255, 255)),
            (tagline, 55, (255, 255, 255)),
            ("", 50, (255, 255, 255)),
            (f">>> {url_label}: {cta_url}", 50, (255, 255, 255)),
            ("", 30, (255, 255, 255)),
            ("@InovareStories", 38, (180, 180, 180)),
        ],
        y_center_frac=y_frac,
    )

    # 2) compoe com fundo preto 78% (destaca mesmo em video claro)
    bg = Image.new("RGBA", (W, H), (0, 0, 0, 200))

    # 2b) screenshot num quadro com borda da cor da marca (metade inferior)
    if shot_path:
        try:
            shot = Image.open(shot_path).convert("RGBA")
            max_w = int(W * 0.82)
            ratio = max_w / shot.width
            new_h = int(shot.height * ratio)
            # limita altura a ~38% do frame
            if new_h > int(H * 0.38):
                new_h = int(H * 0.38)
                max_w = int(shot.width * (new_h / shot.height))
                if max_w > int(W * 0.82):
                    max_w = int(W * 0.82)
            shot = shot.resize((max_w, new_h), Image.LANCZOS)
            bx = (W - max_w) // 2
            by = int(H * 0.55)
            # moldura: retangulo da cor da marca 6px atras do print
            draw = ImageDraw.Draw(bg)
            pad = 6
            draw.rectangle([bx - pad, by - pad, bx + max_w + pad, by + new_h + pad],
                           fill=(*cor, 255))
            bg.paste(shot, (bx, by), shot)
        except Exception:
            pass

    txt = Image.open(tmp_text_png).convert("RGBA")
    bg.paste(txt, (0, 0), txt)
    bg.save(str(out_path))

    # 3) limpa o temp
    try:
        tmp_text_png.unlink()
    except Exception:
        pass
    return str(out_path)


# ============================================================
# FFMPEG OVERLAY (chamado por story_pipeline.py)
# ============================================================

def burn_cta_card(video_in, video_out, produto, dur=6.0, fade_in=0.4,
                  genero=None, tema=None):
    """Queima o card nos últimos `dur` segundos do video, com fade-in.

    genero/tema: se passados e promo_cta_contextual=true, a tagline vira
    contextual (gerada por LLM conectando a emocao da historia ao produto).

    Idempotente: se ffmpeg falhar, retorna False e o pipeline segue normal.
    """
    if not produto:
        return False
    try:
        # descobre a duracao
        import subprocess, json as _json
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", video_in],
            capture_output=True, text=True, timeout=30,
        )
        total = float(r.stdout.strip() or 0)
        if total <= dur:
            return False
        start = total - dur

        # tagline contextual (opcional) + PNG
        tl = tagline_contextual(produto, genero=genero, tema=tema)
        png = render_cta_card(produto, dur=dur, tagline_override=tl,
                              out_path=Path(video_out).with_suffix(".cta.png"))

        # overlay com fade-in
        cmd = [
            "ffmpeg", "-y", "-i", video_in, "-i", str(png),
            "-filter_complex",
            f"[1:v]format=rgba,fade=t=in:st=0:d={fade_in}:alpha=1[cta];"
            f"[0:v][cta]overlay=0:0:enable='between(t,{start},{total})'",
            "-c:a", "copy", "-shortest", video_out,
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return r.returncode == 0 and Path(video_out).exists() \
            and Path(video_out).stat().st_size > 10000
    except Exception as e:
        print(f"  ! burn_cta_card falhou: {e}")
        return False


# ============================================================
# SMOKE TEST
# ============================================================

if __name__ == "__main__":
    print("modo:", _modo())
    for _ in range(8):
        p = promo_pick()
        print(" ->", p["id"] if p else "(sem promo)")
    print()
    p = PROMOS[0]
    out = render_cta_card(p)
    print("PNG gerado:", out, Path(out).stat().st_size, "bytes")
    # mostra resolução do PNG
    from PIL import Image
    im = Image.open(out)
    print(f"  tamanho: {im.size} modo={im.mode}")
