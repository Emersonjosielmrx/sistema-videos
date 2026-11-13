# -*- coding: utf-8 -*-
"""cta_card: gera o CARD de CTA premium (1080x1920) por produto, com cache.

  - fundo IA cinematografico (OmniRoute/Pollinations) com overlay pra legibilidade
  - tipografia forte com quebra de linha automatica (nao estoura a largura)
  - CACHE por (produto + versao layout + contato): gera 1x, reusa sempre

SEM CONTATO NA TELA (16/10/2026, item IM-01 de docs\\PLANO_MELHORIAS_VEO.md).
Ate 15/10 este card desenhava, em TODO video, o numero de WhatsApp (escrito aqui no
codigo) e o endereco do site. Em 04/09/2026 o YouTube suspendeu 22 canais por spam e
praticas enganosas, e esse slide esta entre as causas apontadas
(D:\\postador-de-videos\\SPAM_BANIMENTO_2026-09-04.md e LEIA.txt). A politica de spam
do YouTube trata contato e redirecionamento para fora da plataforma tambem quando
aparecem como TEXTO NA TELA, nao so em link.

Agora o card leva: nome do produto + um beneficio curto + um convite sem contato
("link no perfil"). Telefone e endereco ficam na aba Sobre do canal e no site.

A variante com contato existe so para fora do YouTube (TikTok/Instagram) e NAO e
usada por ninguem por padrao: e preciso passar contato="..." de proposito.
Quem monta o video (montar_final.py, cta_builder.py) nunca passa esse parametro.

Uso:
    from cta_card import gerar_card
    png = gerar_card(produto_dict)                      # YouTube: sem contato
    png = gerar_card(produto_dict, contato="91 ...")    # so TikTok/Instagram
"""
import hashlib
import os
import sys
import textwrap
from pathlib import Path

_BASE = Path(__file__).resolve().parent.parent          # D:\veo\beta
_CACHE = _BASE / "pos_producao" / "cta_cache_cards"
_CACHE.mkdir(parents=True, exist_ok=True)
_FUNDO_CACHE = _BASE / "pos_producao" / "propaganda_cache_fundo"
_FUNDO_CACHE.mkdir(parents=True, exist_ok=True)

# v5 (16/10/2026): sem telefone e sem endereco na tela. O bump invalida o cache:
# os cards v4 em cta_cache_cards/ ainda tem o numero de WhatsApp desenhado e NAO
# podem ser reusados.
# v6 (16/10/2026, noite): beneficio em branco com contorno (na cor do produto ele sumia no fundo da mesma cor).
_LAYOUT_VER = "v6"
# Convite que substitui o badge de contato. Sem telefone, sem URL, sem @.
_CONVITE_PADRAO = "LINK NO PERFIL"
_OMNIROUTE_DISABLED = os.environ.get("OMNIROUTE_DISABLED", "0") == "1"

# ---------------------------------------------------------------------------
# BANCO DE VARIANTES VISUAIS — a dona pediu "grava 10 ou 20 diferentes e fica
# repetindo": a VOZ/TEXTO nao mudam (banco de vozes cuida disso), so o VISUAL.
# Cada variante e um conjunto de knobs (posicao, fundo, vinheta, faixa, badge).
# A escolha e por STEM (md5) -> reproduzivel e alterna de video pra video.
# Cada (produto, variante) gera 1x e fica no cache = banco de cards.
# ---------------------------------------------------------------------------
_ESTILOS_FUNDO = [
    "premium abstract cinematic background, soft neon glow, elegant bokeh particles",
    "dark moody studio backdrop, dramatic rim light, subtle smoke, high-end",
    "clean minimalist gradient, geometric soft shapes, modern tech aesthetic",
    "luxury 3d fluid waves, glossy metallic reflections, depth of field",
    "futuristic grid horizon, glowing particles rising, deep space vibe",
    "warm cinematic light rays through fog, premium lens flare, soft focus",
]
_VARIANTES = [
    # y_nome: fracao vertical do NOME | vinheta: forca base | faixa_topo px
    # badge_cor: cor da pilula do zap | fundo_idx: estilo de fundo IA
    {"y_nome": 0.30, "vinheta": 210, "faixa": 18, "badge": (37, 211, 102), "fundo": 0, "y_zap": 0.76, "y_handle": 0.90},
    {"y_nome": 0.34, "vinheta": 180, "faixa": 0,  "badge": (37, 211, 102), "fundo": 1, "y_zap": 0.72, "y_handle": 0.92},
    {"y_nome": 0.28, "vinheta": 230, "faixa": 26, "badge": (255, 107, 107), "fundo": 2, "y_zap": 0.78, "y_handle": 0.90},
    {"y_nome": 0.32, "vinheta": 200, "faixa": 12, "badge": (37, 211, 102), "fundo": 3, "y_zap": 0.74, "y_handle": 0.91},
    {"y_nome": 0.36, "vinheta": 160, "faixa": 22, "badge": (91, 108, 255),  "fundo": 4, "y_zap": 0.80, "y_handle": 0.93},
    {"y_nome": 0.30, "vinheta": 220, "faixa": 0,  "badge": (37, 211, 102), "fundo": 5, "y_zap": 0.76, "y_handle": 0.90},
    {"y_nome": 0.26, "vinheta": 240, "faixa": 30, "badge": (255, 169, 77),  "fundo": 0, "y_zap": 0.72, "y_handle": 0.89},
    {"y_nome": 0.33, "vinheta": 190, "faixa": 16, "badge": (37, 211, 102), "fundo": 2, "y_zap": 0.78, "y_handle": 0.92},
    {"y_nome": 0.31, "vinheta": 205, "faixa": 20, "badge": (167, 139, 250), "fundo": 3, "y_zap": 0.75, "y_handle": 0.90},
    {"y_nome": 0.29, "vinheta": 215, "faixa": 14, "badge": (37, 211, 102), "fundo": 1, "y_zap": 0.77, "y_handle": 0.91},
    {"y_nome": 0.35, "vinheta": 170, "faixa": 24, "badge": (244, 114, 182), "fundo": 4, "y_zap": 0.79, "y_handle": 0.93},
    {"y_nome": 0.27, "vinheta": 235, "faixa": 18, "badge": (37, 211, 102), "fundo": 5, "y_zap": 0.73, "y_handle": 0.89},
]


def escolher_variante(stem: str = "") -> int:
    """Indice da variante visual do card, estavel por stem (md5)."""
    return int(hashlib.md5((stem or "x").encode("utf-8")).hexdigest(), 16) % len(_VARIANTES)

sys.path.insert(0, str(_BASE / "pos_producao"))


def _hex_rgb(h, default=(37, 211, 102)):
    try:
        h = h.lstrip("#")
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    except Exception:
        return default


def _fundo_ia(cor_rgb, tema, w, h, estilo_idx=0):
    """Gera/reusa fundo IA cinematografico. None se indisponivel.
    estilo_idx: escolhe um dos _ESTILOS_FUNDO (variacao visual do banco)."""
    if _OMNIROUTE_DISABLED:
        return None
    estilo = _ESTILOS_FUNDO[estilo_idx % len(_ESTILOS_FUNDO)]
    chave = f"cta|{tema}|{cor_rgb}|{w}x{h}|{_LAYOUT_VER}|e{estilo_idx}"
    cache = _FUNDO_CACHE / f"{hashlib.md5(chave.encode()).hexdigest()[:16]}.png"
    if cache.exists() and cache.stat().st_size > 5000:
        return cache
    cor_nome = {
        (37, 211, 102): "vibrant emerald green", (255, 107, 107): "warm coral red",
        (78, 205, 196): "turquoise teal", (91, 108, 255): "electric blue",
        (255, 169, 77): "warm orange", (167, 139, 250): "deep violet",
        (244, 114, 182): "vivid pink", (248, 113, 113): "soft red",
        (16, 185, 129): "emerald green",
    }.get(cor_rgb, "dark teal")
    prompt = (
        f"Vertical {w}x{h} {estilo}, {cor_nome} palette, smooth gradient, "
        f"depth of field, minimalist high-end tech aesthetic, no text, no "
        f"characters, no logos, clean professional advertising background"
    )
    try:
        from omniroute_image import _generate  # type: ignore
        if _generate(prompt, cache) and cache.exists() and cache.stat().st_size > 5000:
            return cache
    except Exception:
        pass
    try:
        cache.unlink(missing_ok=True)
    except Exception:
        pass
    return None


def _fit_font(draw, texto, font_loader, alvo_px, max_size, min_size, stroke=0):
    """Acha o maior fontsize <= max_size cujo texto cabe em alvo_px de largura."""
    size = max_size
    while size > min_size:
        f = font_loader(size)
        bbox = draw.textbbox((0, 0), texto, font=f, stroke_width=stroke)
        if (bbox[2] - bbox[0]) <= alvo_px:
            return f, size
        size -= 4
    return font_loader(min_size), min_size


def _draw_center(draw, cx, y, texto, font, fill, stroke=0, stroke_fill=(0, 0, 0)):
    bbox = draw.textbbox((0, 0), texto, font=font, stroke_width=stroke)
    tw = bbox[2] - bbox[0]
    draw.text((cx - tw // 2 - bbox[0], y - bbox[1]), texto, font=font,
              fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
    return bbox[3] - bbox[1]  # altura


def gerar_card(produto: dict, w=1080, h=1920, force=False, stem="", variante=None,
               contato: str = "") -> Path:
    """Gera (ou reusa do cache) o PNG do card de CTA do produto.

    variante: indice do banco visual (_VARIANTES). Se None, escolhe por stem
      (md5) -> alterna de video pra video mas cada (produto,variante) grava 1x.
    stem: usado pra escolher a variante quando variante=None.
    contato: NAO USE para video de YouTube. Vazio (padrao) = card sem telefone e
      sem endereco, so com o convite. Preenchido = desenha o contato na pilula;
      existe so para TikTok/Instagram e precisa ser passado de proposito
      (ver o cabecalho deste arquivo e o item IM-01 do plano)."""
    from PIL import Image, ImageDraw, ImageFilter
    from subtitles_veo import _load_font

    pid = produto.get("id", "generico")
    if variante is None:
        variante = escolher_variante(stem)
    var = _VARIANTES[variante % len(_VARIANTES)]
    contato = (contato or "").strip()
    # o contato entra na chave do cache: card com e sem contato sao arquivos diferentes
    chave = f"{pid}|{_LAYOUT_VER}|{w}x{h}|var{variante}|c{contato}"
    sufixo = "_contato" if contato else ""
    out_png = _CACHE / f"{hashlib.md5(chave.encode()).hexdigest()[:16]}_{pid}_v{variante}{sufixo}.png"
    if out_png.exists() and out_png.stat().st_size > 5000 and not force:
        return out_png

    cor_rgb = _hex_rgb(produto.get("cor", "#25D366"))
    nome = produto.get("nome", "Inovare IA")
    # IM-05 (16/10): o texto tambem varia com a variante (antes todo card do produto dizia o mesmo cta_curto): o
    # cta_curto ou a 1a frase do cta_longo, se curta e sem nada que pareca contato (digitos, @, link, {marcador})
    import re as _re
    copias = [produto.get("cta_curto") or nome]
    frase = _re.split(r"(?<=[.!?])\s", (produto.get("cta_longo") or "").strip())[0].strip().rstrip(".")
    if frase and len(frase) <= 52 and frase not in copias and not _re.search(r"\d{4,}|@|http|www\.|\{", frase):
        copias.append(frase)
    copy = copias[variante % len(copias)]
    # pilula do rodape: o contato so aparece quando pedido de proposito (TikTok/
    # Instagram); no YouTube fica o convite, sem telefone e sem endereco.
    pilula = contato or (produto.get("convite") or _CONVITE_PADRAO)
    tema = produto.get("descricao", nome)

    # --- fundo: IA se der, senao gradiente diagonal ---
    fundo = _fundo_ia(cor_rgb, tema, w, h, estilo_idx=var["fundo"])
    if fundo:
        try:
            img = Image.open(fundo).convert("RGB").resize((w, h), Image.LANCZOS)
        except Exception:
            fundo = None
    if not fundo:
        img = Image.new("RGB", (w, h), cor_rgb)
        grad = ImageDraw.Draw(img)
        c2 = tuple(max(0, int(c * 0.35)) for c in cor_rgb)
        for y in range(h):
            f = y / h
            grad.line([(0, y), (w, y)],
                      fill=tuple(int(cor_rgb[i] * (1 - f) + c2[i] * f) for i in range(3)))

    img = img.convert("RGBA")

    # --- vinheta escura (topo+base mais escuros pra copy destacar) ---
    vin = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    vd = ImageDraw.Draw(vin)
    for y in range(h):
        # escurece topo (0-15%) e base (65-100%)
        a = 0
        if y < h * 0.15:
            a = int(120 * (1 - y / (h * 0.15)))
        elif y > h * 0.60:
            a = int(var["vinheta"] * ((y - h * 0.60) / (h * 0.40)))
        if a:
            vd.line([(0, y), (w, y)], fill=(0, 0, 0, a))
    img.alpha_composite(vin)
    draw = ImageDraw.Draw(img)
    cx = w // 2

    # --- faixa de cor fina no topo (identidade do produto; variante pode zerar) ---
    if var["faixa"] > 0:
        draw.rectangle([0, 0, w, var["faixa"]], fill=cor_rgb + (255,))

    y_nome = var["y_nome"]
    # (o selo "OFERECIDO POR" saiu em 16/10: repetia em todo video e so ocupava
    #  espaco; o que vende e o nome do produto + o beneficio.)

    # --- NOME do produto (grande, auto-fit) ---
    f_nome, _ = _fit_font(draw, nome, _load_font, w - 140, 150, 70, stroke=10)
    hnome = _draw_center(draw, cx, int(h * y_nome), nome, f_nome,
                         (255, 255, 255), stroke=10, stroke_fill=(0, 0, 0))

    # --- COPY (quebra em ate 2 linhas, auto-fit) ---
    linhas = textwrap.wrap(copy, width=26)[:2]
    f_copy, _ = _fit_font(draw, max(linhas, key=len) if linhas else copy,
                          _load_font, w - 160, 64, 40, stroke=6)
    y = int(h * y_nome) + hnome + 60
    for ln in linhas:
        # v6 (16/10): branco com contorno, nao a cor do produto - o fundo e tingido com a MESMA cor e o beneficio
        # sumia (verde sobre verde no card do Hermes Call, quadros conferidos)
        hln = _draw_center(draw, cx, y, ln, f_copy, (255, 255, 255),
                           stroke=6, stroke_fill=(0, 0, 0))
        y += hln + 24

    # --- PILULA do rodape: convite (padrao) ou contato (so fora do YouTube) ---
    # Com contato, mantem o icone redondo a esquerda; sem contato e so o texto
    # centralizado, porque nao ha para onde "ligar".
    f_zap, _ = _fit_font(draw, pilula, _load_font, w - 360, 82, 50, stroke=0)
    bbox = draw.textbbox((0, 0), pilula, font=f_zap)
    zw, zh = bbox[2] - bbox[0], bbox[3] - bbox[1]
    icon_r = int(zh * 0.7) if contato else 0
    gap = 34 if contato else 0
    pad_x, pad_y = 60, 34
    total_w = icon_r * 2 + gap + zw
    bx0 = cx - total_w // 2 - pad_x
    bx1 = cx + total_w // 2 + pad_x
    by = int(h * var["y_zap"])
    by0, by1 = by - pad_y, by + zh + pad_y
    rad = (by1 - by0) // 2
    draw.rounded_rectangle([bx0, by0, bx1, by1], radius=rad, fill=var["badge"] + (255,))
    if contato:
        icx = bx0 + pad_x + icon_r
        icy = (by0 + by1) // 2
        draw.ellipse([icx - icon_r, icy - icon_r, icx + icon_r, icy + icon_r],
                     fill=(255, 255, 255))
        fr = int(icon_r * 0.5)
        draw.ellipse([icx - fr, icy - fr, icx + fr, icy + fr], outline=var["badge"],
                     width=max(4, icon_r // 6))
        draw.text((icx + icon_r + gap, icy - zh // 2 - bbox[1]), pilula,
                  font=f_zap, fill=(255, 255, 255))
    else:
        _draw_center(draw, cx, by, pilula, f_zap, (255, 255, 255))

    # (o endereco do site saia aqui na base ate 15/10. Saiu junto com o telefone:
    #  endereco na tela tambem conta como redirecionar para fora. Site e contato
    #  ficam na aba Sobre do canal.)

    img.convert("RGB").save(out_png, "PNG")
    return out_png


if __name__ == "__main__":
    import json
    cat = json.loads((_BASE / "pos_producao" / "assets" / "produtos.json").read_text(encoding="utf-8"))
    prods = cat.get("produtos", [])[:4]
    for p in prods:
        png = gerar_card(p, force=True)
        print(f"  {p['id']:14} -> {png} ({png.stat().st_size//1024}KB)")
