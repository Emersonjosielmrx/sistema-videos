# -*- coding: utf-8 -*-
"""fx_subtitles.py — TEXTO NA TELA (legendas/karaokê/nametag/watermark) + censura de vídeo legada.
render_subtitles*, burn_subtitles, censurar_video, fontes (_load_font).

Parte do motor de efeitos — mapa completo na fachada effects_engine.py.
Split mecânico verbatim do _PRE_SPLIT_effects_engine.py.bak (2026-07-04).
"""
import json
import random
import subprocess
import os
import re
import unicodedata
from pathlib import Path
from fx_assets import H, QP, W

ULTIMO_MASTER = None  # 04/11: medidas do master feito na junção das fatias (o pipeline pula o master separado)


def _strip_lead_punct(s):
    """Remove QUALQUER pontuação/símbolo/espaço no INÍCIO da string, por categoria
    Unicode — char-agnóstico. Pega vírgula comum (,), fullwidth (，U+FF0C),
    low-9 quote (‚U+201A), ideográfica (、U+3001) e toda variante que exista, sem
    depender de uma lista fixa. Categorias P* (pontuação), S* (símbolo) e Z*/espaço.
    Preserva letras/números (categorias L* e N*)."""
    if not s:
        return s
    i = 0
    for ch in s:
        cat = unicodedata.category(ch)
        if cat[0] in ("P", "S", "Z") or ch.isspace():
            i += 1
        else:
            break
    return s[i:]




# ══════════════════════════════════════════════════════════════════════════
# SEÇÃO 4E: INTRO HOOK + OUTRO CTA (branding)
# ══════════════════════════════════════════════════════════════════════════

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
# SEÇÃO 5B: LEGENDAS QUEIMADAS (estilo Shorts) — Ponto F
# Este ffmpeg não tem libass/drawtext, então renderizamos cada legenda como PNG
# transparente com PIL e sobrepomos via filtro overlay (sem dependências novas).
# ══════════════════════════════════════════════════════════════════════════

# Fontes bold disponíveis no macOS (heavy → bom pra Shorts)
_FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Impact.ttf",
    "/System/Library/Fonts/Supplemental/Arial Black.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Helvetica Bold.ttf",
    "/System/Library/Fonts/Impact.ttf",
    "/Library/Fonts/Impact.ttf",
    "/Library/Fonts/Arial Black.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "/Library/Fonts/Helvetica Bold.ttf",
]

# Fallback de fontes populares em Linux/Windows, se necessário
# (ex: para ambiente Docker ou CI/CD headless)
_FONT_CANDIDATES_FALLBACK = [
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", # Linux
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",        # Linux
    "C:/Windows/Fonts/impact.ttf",                                  # Windows
    "C:/Windows/Fonts/arialbd.ttf",                                 # Windows
]


def _load_font(size):
    from PIL import ImageFont
    # ANIME_SUB_FONT_PNG: fonte da língua (devanágari/tailandês/vietnamita não existem na Impact — viram quadradinho)
    _extra = [os.environ["ANIME_SUB_FONT_PNG"]] if os.environ.get("ANIME_SUB_FONT_PNG") else []
    for fp in _extra + _FONT_CANDIDATES + _FONT_CANDIDATES_FALLBACK:
        if Path(fp).exists():
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _chave_palavra(w):
    return re.sub(r"[^0-9a-zà-ÿ]", "", str(w).lower())


def _alinhar_tempos(words, wt):
    """Tempo REAL de cada palavra da legenda a partir do que a voz devolveu (wt = [[ini, fim, palavra], ...]).
    Antes só valia quando a CONTAGEM batia; bastava a voz partir "Dong-su" em duas, juntar "1.500" ou a fala trocar uma
    palavra do roteiro (anti_ban: "matou" -> "tirou a vida") pra frase inteira cair na estimativa por tamanho da
    palavra — e o karaokê acendia fora do tempo. Agora casa palavra com palavra; onde não casa, reparte só o tempo
    daquele pedaço. Devolve lista do tamanho de words, ou None (pouca coisa casou: fica a estimativa)."""
    try:
        wt = [(float(a), float(b), str(c)) for a, b, c in wt]
    except (TypeError, ValueError):
        return None
    if not words or not wt:
        return None
    if len(wt) == len(words):
        return [[x[0], x[1], w] for x, w in zip(wt, words)]
    import difflib
    a = [_chave_palavra(w) for w in words]
    b = [_chave_palavra(x[2]) for x in wt]
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    iguais = sum(i2 - i1 for tag, i1, i2, _j1, _j2 in sm.get_opcodes() if tag == "equal")
    if iguais < max(1, 0.5 * len(words)):
        return None
    out = [None] * len(words)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                out[i1 + k] = [wt[j1 + k][0], wt[j1 + k][1], words[i1 + k]]
        elif i2 > i1:  # palavras da legenda sem par exato: repartem o tempo do pedaço correspondente da fala
            t0 = wt[j1][0] if j2 > j1 else (wt[j1 - 1][1] if j1 > 0 else wt[0][0])
            t1 = wt[j2 - 1][1] if j2 > j1 else (wt[j1][0] if j1 < len(wt) else wt[-1][1])
            t1 = max(t1, t0)
            pesos = [max(2, len(w)) for w in words[i1:i2]]
            acum, total = 0.0, float(sum(pesos))
            for k, pz in enumerate(pesos):
                ini = t0 + (t1 - t0) * acum / total
                acum += pz
                out[i1 + k] = [round(ini, 3), round(t0 + (t1 - t0) * acum / total, 3), words[i1 + k]]
    return out if all(out) else None


def _wrap_lines(text, font, draw, max_w):
    """Quebra o texto em linhas que cabem em max_w pixels."""
    words = (text or "").strip().replace("\n", " ").split()
    lines, cur = [], ""
    for w in words:
        test = f"{cur} {w}".strip()
        bbox = draw.textbbox((0, 0), test, font=font, stroke_width=8)
        if cur and (bbox[2] - bbox[0]) > max_w:
            lines.append(cur)
            cur = w
        else:
            cur = test
    if cur:
        lines.append(cur)
    return lines[:3]  # no máx 3 linhas


def detect_context(text):
    """T6: detecta o TOM da frase p/ estilo de legenda (porte do SubtitleProcessor do n8n).
    Retorna 'shout'|'whisper'|'thought'|'emphasis'|'normal'. Ordem: emphasis(!!)>shout(!)>
    whisper(...)>thought(*) — !! checado antes de ! pra não virar shout."""
    t = (text or "")
    low = t.lower()
    if "!!" in t or re.search(r"\bimportant|\bcrític|\bcritic|\bvita(?:l|is)\b", low):
        return "emphasis"
    if "!" in t or re.search(r"\bgrit|\bberr|\bem voz alta\b", low):
        return "shout"
    if "..." in t or re.search(r"\bsussurr|\bbaixinho\b|\bem voz baixa\b|\bmurmur", low):
        return "whisper"
    if "*" in t or re.search(r"\bpens(?:a|ou|ava|ando|amento)|\bimagin|\breflet", low):
        return "thought"
    return "normal"


# Estilo por contexto (NOSSO formato PNG, não ASS). (mult_fontsize, cor_RGB|None=branco).
_SUB_CONTEXT_STYLE = {
    "normal":   (1.00, None),
    "shout":    (1.22, None),              # maior, outline forte (tratado no render)
    "whisper":  (0.82, (190, 190, 200)),   # menor, cinza
    "thought":  (0.90, (200, 200, 235)),   # leve azulado (pensamento)
    "emphasis": (1.10, (255, 214, 60)),    # amarelo
}


_BASE_MAX = 0.82  # base da legenda nunca abaixo disto (y 1580/1920 = início dos botões/descrição do Shorts)


def _desenha_enfase(draw, text, fontsize, font, highlight_idx, cor, base_fill, stroke, enfase, escala, y0, total_h0,
                    cores=None):
    """23/10 (dona: "dar ênfase de tamanho também em palavras"): desenha o card com as palavras de `enfase` maiores e
    na cor de quem fala, todas na mesma linha de base. Mesma área/centro do card normal. Devolve o y do topo."""
    ws = (text or "").split()
    grande = _load_font(int(fontsize * escala))
    fontes = [grande if k in enfase else font for k in range(len(ws))]
    larg = [draw.textlength(w, font=f) for w, f in zip(ws, fontes)]
    esp = draw.textlength(" ", font=font)
    linhas, cur = [], []
    for k in range(len(ws)):
        if cur and sum(larg[j] for j in cur) + esp * len(cur) + larg[k] > W * 0.86:
            linhas.append(cur)
            cur = []
        cur.append(k)
    if cur:
        linhas.append(cur)
    alturas = [int(max(fontes[k].size for k in ln) * 1.18) for ln in linhas[:3]]
    y = y0 + total_h0 - sum(alturas)  # mesma base do card normal (cresce pra cima)
    _yc = os.environ.get("SUB_Y_CENTER")
    if _yc:
        try:
            y = min(int(H * float(_yc)) - sum(alturas) // 2, int(H * _BASE_MAX) - sum(alturas))
        except ValueError:
            pass
    topo = y
    for ln, alt in zip(linhas[:3], alturas):
        base = y + max(fontes[k].getmetrics()[0] for k in ln)
        cx = (W - (sum(larg[k] for k in ln) + esp * (len(ln) - 1))) // 2
        for k in ln:
            fill = (*cor, 255) if (k in enfase or k == highlight_idx) else base_fill
            if cores and k in cores:  # 28/10: nome de personagem sempre na cor dele (dona: "cor por personagem")
                fill = (*cores[k], 255)
            draw.text((cx, base), ws[k], font=fontes[k], fill=fill, anchor="ls",
                      stroke_width=stroke if k not in enfase else int(stroke * escala), stroke_fill=(0, 0, 0, 235))
            cx += larg[k] + esp
        y += alt
    return topo


_FONTES_IMPACTO = [r"D:\hipercool-materiais\assets\fonts\Bangers-Regular.ttf",
                   r"D:\hipercool-materiais\assets\fonts\LuckiestGuy-Regular.ttf"]


def _render_impacto_png(palavra, out_png, cor, zoom=1.0, alfa=1.0, fontsize=65, lateral=None):
    """23/10 (dona: "palavras muito chave por um segundo na tela quase toda, como impacto"): a palavra ENORME no
    centro (até 90% da largura), na cor de quem fala, contorno grosso. zoom/alfa = quadro da animação de entrada/saída.
    lateral = n (27/10, dona: "muito maiores e até de lado na tela, fontes diferentes"): inclinada ~9°, do lado
    esquerdo (n par) ou direito, fonte de impacto alternando. Retorna (png, x, y) recortado, como _render_caption_png."""
    from PIL import Image, ImageDraw, ImageFont
    palavra = re.sub(r"[^\w]+$", "", palavra or "").upper()
    if not palavra:
        return None
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    carregar = _load_font
    if lateral is not None:
        fp = _FONTES_IMPACTO[lateral % len(_FONTES_IMPACTO)]
        if not Path(fp).exists():  # PC2: hipercool-materiais fica no C: (o D: só existe dentro da tarefa)
            fp = "C" + fp[1:]
        if Path(fp).exists():
            carregar = lambda s: ImageFont.truetype(fp, s)  # noqa: E731
    ref = carregar(100)
    largura100 = max(1.0, draw.textlength(palavra, font=ref))
    fs = int(min(fontsize * 3.2, 100 * W * (0.9 if lateral is None else 0.70) / largura100) * zoom)
    font = carregar(max(20, fs))
    st = max(4, int(fs * 0.08))
    a = int(255 * alfa)
    if lateral is None:
        draw.text((W // 2, int(H * 0.42)), palavra, font=font, anchor="mm", fill=(*cor, a),
                  stroke_width=st, stroke_fill=(0, 0, 0, int(235 * alfa)))
    else:
        lado = -1 if lateral % 2 == 0 else 1
        camada = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(camada).text((W // 2, H // 2), palavra, font=font, anchor="mm", fill=(*cor, a),
                                    stroke_width=st, stroke_fill=(0, 0, 0, int(235 * alfa)))
        camada = camada.crop(camada.getbbox() or (0, 0, 1, 1)).rotate(9 * -lado, expand=True, resample=Image.BICUBIC)
        cx = int(W * (0.5 + 0.16 * lado))
        x0 = min(max(0, cx - camada.width // 2), max(0, W - camada.width))
        img.alpha_composite(camada, (x0, max(0, int(H * 0.40) - camada.height // 2)))
    bbox = img.getbbox()
    if not bbox:
        return None
    pad = 6
    cx0 = max(0, bbox[0] - pad); cy0 = max(0, bbox[1] - pad)
    cx1 = min(W, bbox[2] + pad); cy1 = min(H, bbox[3] + pad)
    img.crop((cx0, cy0, cx1, cy1)).save(out_png)
    return (out_png, cx0, cy0)


# pop de entrada, segura, encolhe sumindo: (início s, zoom, alfa) — total ~1 s
_IMPACTO_QUADROS = [(0.0, 0.55, 1.0), (0.05, 0.8, 1.0), (0.10, 1.08, 1.0), (0.16, 1.0, 1.0), (0.85, 0.9, 0.7),
                    (0.92, 0.75, 0.35)]
_IMPACTO_FIM = 1.0


# 28/10 (dona: "efeitos de choque e fogo como os do manhwa-react ... pra transicionar a tela ou pra impactos"): quadros
# transparentes 720x1280 renderizados UMA vez no Remotion (claude-code-video src/videos/_cortes_fx, porte do divider.py
# do manhwa-react). impacto_* = choque cortando a tela sob a palavra de impacto; varredura_* = a faixa atravessa a tela
# na troca de cena. Teste T6 (CORTES_FX_CHOQUE). Estilo fixo por vídeo.
_FX_DIR = Path(r"D:\hipercool-materiais\assets\cortes_fx")
_FX_ESTILOS = ["raio_00d1ff", "raio_ffc83d", "fogo_ff2a1a"]  # glitch: render do Remotion travou (28/10)
_FX_VARREDURAS, _FX_INTERVALO, _FX_INICIO = 2, 6.0, 3.5


def _fx_choque(impactos_t, offsets, tmp_dir, semente):
    from PIL import Image
    base = _FX_DIR if _FX_DIR.exists() else Path("C" + str(_FX_DIR)[1:])  # PC2: hipercool-materiais no C:
    if (W, H) != (720, 1280) or not base.exists():
        return []
    import hashlib
    estilo = _FX_ESTILOS[int(hashlib.md5(semente.encode()).hexdigest(), 16) % len(_FX_ESTILOS)]
    eventos = [("impacto", t) for t in impactos_t]
    ocupados = list(impactos_t)
    for t in offsets[1:]:  # trocas de cena (início de cada frase): longe do gancho, dos impactos e uma da outra
        if len([e for e in eventos if e[0] == "varredura"]) >= _FX_VARREDURAS:
            break
        if t >= _FX_INICIO and all(abs(t - o) >= _FX_INTERVALO for o in ocupados):
            eventos.append(("varredura", t))
            ocupados.append(t)
    subs = []
    for tipo, t0 in eventos:
        quadros = sorted((base / f"{tipo}_{estilo}").glob("f_*.png"))
        for k, q in enumerate(quadros):
            png = Path(tmp_dir) / f"_fx_{tipo}_{t0:.2f}_{k:02d}.png"
            im = Image.open(q)
            bb = im.getbbox()
            if not bb:
                continue
            im.crop(bb).save(png)
            subs.append({"png": str(png), "x": bb[0], "y": bb[1], "start": t0 + k / 30, "end": t0 + (k + 1) / 30})
    if subs:
        marcar_usado(tmp_dir, "fx_choque", estilo)
    return subs


def marcar_usado(pasta, chave, valor):
    """Testes A/B: o que o render (outro processo) usou de fato -> pasta/_testes_usados.json, lido pelo anime_publish."""
    import json
    arq = Path(pasta) / "_testes_usados.json"
    try:
        d = json.loads(arq.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        d = {}
    d[chave] = valor
    arq.write_text(json.dumps(d), encoding="utf-8")


def _escolher_impactos_legenda(cands):
    """cands [(nota, início_s, ...)] -> os escolhidos: maior nota primeiro, no máx imp_max, um a cada imp_intervalo."""
    if not cands:
        return []
    imp_max, intervalo = int(cands[0][-1].get("imp_max", 2)), float(cands[0][-1].get("imp_intervalo", 8))
    escolhidos = []
    for c in sorted(cands, key=lambda c: (-c[0], c[1])):
        if len(escolhidos) >= imp_max:
            break
        if all(abs(c[1] - e[1]) >= intervalo for e in escolhidos):
            escolhidos.append(c)
    return sorted(escolhidos, key=lambda c: c[1])


def _render_caption_png(text, out_png, fontsize=65, highlight_idx=None,
                        highlight_color=(255, 214, 60), rotulo=None, enfase=None, escala=1.3, cores=None):
    """Renderiza uma legenda como PNG transparente (recortado na região do texto).

    Branco com contorno preto grosso, embaixo-centro. Retorna (png, x, y) com a
    posição do recorte no canvas 1080x1920, pra overlay leve (pouca memória).

    highlight_idx: índice da palavra (na contagem global do texto) a destacar em
    amarelo (estilo karaokê). None = sem destaque (legenda estática).
    rotulo: nome curto de quem fala, pequeno em cima do card na highlight_color (Short de formato, 23/10).
    enfase: índices (no card) das palavras importantes: saem `escala`x MAIORES e sempre na highlight_color (23/10).
    """
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # T6: estilo por contexto (SUB_CONTEXT=1). Ajusta fontsize/cor base pelo tom da frase.
    _ctx_color = None
    _ctx_stroke_boost = 0
    if os.environ.get("SUB_CONTEXT", "0") == "1":
        _ctx = detect_context(text)
        _mult, _col = _SUB_CONTEXT_STYLE.get(_ctx, (1.0, None))
        fontsize = int(fontsize * _mult)
        _ctx_color = _col
        if _ctx == "shout":
            _ctx_stroke_boost = 3
    font = _load_font(fontsize)
    lines = _wrap_lines(text, font, draw, max_w=int(W * 0.86))
    if not lines:
        return None

    line_h = int(fontsize * 1.18)
    total_h = line_h * len(lines)
    # Base em 80% da altura. 29/10: era 85% — a 2ª linha caía em y≈1620-1690/1920, debaixo dos botões do Shorts
    # (júri em d9bb92 q13 e b0c0f3 q06; os 5 modelos da bancada do melhorador e a sessão concordaram)
    y0 = int(H * 0.80) - total_h
    # SUB_Y_CENTER (fração da altura): centraliza o card ali — Short de parceiro põe a NOSSA legenda exatamente em
    # cima da linha da legenda deles, que foi coberta só onde tinha palavra (16/10)
    _yc = os.environ.get("SUB_Y_CENTER")
    if _yc:
        try:
            y0 = min(int(H * float(_yc)) - total_h // 2, int(H * _BASE_MAX) - total_h)
        except ValueError:
            pass
    stroke = 8 + _ctx_stroke_boost
    _base_fill = (*_ctx_color, 255) if _ctx_color else (255, 255, 255, 255)
    if (enfase or cores) and highlight_idx is not None:  # 23/10: card com palavra maior tem o próprio desenho
        y0 = _desenha_enfase(draw, text, fontsize, font, highlight_idx, highlight_color, _base_fill, stroke,
                             set(enfase or ()), escala, y0, total_h, cores=cores)
        lines = []
    word_counter = 0  # índice global da palavra (pra casar com highlight_idx)
    space_w = draw.textlength(" ", font=font)
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font, stroke_width=stroke)
        lw = bbox[2] - bbox[0]
        x = (W - lw) // 2 - bbox[0]
        y = y0 + i * line_h
        if highlight_idx is None:
            draw.text((x, y), line, font=font, fill=_base_fill,
                      stroke_width=stroke, stroke_fill=(0, 0, 0, 235))
        else:
            # desenha palavra a palavra pra colorir a ativa
            cx = x
            for word in line.split():
                color = (*highlight_color, 255) if word_counter == highlight_idx \
                    else _base_fill
                draw.text((cx, y), word, font=font, fill=color,
                          stroke_width=stroke, stroke_fill=(0, 0, 0, 235))
                cx += draw.textlength(word, font=font) + space_w
                word_counter += 1
    if rotulo:  # 23/10: "QUICO" pequeno em cima da fala, na cor dele
        lfont = _load_font(max(18, int(fontsize * 0.5)))
        lb = draw.textbbox((0, 0), rotulo, font=lfont, stroke_width=5)
        draw.text(((W - (lb[2] - lb[0])) // 2 - lb[0], y0 - (lb[3] - lb[1]) - int(fontsize * 0.25) - lb[1]), rotulo,
                  font=lfont, fill=(*highlight_color, 255), stroke_width=5, stroke_fill=(0, 0, 0, 235))

    # Recorta só a região do texto (com folga) → PNG pequeno, overlay barato
    bbox = img.getbbox()
    if not bbox:
        return None
    pad = 6
    cx0 = max(0, bbox[0] - pad); cy0 = max(0, bbox[1] - pad)
    cx1 = min(W, bbox[2] + pad); cy1 = min(H, bbox[3] + pad)
    img.crop((cx0, cy0, cx1, cy1)).save(out_png)
    return (out_png, cx0, cy0)


def render_subtitles(entries, tmp_dir, offsets=None):
    """Gera PNGs das legendas com timing cumulativo.

    entries: lista de (texto, duracao_segundos) na ORDEM dos clips.
    offsets: se fornecido, lista de timestamps absolutos de início para cada entry.
             Usado quando as legendas são filtradas (ex: só narrador) e os tempos
             não são mais sequenciais.
    Retorna lista de dicts {png, start, end} (só pros painéis com texto).
    """
    tmp_dir = Path(tmp_dir)
    subs = []
    t = 0.0
    for i, (text, dur) in enumerate(entries):
        dur = max(0.4, float(dur or 0))
        if offsets:
            start = offsets[i]
            end = start + dur
        else:
            start, end = t, t + dur
            t = end
        if not (text or "").strip():
            continue
        png = tmp_dir / f"_cap_{i:03d}.png"
        res = _render_caption_png(text, png)
        if res:
            _, x, y = res
            subs.append({"png": str(png), "x": x, "y": y, "start": start, "end": end})
    return subs


def render_subtitles_progressive(entries, tmp_dir, offsets=None, word_times=None):
    """Legendas KARAOKÊ OTIMIZADO: a palavra ativa fica amarela, sincronizada por tempo.

    word_times (MELHORIA WordBoundary): lista alinhada às entries; cada item é a lista de
    [start_s,end_s,word] REAL do edge-tts (sidecar .words.json). Quando presente p/ a entry,
    usa o timing REAL de cada palavra (mata o drift do karaokê); senão, estimativa por len().

    OTIMIZAÇÃO: Em vez de 1 PNG por palavra (que gerava centenas de overlays e timeout),
    gera 1 PNG a cada CHUNK de 3 palavras. Dentro de cada chunk, a palavra destacada
    muda — mas o total de PNGs fica ~3x menor que o original.

    Sem timestamps do TTS, estima o timing dividindo a duração do clip igualmente
    entre as palavras. Reusa o mesmo wrap/layout da legenda estática.

    offsets: se fornecido, lista de timestamps absolutos de início para cada entry.
    """
    tmp_dir = Path(tmp_dir)
    subs = []
    t = 0.0
    CHUNK_SIZE = 5  # Palavras por PNG (aumentado de 3 pra 5 pra gerar menos PNGs)

    for i, (text, dur) in enumerate(entries):
        dur = max(0.4, float(dur or 0))
        if offsets:
            start = offsets[i]
        else:
            start = t
            t += dur
        words = (text or "").strip().split()
        if not words:
            continue
        n = len(words)
        # MELHORIA WordBoundary: usa timing REAL de cada palavra se veio o sidecar da entry.
        wt_real = None
        if word_times and i < len(word_times) and word_times[i]:
            wt_real = _alinhar_tempos(words, word_times[i])  # [[start,end,word],...] relativo ao clip
        # Distribuição proporcional ao comprimento de cada palavra (fallback quando sem real)
        weights = [max(2, len(w)) for w in words]
        total_weight = sum(weights)
        word_durs = [dur * (wt / total_weight) for wt in weights]

        # Gerar PNGs em chunks: cada chunk destaca 1 palavra diferente
        # mas só cria 1 PNG por chunk (a palavra central do chunk fica amarela)
        for w_idx in range(0, n, CHUNK_SIZE):
            chunk_end = min(w_idx + CHUNK_SIZE, n)
            # Pra cada palavra do chunk, gerar um PNG com ela destacada
            for highlight in range(w_idx, chunk_end):
                png = tmp_dir / f"_capk_{i:03d}_{highlight:03d}.png"
                res = _render_caption_png(text, png, highlight_idx=highlight)
                if not res:
                    continue
                _, x, y = res
                if wt_real:
                    # timing REAL do edge-tts (relativo ao clip) + offset absoluto do clip
                    w_start = start + wt_real[highlight][0]
                    w_end = start + wt_real[highlight][1]
                else:
                    w_start = start + sum(word_durs[:highlight])
                    w_end = start + sum(word_durs[:highlight + 1])
                subs.append({"png": str(png), "x": x, "y": y,
                             "start": w_start, "end": w_end})

        # LIMITE DE SEGURANÇA: se já ultrapassou 300 PNGs, para de gerar karaokê
        # e volta pra estático pro restante (evita timeout no ffmpeg)
        if len(subs) > 300:
            # Restante em modo estático (1 PNG por entry)
            for j in range(i + 1, len(entries)):
                txt_j, dur_j = entries[j]
                dur_j = max(0.4, float(dur_j or 0))
                if offsets:
                    start_j = offsets[j]
                else:
                    start_j = t
                    t += dur_j
                if not (txt_j or "").strip():
                    continue
                png = tmp_dir / f"_capk_{j:03d}_static.png"
                res = _render_caption_png(txt_j, png)
                if res:
                    _, x, y = res
                    subs.append({"png": str(png), "x": x, "y": y,
                                 "start": start_j, "end": start_j + dur_j})
            break

    return subs


def render_name_tag(name, out_png, fontsize=58):
    """Renderiza o nome do personagem (tag) acima da legenda, em destaque.

    Retorna (png, x, y) recortado. Cor de destaque amarela com contorno preto.
    """
    from PIL import Image, ImageDraw
    name = (name or "").strip().upper()
    if not name:
        return None
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = _load_font(fontsize)
    bbox = draw.textbbox((0, 0), name, font=font, stroke_width=6)
    # Canto superior-esquerdo (abaixo do watermark central, longe da legenda)
    x = 60 - bbox[0]
    y = int(H * 0.12)
    draw.text((x, y), name, font=font, fill=(255, 214, 60, 255),
              stroke_width=6, stroke_fill=(0, 0, 0, 235))
    crop = img.getbbox()
    if not crop:
        return None
    img.crop(crop).save(out_png)
    return (out_png, crop[0], crop[1])


def render_watermark(text, tmp_dir, total_dur, fontsize=40):
    """Gera um watermark (handle do canal) fixo no topo, semitransparente.

    Retorna um spec de overlay {png,x,y,start,end} pro burn_subtitles.
    """
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = _load_font(fontsize)
    bbox = draw.textbbox((0, 0), text, font=font, stroke_width=4)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (W - tw) // 2 - bbox[0]
    y = int(H * 0.045)
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 200),
              stroke_width=4, stroke_fill=(0, 0, 0, 160))
    crop = img.getbbox()
    if not crop:
        return None
    out = Path(tmp_dir) / "_watermark.png"
    img.crop(crop).save(out)
    return {"png": str(out), "x": crop[0], "y": crop[1], "start": 0.0, "end": total_dur}


def censurar_video(video_in, windows, video_out, radius=45):
    """Censura com 3 níveis por janela de tempo (painéis +18).

    windows: lista de tuplas. Aceita 2 formatos:
      - (start, end)          → censura FORTE (retrocompat)
      - (start, end, nivel)   → 'forte' / 'leve' / 'intacto'
    nivel='forte': UM método só — tarja preta central (default) OU blur pesado.
                   Escolha por CENSURA_FORTE_MODO: 'tarja' (default) | 'blur'.
                   NUNCA os dois juntos.
    nivel='leve':  UM método só — shift de cor sutil (engana detector sem destruir cena).
    Uma passada só (re-encode do vídeo; áudio copiado).
    """
    parsed = []
    for w in windows:
        if len(w) == 3:
            s, e, niv = float(w[0]), float(w[1]), w[2]
        else:
            s, e, niv = float(w[0]), float(w[1]), "forte"
        if e > s and niv != "intacto":
            parsed.append((s, e, niv))
    if not parsed:
        import shutil as _shu
        _shu.copy2(str(video_in), str(video_out))
        return True
    fortes = [(s, e) for s, e, n in parsed if n == "forte"]
    leves = [(s, e) for s, e, n in parsed if n == "leve"]
    modo_forte = os.environ.get("CENSURA_FORTE_MODO", "tarja").strip().lower()
    filters = []
    if fortes:
        en_f = "+".join(f"between(t,{s:.2f},{e:.2f})" for s, e in fortes)
        if modo_forte == "blur":
            # MÉTODO ÚNICO: blur pesado na tela toda (sem tarja).
            filters.append(
                f"boxblur=luma_radius=28:luma_power=3:chroma_radius=28:chroma_power=3:enable='{en_f}'")
        else:
            # MÉTODO ÚNICO (default): tarja preta central sólida (sem blur junto).
            filters.append(
                f"drawbox=x=iw*0.10:y=ih*0.10:w=iw*0.80:h=ih*0.78:color=black:t=fill:enable='{en_f}'")
    if leves:
        # MÉTODO ÚNICO: grade de cor sutil (dessatura + leve brilho/contraste), sem blur/tarja.
        en_l = "+".join(f"between(t,{s:.2f},{e:.2f})" for s, e in leves)
        filters.append(f"hue=s=0.78:enable='{en_l}'")
        filters.append(f"eq=brightness=0.02:contrast=1.05:enable='{en_l}'")
    vf = ",".join(filters)
    cmd = [
        "ffmpeg", "-y", "-i", str(video_in),
        "-vf", vf,
        "-c:v", "libx264", "-preset", QP["preset"], "-crf", str(QP["crf"]), "-g", "30",
        "-c:a", "copy", "-movflags", "+faststart", "-pix_fmt", "yuv420p",
        str(video_out),
    ]
    # 22/10 (HUB-03): mesmo padrão da linha ~800 — o erro do ffmpeg ia pro lixo e a legenda sumia sem causa
    for _tentativa in (1, 2):
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=1200)
            if Path(video_out).exists() and Path(video_out).stat().st_size > 0:
                return True
            motivo = "saída vazia"
        except subprocess.CalledProcessError as e:
            motivo = (e.stderr or b"").decode("utf-8", "replace").strip()[-400:]
        except subprocess.TimeoutExpired:
            motivo = "passou de 1200s"
        import logging as _lg
        _lg.warning(f"[fx_subtitles] queima de filtros falhou (tentativa {_tentativa}): {motivo}")
    return False


def _ass_ts(t):
    """Segundos -> timestamp ASS H:MM:SS.cc (centésimos)."""
    if t < 0:
        t = 0.0
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = int(t % 60)
    cs = int(round((t - int(t)) * 100))
    if cs >= 100:
        cs = 99
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _ass_escape(text):
    """Escapa chars especiais do ASS dentro do campo de texto."""
    return (text or "").replace("\\", "\\\\").replace("{", "(").replace("}", ")").replace("\n", " ")


# 28/10 (Hypit skills/hypit/references/playbooks/craft/captions.md "Design Cue rhythm"): cartão por SENTIDO, não por
# contagem fixa. Nunca separa artigo+substantivo ("o rei"), negação+verbo ("não quer"), preposição+objeto ("de novo"),
# nome próprio de 2 palavras, número+unidade; palavra de impacto fica sozinha. Alvo continua words_per_card (~2) e
# vai a 3 quando junta o par. SUB_AGRUPAR=fixo volta ao antigo.
_COLA_FRENTE = set("""o a os as um uma uns umas não nem nunca já de da do das dos em na no nas nos pra pro pras pros
para por pelo pela pelos pelas com sem ao à aos às meu minha meus minhas seu sua seus suas teu tua nosso nossa esse
essa este esta aquele aquela muito mais tão bem the a an not no of to in on at for with my his her""".split())
_NUMERO = re.compile(r"^\d[\d.,%]*$|^(dois|três|quatro|cinco|seis|sete|oito|nove|dez|cem|mil|vinte|trinta|cinquenta)$",
                     re.IGNORECASE)


def _limpa(w):
    return re.sub(r"[^\wÀ-ÿ%]", "", w).lower()


def cartoes_por_sentido(words, alvo=2, isolar=()):
    """[(ini, fim_exclusivo)] cobrindo words na ordem."""
    if os.environ.get("SUB_AGRUPAR", "sentido") == "fixo" or alvo < 2:
        return [(g, min(g + alvo, len(words))) for g in range(0, len(words), max(1, alvo))]
    isolar = set(isolar or ())
    n, out, g = len(words), [], 0

    def preso(k):  # words[k] e words[k+1] não podem ficar em cartões diferentes
        if k + 1 >= n or k in isolar or k + 1 in isolar or words[k][-1:] in ".!?,;:…":
            return False
        a, b = words[k], words[k + 1]
        if _limpa(a) in _COLA_FRENTE or _NUMERO.match(_limpa(a)):
            return True
        return a[:1].isupper() and b[:1].isupper() and not a.isupper() and k > 0 and words[k - 1][-1:] not in ".!?"

    while g < n:
        if g in isolar:
            out.append((g, g + 1))
            g += 1
            continue
        fim = min(g + alvo, n)
        while fim < n and fim - g < alvo + 1 and fim - 1 >= g and preso(fim - 1) and fim not in isolar:
            fim += 1
        # cartão não termina em palavra que cola na frente nem começa um par que ficaria cortado
        if fim < n and fim - g > 1 and preso(fim - 1) and fim - g >= alvo + 1:
            limpa = next((e for e in range(fim - 1, g, -1) if not preso(e - 1)), None)
            if limpa is not None:  # sem fronteira limpa ("de dois mil e...") fica o cartão de 3
                fim = limpa
        k = next((j for j in range(g + 1, fim) if j in isolar), None)
        if k is not None:
            fim = k
        out.append((g, fim))
        g = fim
    return out


_RAJADA_MAX_S = 20.0  # batalha: o trecho criativo segue enquanto vierem palavras pesadas, até 20 s
# 01/11 dona ("lutas, momentos dramáticos, dar ênfase em palavras pesadas"): palavra que puxa o destaque criativo
_PESADAS = re.compile(
    r"^(mat(ou|ar|ando)|morr\w*|mort[ea]s?|sangue\w*|explod\w*|explos\w*|destru\w*|esmag\w*|trai(u|ção|çao|dor\w*)|"
    r"vingan\w*|humilh\w*|monstr\w*|dem[ôo]ni\w*|poder(oso|osa)?|desperto?u|despertar|socorro|grit\w*|lut\w*|"
    r"golpe\w*|espada|inimig\w*|massacr\w*|cort(ou|ada|ado)|decapit\w*|queim\w*|fogo|raio\w*|furi\w*|insano|"
    r"absurd\w*|imposs[ií]vel|lend[áa]ri\w*|invenc[ií]vel|rei|rainha|deus(a|es)?|nunca|jamais|inferno|pesadel\w*|"
    r"bizarr\w*|medonh\w*|capeta|diab\w*|guerra|terr[íi]ve(l|is)|terror|brutal\w*|apel[ãa]o|selvage\w*|"
    r"assassin\w*|amaldi[çc]o\w*|maldi[çc][ãa]o|caos|apocalipse|sacrif[íi]ci\w*)[.,!?…]*$", re.I)


MASCOTE_CTA_DIR = Path(r"D:\hipercool-materiais\mascote_waifu_v2\cosplay_recorte")
if not MASCOTE_CTA_DIR.is_dir() and os.environ.get("RAIZ_WIN"):  # 02/11: no Kaggle a raiz do D: fica em RAIZ_WIN
    MASCOTE_CTA_DIR = Path(os.environ["RAIZ_WIN"]) / "D" / "hipercool-materiais" / "mascote_waifu_v2" / "cosplay_recorte"


def mascote_cta(marcas, video_in, retrato):
    """(png, filtro) da Maria muda nos cartões de like/CTA: entra deslizando do lado esquerdo, balança de leve e sai.
    Sem pasta da mascote (nuvem) ou sem CTA = None. ANIME_MASCOTE_CTA=0 desliga."""
    if os.environ.get("ANIME_MASCOTE_CTA", "1") == "0" or not MASCOTE_CTA_DIR.is_dir():
        return None
    ctas = [(float(t), tipo) for t, tipo, _r in marcas if tipo == "like"]
    if not ctas:
        return None
    fotos = sorted(p for p in MASCOTE_CTA_DIR.glob("*.png") if "estudante" not in p.name)
    if not fotos:
        return None
    import hashlib as _h
    foto = fotos[int(_h.md5(str(video_in).encode()).hexdigest(), 16) % len(fotos)]
    alto = 0.40 if retrato else 0.55
    partes, base = [], "[_b]"
    partes.append(f"[1:v]scale=-1:ih*0+{int(1920 * alto) if retrato else int(1080 * alto)},format=rgba[_m]")
    ult = "_m"
    for k, (t0, _tp) in enumerate(ctas[:3]):
        t1 = t0 + 3.6
        if k < len(ctas[:3]) - 1:
            partes.append(f"[{ult}]split[{ult}a][{ult}b]")
            src, ult = f"{ult}a", f"{ult}b"
        else:
            src = ult
        x = (f"if(lt(t-{t0:.2f},0.35),-w+(w*0.95)*(t-{t0:.2f})/0.35,"
             f"if(gt(t,{t1 - 0.35:.2f}),-w*0.05-(w*0.95)*(t-{t1 - 0.35:.2f})/0.35,-w*0.05))")
        y = f"H*{0.80 if retrato else 0.97}-h+10*sin(5*(t-{t0:.2f}))"
        saida = "[_v]" if k == len(ctas[:3]) - 1 else f"[_o{k}]"
        partes.append(f"{base}[{src}]overlay=x='{x}':y='{y}':enable='between(t,{t0:.2f},{t1:.2f})'{saida}")
        base = saida
    return str(foto), ";".join(partes)


def burn_subtitles_ass(video_in, entries, video_out, words_per_card=None,
                       word_times=None, offsets=None, extra=None, falantes=None):
    """Queima legenda dinâmica (1-2 palavras, karaokê amarelo) via libass — UMA passada.

    Substitui burn_subtitles (PNG overlay) pra vídeos LONGOS: o overlay PNG re-encoda
    o vídeo inteiro a cada ~100 cartões, o que em recap de 40min vira dezenas de
    passadas (horas). O libass renderiza TODOS os cartões numa única passada de
    re-encode (filtro `subtitles`), independente da quantidade.

    Replica o timing/estilo de render_subtitles_short: fonte pesada (Impact),
    branco com contorno preto grosso, embaixo-centro; cada palavra ACENDE amarelo
    no seu tempo.

    word_times: [[[start_rel,end_rel,palavra],...] | None, ...] alinhado a entries —
                timing REAL por palavra do edge-tts (relativo ao início do clipe).
                Quando presente e a contagem casa, dá sincronia exata; senão cai na
                estimativa por peso de len() da palavra.
    offsets:    [start_abs_s, ...] alinhado a entries — início absoluto de cada clipe
                no vídeo concatenado (corrige o drift NÃO-linear do xfade). Quando
                ausente, usa o acumulado t += dur (desanda ~30s em 1h).
    falantes:   [(cor_rgb, nome[, extra]), ...] alinhado a entries (formato com várias vozes, 23/10): palavra ativa
                na cor de quem fala + nome pequeno em cima; extra = ênfase (palavra maior) e impacto (palavra enorme
                no centro ~1 s). None = karaokê amarelo de sempre.
    """
    import os as _os
    if words_per_card is None:
        try:
            words_per_card = max(1, int(_os.environ.get("SUB_WORDS_PER_CARD", "2")))
        except ValueError:
            words_per_card = 2

    YELLOW = r"{\c&H3CD6FF&}"   # ASS = &HBBGGRR ; amarelo RGB(255,214,60)
    WHITE = r"{\c&HFFFFFF&}"
    fontsize = 64

    events = []
    imp_cands = []  # 23/10: candidatos a palavra de impacto (nota, início, palavra, cor, extra)
    # 01/11 dona: nos primeiros ANIME_LEGENDA_CRIATIVA_S segundos a legenda FALADA vira a abertura criativa (cada
    # palavra no seu tempo, fonte/cor/tamanho/lugar diferentes, efeito de elemento) e a legenda de baixo não aparece
    try:
        _criativa_ate = float(os.environ.get("ANIME_LEGENDA_CRIATIVA_S", "45"))  # 01/11 dona: "deveria estar pelo menos no resumo inteiro"
    except ValueError:
        _criativa_ate = 45.0
    criativos = []  # [(início, palavra), ..., fim do cartão]
    try:
        _cada_s = float(os.environ.get("ANIME_LEGENDA_CRIATIVA_CADA_S", "45"))
    except ValueError:
        _cada_s = 45.0
    _rajada_ini, _rajada_ate, _prox_rajada, _cart_cria = 0.0, 0.0, _criativa_ate + _cada_s / 2, False
    todas = []  # [(início, fim, palavra)] do vídeo todo
    cenas = []  # V-02: início de cada clipe = troca de cena
    t = 0.0
    for i, (text, dur) in enumerate(entries):
        dur = max(0.4, float(dur or 0))
        # Base do cartão: offset absoluto pós-xfade quando disponível (mata o
        # drift); senão o acumulado simples.
        if offsets and i < len(offsets) and offsets[i] is not None:
            start = float(offsets[i])
        else:
            start = t
        cenas.append(start)
        t += dur
        # Limpa pontuação órfã no INÍCIO de cada palavra (ex: vírgula solta que
        # vira ",coordenado." no card) e descarta tokens só de pontuação (o
        # ", " isolado que aparecia colado na palavra seguinte).
        words = []
        for _w in (text or "").strip().split():
            _w = _strip_lead_punct(_w)
            if _w:
                words.append(_w)
        if not words:
            continue
        # Timing REAL por palavra: só usa se a contagem do sidecar casa com as
        # palavras limpas (o tokenizer do edge-tts pode divergir por pontuação/
        # hífen). Senão cai na estimativa por peso de len(). Mesma guarda de
        # render_subtitles_short.
        wt_real = None
        if word_times and i < len(word_times) and word_times[i]:
            wt_real = _alinhar_tempos(words, word_times[i])
        weights = [max(2, len(w)) for w in words]
        total_w = sum(weights)
        word_durs = [dur * (wt / total_w) for wt in weights]
        # 25/10: era "extra" e apagava o parâmetro extra (gancho/barra/tarja) — desde 23/10 nenhum longo tinha gancho
        ativa, nome_tag, enf, fx_fala = YELLOW, "", set(), {}
        if falantes and i < len(falantes) and falantes[i]:  # 23/10: cor/nome de quem fala
            (_r, _g, _b), _nome = falantes[i][0], falantes[i][1]
            ativa = r"{\c&H%02X%02X%02X&}" % (_b, _g, _r)
            if _nome:
                nome_tag = r"{\fscx50\fscy50}%s%s\N{\fscx100\fscy100}" % (ativa, _ass_escape(_nome))
            fx_fala = falantes[i][2] if len(falantes[i]) > 2 and falantes[i][2] else {}
            enf = set(fx_fala.get("enfase") or [])
            _imp = fx_fala.get("impacto")
            if _imp and 0 <= _imp[0] < len(words):
                _t0 = start + (float(wt_real[_imp[0]][0]) if wt_real else sum(word_durs[:_imp[0]]))
                imp_cands.append((float(_imp[1]), _t0, words[_imp[0]], ativa, fx_fala))
        _isol = [fx_fala["impacto"][0]] if fx_fala.get("impacto") else []
        for g, _fim in cartoes_por_sentido(words, words_per_card, _isol):  # 28/10: por sentido (Hypit)
            grp = words[g:_fim]
            for local_idx in range(len(grp)):
                gi = g + local_idx
                if wt_real:
                    w_start = start + float(wt_real[gi][0])
                    w_end = start + float(wt_real[gi][1])
                else:
                    w_start = start + sum(word_durs[:gi])
                    w_end = start + sum(word_durs[:gi + 1])
                # monta o texto do card com a palavra ativa em amarelo, resto branco
                partes = []
                for j, w in enumerate(grp):
                    col = ativa if (j == local_idx or g + j in enf) else WHITE
                    if g + j in enf:  # 23/10: ênfase = palavra maior
                        _e = int(100 * float(fx_fala.get("escala", 1.3)))
                        partes.append(r"%s{\fscx%d\fscy%d}%s{\fscx100\fscy100}" % (col, _e, _e, _ass_escape(w)))
                        continue
                    partes.append(f"{col}{_ass_escape(w)}")
                # 27/10: com a Impact + contorno 4 o vão entre palavras era 0 px ("atingir o" = "atingiro");
                # 2 espaços = 9 px (o libass não junta espaços), sem espaçar as letras
                card = nome_tag + "  ".join(partes)
                todas.append((w_start, w_end, grp[local_idx]))  # 01/11: cartões animados (anime_cartoes)
                if local_idx == 0:  # 01/11 dona: momentos-chave no meio do vídeo (palavra pesada) também viram criativa
                    _pesada = any(_PESADAS.search(w) for w in grp)
                    _cart_cria = w_start < _criativa_ate or w_start < _rajada_ate
                    if _cart_cria and _pesada and w_start >= _criativa_ate:
                        # batalha: palavra pesada seguida estica o trecho criativo (até RAJADA_MAX_S)
                        _rajada_ate = min(_rajada_ini + _RAJADA_MAX_S, max(_rajada_ate, w_start + 2.5))
                        _prox_rajada = _rajada_ate + _cada_s
                    elif not _cart_cria and _cada_s > 0 and w_start >= _prox_rajada and _pesada:
                        _cart_cria, _rajada_ini, _rajada_ate = True, w_start, w_start + 2.5
                        _prox_rajada = _rajada_ate + _cada_s
                if _cart_cria:  # 01/11: este cartão vira palavras soltas (abertura criativa, abaixo)
                    if local_idx == 0:
                        _fim_cart = start + (float(wt_real[_fim - 1][1]) if wt_real else sum(word_durs[:_fim]))
                        criativos.append({"palavras": [(start + (float(wt_real[g + j][0]) if wt_real else sum(word_durs[:g + j])),
                                           w) for j, w in enumerate(grp)], "fim": _fim_cart,
                                           "abertura": w_start < _criativa_ate})
                    continue
                events.append((w_start, w_end, card))

    if not events and not criativos:
        return False

    # PlayRes PRECISA casar com a resolução REAL do vídeo: o recap deitado é
    # 1280x720, mas os globais W/H são 720x1280 (retrato dos shorts). Se o PlayRes
    # não bate com o vídeo, o libass escala/posiciona errado (texto minúsculo e
    # deslocado, às vezes fora do quadro). Então detecta a dimensão real por ffprobe.
    vw, vh = W, H
    try:
        _dim = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height", "-of", "csv=p=0:s=x",
             str(video_in)],
            capture_output=True, text=True, timeout=60)
        _parts = (_dim.stdout or "").strip().split("x")
        if len(_parts) == 2 and int(_parts[0]) > 0 and int(_parts[1]) > 0:
            vw, vh = int(_parts[0]), int(_parts[1])
    except Exception:
        pass
    # Fonte e margem proporcionais à ALTURA real (fontsize=64 foi calibrado p/ 720p;
    # escala linear mantém o mesmo tamanho relativo em qualquer resolução).
    fs = max(24, int(round(fontsize * vh / 720)))
    margin_v = max(24, int(round(60 * vh / 720)))
    # SUB_Y_CENTER (Short de parceiro): o centro da legenda fica nessa altura — em cima da placa que cobriu a deles.
    # Hindi/tailandês vêm por aqui (o Pillow daqui não tem raqm: devanágari/tailandês sairiam com os sinais fora do
    # lugar no PNG; o libass monta certo), com a fonte da língua em ANIME_SUB_FONT_ASS (16/10).
    _yc = os.environ.get("SUB_Y_CENTER")
    if _yc:
        try:
            margin_v = max(10, int(vh * (1 - float(_yc)) - fs * 0.5))
            if vh > vw:  # 30/10: mesmo teto do PNG (_BASE_MAX) — no vertical a base nunca embaixo dos botões do Shorts
                margin_v = max(margin_v, int(vh * (1 - _BASE_MAX)))
        except ValueError:
            pass
    _fonte_cap = os.environ.get("ANIME_SUB_FONT_ASS") or "Impact"
    # Alignment 2 = embaixo-centro; MarginV sobe.
    header = (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        f"PlayResX: {vw}\n"
        f"PlayResY: {vh}\n"
        "WrapStyle: 2\n"
        "ScaledBorderAndShadow: yes\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
        "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
        "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Cap,{_fonte_cap},{fs},&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,"
        f"-1,0,0,0,100,100,0,0,1,4,2,2,40,40,{margin_v},1\n\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    lines = [
        f"Dialogue: 0,{_ass_ts(s)},{_ass_ts(e)},Cap,,0,0,0,,{txt}"
        for (s, e, txt) in events
    ]
    # 23/10: palavra de impacto — enorme no centro ~1 s, pop de entrada e some encolhendo
    try:
        for _n, _t0, _w, _cor, _ex in _escolher_impactos_legenda(imp_cands):
            _p = re.sub(r"[^\w]+$", "", _w).upper()
            _sc = int(min(300, 100 * vw * 0.9 / max(1.0, len(_p) * fs * 0.55)))
            lines.append(
                f"Dialogue: 1,{_ass_ts(_t0)},{_ass_ts(_t0 + _IMPACTO_FIM)},Cap,,0,0,0,,"
                + r"{\an5\pos(%d,%d)\bord%d%s\fscx%d\fscy%d\t(0,100,\fscx%d\fscy%d)\t(100,160,\fscx%d\fscy%d)"
                  r"\fad(0,150)}%s" % (vw // 2, int(vh * 0.42), max(4, int(fs * 0.08)), _cor.strip("{}"), _sc * 55 // 100,
                                       _sc * 55 // 100, _sc * 108 // 100, _sc * 108 // 100, _sc, _sc, _ass_escape(_p)))
    except Exception as e:  # noqa: BLE001
        import logging as _lgi
        _lgi.warning(f"[fx_subtitles] impacto no ASS pulado ({type(e).__name__}: {e})")

    if criativos:  # 01/11: abertura criativa + ênfase com as palavras faladas (anime_gancho.legenda_criativa)
        try:
            import anime_gancho as _ag
            cor = _ag.cor_da_cena(video_in)
            abert = [c["palavras"] + [c["fim"]] for c in criativos if c["abertura"]]
            enfase = [c["palavras"] + [c["fim"]] for c in criativos if not c["abertura"]]
            _est_all, _ln_all = [], []
            if abert:
                e, l = _ag.legenda_criativa(abert, vw, vh, cor, eh_abertura=True)
                _est_all += e; _ln_all += l
            if enfase:
                e, l = _ag.legenda_criativa(enfase, vw, vh, cor, eh_abertura=False)
                _est_all += e; _ln_all += l
            if _est_all:
                seen = set()
                _est_uniq = [s for s in _est_all if not (s in seen or seen.add(s))]
                header = header.replace("\n\n[Events]", "\n" + "\n".join(_est_uniq) + "\n\n[Events]", 1)
            lines += _ln_all
        except Exception as e:  # noqa: BLE001 — falhou = esses cartões voltam como legenda normal
            import logging as _lgc
            _lgc.warning(f"[fx_subtitles] abertura criativa falhou ({type(e).__name__}: {e}) — legenda normal")
            for cart in criativos:
                lines.append(f"Dialogue: 0,{_ass_ts(cart['palavras'][0][0])},{_ass_ts(cart['fim'])},Cap,,0,0,0,,"
                             + "  ".join(_ass_escape(w) for _t, w in cart["palavras"]))
    # 01/11 dona: cartões animados estilo comercial do Instagram (personagem, lugar, sistema, chat, alerta, antes/agora,
    # like) no que a narração fala — mesma passada, custo ~0. marcas_visuais.json = onde cada coisa aparece (prévia)
    marcas = [(c["palavras"][0][0], "legenda_criativa_" + ("abertura" if c["abertura"] else "enfase"),
               " ".join(w for _t, w in c["palavras"])) for c in criativos]
    try:
        import anime_cartoes as _ac
        try:
            import anime_gancho as _ag2
            _cor_c = _ag2.cor_da_cena(video_in, 30)
        except Exception:  # noqa: BLE001
            _cor_c = _ac.OURO
        _e, _l, _m = _ac.gerar(todas, vw, vh, _cor_c)
        if _l:
            header = header.replace("\n\n[Events]", "\n" + "\n".join(_e) + "\n\n[Events]", 1)
            lines += _l
        marcas += _m
        try:  # 01/11: modo do MIX da legenda (inteligente/livre) junto do vídeo pro placar
            import legenda_mix as _lm
            if _lm.ULTIMO_MODO:
                marcas.append((0.0, "legenda_mix_modo", _lm.ULTIMO_MODO))
        except Exception:  # noqa: BLE001
            pass
    except Exception as e:  # noqa: BLE001
        import logging as _lgk
        _lgk.warning(f"[fx_subtitles] cartões animados pulados ({type(e).__name__}: {e})")
    # também em cortes_longo/ (o trabalhador já sobe essa pasta pro Drive — chega no PC sem relançar o Kaggle)
    for _dest in (Path(str(video_out)).with_name("marcas_visuais.json"),
                  Path(str(video_out)).parent / "cortes_longo" / "marcas_visuais.json"):
        try:
            _dest.parent.mkdir(parents=True, exist_ok=True)
            _dest.write_text(json.dumps(sorted(marcas), ensure_ascii=False, indent=0), encoding="utf-8")
            # o trabalhador só sobe cortes_longo/ se tiver cortes.json; a prévia não gera cortes (o melhores_cortes
            # sobrescreve isto nos longos de verdade) — sem ele o "O QUE TESTAR" chegava sem os minutos
            _cj = _dest.parent / "cortes.json"
            if _dest.parent.name == "cortes_longo" and not _cj.exists():
                _cj.write_text("[]", encoding="utf-8")
        except Exception:  # noqa: BLE001
            pass
    # extra(vw, vh, dur) -> (estilos, eventos): gancho/barra do anime_gancho na MESMA passada (16/10)
    if extra:
        try:
            _d = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                 "-of", "csv=p=0", str(video_in)], capture_output=True, text=True, timeout=60)
            _est, _ev = extra(vw, vh, float((_d.stdout or "0").strip() or 0))
            header = header.replace("\n\n[Events]", "\n" + "\n".join(_est) + "\n\n[Events]", 1)
            lines += _ev
        except Exception:
            pass
    ass_path = Path(str(video_out)).with_suffix(".ass")
    ass_path.write_text(header + "\n".join(lines) + "\n", encoding="utf-8")

    # ffmpeg lê o .ass; no filtro `subtitles` o caminho precisa de escape especial
    # no Windows (dois-pontos do drive). Passa relativo ao cwd do processo ffmpeg.
    ass_for_filter = ass_path.name
    try:
        _dur = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", str(video_in)],
            capture_output=True, text=True, timeout=60)
        vdur = float((_dur.stdout or "0").strip() or 0)
    except Exception:
        vdur = 0.0
    to = max(1800, int(vdur * 4) + 600)

    filtro = f"subtitles={ass_for_filter}"
    # 31/10 dona: o YouTube via os longos como 720p ("não está veiculando"). Sobe pra 1080p nesta mesma passada (já
    # reencoda tudo); escala ANTES da legenda = texto renderizado já em 1080p (o libass converte o PlayRes sozinho).
    # 31/10 regra da dona: NENHUM vídeo sai com menos de 1080p (deitado e em pé) — sempre, sem chave pra desligar
    fw, fh = (vw, vh) if min(vw, vh) >= 1080 else ((1920, 1080) if vw >= vh else (1080, 1920))
    _fxv, _mfx = "", None
    try:  # 01/11 V-01/03/04/05/08: efeitos visuais dos edits parceiros, antes do texto (fx_visual)
        import fx_visual
        _mfx = fx_visual.momentos(todas, marcas, _PESADAS.search, vdur, cenas)
        _fxv = fx_visual.filtro(_mfx, fw, fh)
        try:  # prévia: onde cada efeito cai (vai junto no marcas_visuais.json do "O QUE TESTAR")
            _mv = Path(str(video_out)).with_name("marcas_visuais.json")
            _mm_fx = sorted(marcas + [(t, "fx_" + k, k) for k, ts in _mfx.items() for t in ts[:40]])
            for _dest in (_mv, _mv.parent / "cortes_longo" / "marcas_visuais.json"):
                if _dest.exists():
                    _dest.write_text(json.dumps(_mm_fx, ensure_ascii=False, indent=0), encoding="utf-8")
        except Exception:  # noqa: BLE001
            pass
        if _fxv:
            filtro = f"{_fxv},{filtro}"
    except Exception as e:  # noqa: BLE001
        import logging as _lgv
        _lgv.warning(f"[fx_subtitles] efeitos visuais pulados ({type(e).__name__}: {e})")
    if min(vw, vh) < 1080:
        filtro = (f"scale=1920:1080:flags=spline,unsharp=5:5:0.6,{filtro}" if vw >= vh else
                  f"scale=1080:1920:flags=spline,unsharp=5:5:0.6,{filtro}")
    # 25/10: nos trabalhadores Linux (Kaggle/VPS/Colab) não há Impact instalada e a legenda do longo saía em DejaVu;
    # a pasta de fontes dos assets centrais vai junto no pacote (montar_pacote ASSETS "fonts")
    _fontes = Path(__file__).resolve().parent.parent / "workspace" / "assets" / "fonts"
    if _fontes.is_dir():  # 01/11: no Windows também (abertura usa Bangers/Luckiest Guy/Montserrat, que não vêm no sistema)
        filtro += f":fontsdir='{_fontes.as_posix().replace(':', chr(92) + ':')}'"
    # 01/11 dona ("só pro YouTube reconhecer como 1080p60"): 60 fps repetindo quadro DEPOIS da legenda (o libass
    # desenha 30x/s) — medido: +26% nesta passada, ~+5% no longo. ANIME_60FPS=0 desliga.
    fps60 = os.environ.get("ANIME_60FPS", "1") != "0"
    if fps60:
        filtro += ",fps=60"
    entrada_mascote, filtro_v = [], ["-vf", filtro]
    # 02/11: mascote do LONGO (gravações vivas, anime-pipeline._mascote_longo grava _mascote_eventos.json) entra AQUI,
    # na mesma passada, por baixo da legenda — antes era 1 regravação inteira do longo só pra ela
    viva_in, viva_fc, base_rot = [], "", "[0:v]"
    ev_arq = Path(str(video_in)).parent / "_mascote_eventos.json"
    if ev_arq.exists():
        try:
            import mascote_overlay as _mo
            _ev = json.loads(ev_arq.read_text(encoding="utf-8"))
            _r = _mo.filtro_mascote_deitado(_ev, vw, vh, "[0:v]", 1)
            if _r:
                viva_in, _fcs, _ult = _r
                viva_fc = ";".join(_fcs) + ";"
                base_rot = _ult
        except Exception as e:  # noqa: BLE001
            import logging as _lgv2
            _lgv2.warning(f"[fx_subtitles] mascote do longo pulada ({type(e).__name__}: {e})")
            viva_in, viva_fc, base_rot = [], "", "[0:v]"
    try:  # 01/11 dona: no CTA (curtir/comentar/inscrever) a mascote aparece MUDA, só imagem, entrando pelo lado
        _mm = mascote_cta(marcas, video_in, vh > vw)
        if _mm:
            entrada_mascote = ["-i", _mm[0]]
            # a imagem do CTA é a entrada logo depois das gravações vivas
            _fc_cta = _mm[1].replace("[1:v]", f"[{1 + len([x for x in viva_in if x == '-i'])}:v]")
            filtro_v = ["-filter_complex", f"{viva_fc}{base_rot}{filtro}[_b];{_fc_cta}", "-map", "[_v]", "-map",
                        "0:a?"]
        elif viva_fc:
            filtro_v = ["-filter_complex", f"{viva_fc}{base_rot}{filtro}[_v]", "-map", "[_v]", "-map", "0:a?"]
    except Exception as e:  # noqa: BLE001
        import logging as _lgm
        _lgm.warning(f"[fx_subtitles] mascote do CTA pulada ({type(e).__name__}: {e})")
        if viva_fc:
            filtro_v = ["-filter_complex", f"{viva_fc}{base_rot}{filtro}[_v]", "-map", "[_v]", "-map", "0:a?"]
    cmd = [
        "ffmpeg", "-y", "-i", str(video_in), *viva_in, *entrada_mascote,
        *filtro_v,
        # 30/10 (Fable): legenda do longo = 57 min no Top Fighter com "fast"; ANIME_PRESET_LEGENDA (longo.json: veryfast)
        "-c:v", "libx264", "-preset", os.environ.get("ANIME_PRESET_LEGENDA") or QP["preset"], "-crf", str(QP["crf"]),
        "-g", "60" if fps60 else "30",
        "-c:a", "copy", "-movflags", "+faststart", "-pix_fmt", "yuv420p",
        str(video_out),
    ]
    # 22/10 (HUB-03): erro do ffmpeg agora vai pro log + 1 nova tentativa (antes: "falhou" sem motivo)
    ok = False
    # 02/11 (dona: "aproveitar as GPUs / produção"; pesquisa H6 + revisão sonnet): com o encode na GPU, o gargalo desta
    # passada vira o libass/filtros (1 núcleo). ANIME_LEGENDA_FATIAS=N (kaggle_trabalhador põe 4 com NVENC) parte o
    # vídeo em N pedaços que rodam juntos. Falhou qualquer coisa = a passada normal logo abaixo, como sempre.
    try:
        n_fat = int(os.environ.get("ANIME_LEGENDA_FATIAS") or 1)
    except ValueError:
        n_fat = 1
    if n_fat > 1 and vdur >= 600:
        try:
            ok = _queima_em_fatias(cmd, str(video_in), str(video_out), vdur, n_fat, fps60, to, ass_path.parent,
                                   fx=(_fxv, _mfx, fw, fh) if _fxv and _mfx else None)
        except Exception as e:  # noqa: BLE001
            import logging as _lgf
            _lgf.warning(f"[fx_subtitles] fatias falharam ({type(e).__name__}: {e}) — passada única")
            ok = False
    try:
        for _tentativa in (1, 2):
            if ok:
                break
            try:
                subprocess.run(cmd, check=True, capture_output=True, timeout=to, cwd=str(ass_path.parent))
                if Path(video_out).exists() and Path(video_out).stat().st_size > 0:
                    ok = True
                    break
                motivo = "saída vazia"
            except subprocess.CalledProcessError as e:
                motivo = (e.stderr or b"").decode("utf-8", "replace").strip()[-400:]
            except subprocess.TimeoutExpired:
                motivo = f"passou de {to}s"
            import logging as _lg
            _lg.warning(f"[fx_subtitles] queima do ASS falhou (tentativa {_tentativa}): {motivo}")
            if _fxv:  # 01/11: efeito visual quebrou a passada (negate:enable) — a 2ª vai sem ele e salva a legenda MIX
                cmd = [c.replace(f"{_fxv},", "") if isinstance(c, str) else c for c in cmd]
                _lg.warning("[fx_subtitles] 2ª tentativa SEM os efeitos visuais (fx_visual)")
    finally:
        try:
            ass_path.unlink()
        except Exception:
            pass
    return ok


def _queima_em_fatias(cmd, video_in, video_out, vdur, n, fps60, to, cwd, fx=None):
    """Mesma passada (mesmo cmd: filtros + legenda + mascote), em N fatias simultâneas só de VÍDEO, depois junta sem
    reencodar e põe o áudio original de volta. Regras medidas (revisão sonnet 02/11, teste -f null):
    - "-ss A -to B -copyts" ANTES do -i do vídeo: o t dos enable=between(t,..) e da legenda ASS continua o do vídeo
      inteiro (sem -copyts o flash e a legenda saíam deslocados);
    - "setpts=PTS-STARTPTS" no FIM da cadeia (no começo apaga os efeitos);
    - corte em múltiplos de 1/60 s (sem quadro duplicado/faltando na emenda com fps=60);
    - "-an" nas fatias e 1 mux do áudio original no fim (o -c:a copy com -copyts desloca o áudio 5 s)."""
    import logging as _lg
    from concurrent.futures import ThreadPoolExecutor
    passo = 1 / 60.0
    cortes = [round(round(vdur * k / n / passo) * passo, 4) for k in range(n)] + [vdur + 1]
    i_in = cmd.index("-i")
    pasta = Path(video_out).with_suffix("")
    pasta = pasta.parent / (pasta.name + "_fatias")
    pasta.mkdir(exist_ok=True)
    partes = []
    for k in range(n):
        a, b = cortes[k], cortes[k + 1]
        c = list(cmd)
        if fx:  # 02/11: só os efeitos DESTA fatia (o filtro do vídeo inteiro estoura a memória num longo)
            import fx_visual as _fv
            fxv_all, mfx, fw, fh = fx
            novo = _fv.filtro(_fv.recortar(mfx, a, b), fw, fh)
            c = [x.replace(fxv_all, novo) if isinstance(x, str) and fxv_all in x else x for x in c]
        c[i_in:i_in] = ["-ss", f"{a:.4f}", "-to", f"{min(b, vdur + 1):.4f}", "-copyts"]
        if "-filter_complex" in c:
            j = c.index("-filter_complex") + 1
            ultimo = c[c.index("-map") + 1]  # rótulo de saída do vídeo ([_v])
            c[j] = c[j].replace(ultimo, "[_pre]", 1) if c[j].rstrip().endswith(ultimo) else c[j]
            if "[_pre]" in c[j]:
                c[j] += f";[_pre]setpts=PTS-STARTPTS{ultimo}"
            else:
                raise RuntimeError("não achei a saída do filtro pra pôr o setpts")
            m = [x for x in range(len(c)) if c[x] == "-map" and c[x + 1].startswith("0:a")]
            for x in reversed(m):
                del c[x:x + 2]
        else:
            j = c.index("-vf") + 1
            c[j] += ",setpts=PTS-STARTPTS"
        # sem áudio na fatia
        if "-c:a" in c:
            x = c.index("-c:a")
            del c[x:x + 2]
        c.insert(len(c) - 1, "-an")
        saida = str(pasta / f"p{k}.mp4")
        c[-1] = saida
        partes.append((k, c, saida))

    def roda(item):
        k, c, saida = item
        subprocess.run(c, check=True, capture_output=True, timeout=to, cwd=str(cwd))
        return saida

    t0 = __import__("time").time()
    with ThreadPoolExecutor(max_workers=n) as ex:
        feitas = list(ex.map(roda, partes))
    lista = pasta / "lista.txt"
    lista.write_text("".join(f"file '{Path(f).as_posix()}'\n" for f in feitas), encoding="utf-8")
    # 04/11 dona (item 3, "não atrapalha em nada"): o master -14 LUFS era uma passada à parte que reescrevia o arquivo
    # inteiro de novo (13 min no waaQ). A junção já reescreve tudo: aqui mede só o áudio e aplica o MESMO loudnorm
    # linear de 2 passadas (master_loudness) nela. Só quando o pipeline pede (ANIME_MASTER_NA_JUNCAO=1, longo deitado);
    # medir falhou = junta como antes e o pipeline faz o master separado.
    global ULTIMO_MASTER
    ULTIMO_MASTER = None
    audio, medida = ["-c:a", "copy"], None
    if os.environ.get("ANIME_MASTER_NA_JUNCAO") == "1":
        try:
            import master_loudness as _ML
            m = _ML.measure_pass(video_in, -14.0, -1.0)
            af = (f"loudnorm=I=-14.0:TP=-1.0:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
                  f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:"
                  "linear=true:print_format=summary")
            audio = ["-af", af, "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2"]
            medida = m
        except Exception as e:  # noqa: BLE001
            _lg.warning(f"[fx_subtitles] master na junção não mediu ({type(e).__name__}: {e}) — master separado")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lista), "-i", video_in,
                    "-map", "0:v", "-map", "1:a?", "-c:v", "copy", *audio, "-movflags", "+faststart", video_out],
                   check=True, capture_output=True, timeout=3600)
    dur_out = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                    video_out], capture_output=True, text=True, timeout=60).stdout.strip() or 0)
    import shutil as _sh
    _sh.rmtree(pasta, ignore_errors=True)
    if abs(dur_out - vdur) > 1.0:
        raise RuntimeError(f"duração saiu {dur_out:.1f} s (esperado {vdur:.1f})")
    ULTIMO_MASTER = medida  # só depois da junção certa (falhou = o pipeline faz o master separado)
    _lg.info(f"[fx_subtitles] legenda em {n} fatias: {__import__('time').time() - t0:.0f} s"
             + (" (master -14 LUFS na junção)" if medida else ""))
    return True


def render_subtitles_short(entries, tmp_dir, offsets=None, words_per_card=None, word_times=None, falantes=None):
    """Legenda DINÂMICA estilo Shorts/TikTok: 1-2 palavras na tela por vez.

    Em vez de mostrar a frase inteira (render_subtitles_progressive), mostra só
    um grupo de `words_per_card` palavras de cada vez, trocando rápido — deixa o
    vídeo mais dinâmico/moderno. Cada grupo vira 1 PNG curtinho centralizado.

    words_per_card: nº de palavras por card (default lê env SUB_WORDS_PER_CARD, senão 2).
    offsets: timestamps absolutos de início de cada entry (sincronia pós-xfade).
    word_times (WordBoundary): lista alinhada às entries; cada item é [[start,end,word],...]
      REAL do edge-tts (relativo ao clip). Quando presente e casa nº de palavras, usa o
      timing REAL de cada palavra (mata o drift legenda×balão); senão, estimativa por len().
    falantes: [(cor_rgb, nome[, extra]), ...] alinhado às entries (formato com várias vozes, 23/10): a palavra acende
      na cor de quem fala e o nome vai pequeno em cima; extra = ênfase (palavras maiores) e impacto (palavra enorme
      no centro ~1 s, pop de entrada). None = karaokê amarelo de sempre.
    """
    import os as _os
    if words_per_card is None:
        try:
            words_per_card = max(1, int(_os.environ.get("SUB_WORDS_PER_CARD", "2")))
        except ValueError:
            words_per_card = 2
    tmp_dir = Path(tmp_dir)
    subs = []
    imp_cands = []  # 23/10: candidatos a palavra de impacto (nota, início, palavra, cor, extra)
    t = 0.0
    for i, (text, dur) in enumerate(entries):
        dur = max(0.4, float(dur or 0))
        start = offsets[i] if offsets else t
        if not offsets:
            t += dur
        # Limpa pontuação órfã no INÍCIO de cada palavra (ex: vírgula solta que
        # vira ",cerimônia" no card) e descarta tokens só de pontuação. Mesma
        # guarda de burn_subtitles_ass, pra as duas rotas ficarem idênticas.
        words = []
        for _w in (text or "").strip().split():
            _w = _strip_lead_punct(_w)
            if _w:
                words.append(_w)
        if not words:
            continue
        # tempo de cada palavra proporcional ao tamanho (palavra longa dura mais)
        weights = [max(2, len(w)) for w in words]
        total_w = sum(weights)
        word_durs = [dur * (wt / total_w) for wt in weights]
        # WordBoundary: timing REAL de cada palavra (relativo ao clip) se veio o sidecar
        # e o nº de palavras casa. Mata o drift legenda×balão.
        wt_real = None
        if word_times and i < len(word_times) and word_times[i]:
            wt_real = _alinhar_tempos(words, word_times[i])
        quem, enf, cor_pal = {}, [], {}
        if falantes and i < len(falantes) and falantes[i]:  # 23/10: cor/nome de quem fala
            quem = {"highlight_color": tuple(falantes[i][0]), "rotulo": falantes[i][1] or None}
            extra = falantes[i][2] if len(falantes[i]) > 2 and falantes[i][2] else {}
            enf = list(extra.get("enfase") or [])
            cor_pal = {int(k): tuple(c) for k, c in (extra.get("cores") or {}).items()}  # 28/10: nome = cor dele
            if enf:
                quem["escala"] = float(extra.get("escala", 1.3))
            _imp = extra.get("impacto")
            if _imp and 0 <= _imp[0] < len(words):
                _t0 = start + (wt_real[_imp[0]][0] if wt_real else sum(word_durs[:_imp[0]]))
                imp_cands.append((float(_imp[1]), _t0, words[_imp[0]], quem["highlight_color"], extra))
        # agrupa em cards de N palavras; cada palavra do card ACENDE amarelo no seu tempo
        _isol = [extra["impacto"][0]] if (falantes and i < len(falantes) and falantes[i] and len(falantes[i]) > 2
                                          and (falantes[i][2] or {}).get("impacto")) else []
        for g, _fim in cartoes_por_sentido(words, words_per_card, _isol):  # 28/10: por sentido (Hypit)
            grp = words[g:_fim]
            card_text = " ".join(grp)
            for local_idx in range(len(grp)):
                png = tmp_dir / f"_capshort_{i:03d}_{g:03d}_{local_idx}.png"
                # highlight_idx é relativo ao card_text (que começa na palavra g)
                _e = [k - g for k in enf if g <= k < g + len(grp)]  # ênfase dentro deste card
                _c = {k - g: c for k, c in cor_pal.items() if g <= k < g + len(grp)}
                res = _render_caption_png(card_text, png, highlight_idx=local_idx, **quem, **({"enfase": _e} if _e else {}),
                                          **({"cores": _c} if _c else {}))
                if not res:
                    continue
                _, x, y = res
                gi = g + local_idx
                if wt_real:
                    w_start = start + wt_real[gi][0]
                    w_end = start + wt_real[gi][1]
                else:
                    w_start = start + sum(word_durs[:gi])
                    w_end = start + sum(word_durs[:gi + 1])
                subs.append({"png": str(png), "x": x, "y": y, "start": w_start, "end": w_end})
    # 28/10: a última palavra de uma frase terminava DEPOIS do início da seguinte -> os 2 cartões ficavam ~0,3 s um em
    # cima do outro ("pr[Vinte anos]dr." no T-Rex). Cada cartão sai quando o próximo entra.
    for _a, _b in zip(subs, subs[1:]):
        if _b["start"] > _a["start"]:
            _a["end"] = min(_a["end"], _b["start"])
    # 23/10: palavras de impacto por cima de tudo (quadros da animação; falhou = segue sem)
    try:
        _lat = os.environ.get("CORTES_LEGENDA_ESTILO") == "lateral"  # 27/10: teste T3 (centro x lateral)
        _esc = _escolher_impactos_legenda(imp_cands)
        if os.environ.get("CORTES_FX_CHOQUE") == "B":
            subs += _fx_choque([c[1] for c in _esc], offsets or [], tmp_dir, entries[0][0] if entries else "")
        for n_imp, (_n, _t0, _w, _cor, _ex) in enumerate(_esc):
            for q, (dt, zoom, alfa) in enumerate(_IMPACTO_QUADROS):
                fim = _IMPACTO_QUADROS[q + 1][0] if q + 1 < len(_IMPACTO_QUADROS) else _IMPACTO_FIM
                res = _render_impacto_png(_w, tmp_dir / f"_impacto_{n_imp}_{q}.png", _cor, zoom, alfa,
                                          lateral=n_imp if _lat else None)
                if res:
                    subs.append({"png": str(res[0]), "x": res[1], "y": res[2], "start": _t0 + dt, "end": _t0 + fim})
    except Exception as e:  # noqa: BLE001
        import logging as _lg
        _lg.warning(f"[fx_subtitles] palavra de impacto pulada ({type(e).__name__}: {e})")
    return subs


def burn_subtitles(video_in, subs, video_out, max_overlays_per_pass=30):
    """Sobrepõe os PNGs de legenda no vídeo em MÚLTIPLAS PASSADAS.

    O FFmpeg não suporta mais de ~100 overlays PNG numa única filter_complex
    (a cadeia de overlay fica enorme e o parser do FFmpeg estoura).

    SOLUÇÃO: divide os overlays em lotes de max_overlays_per_pass (default 30)
    e aplica em passadas sequenciais. Cada passada recebe o output da anterior.
    """
    if not subs:
        return False

    # Defesa: este burner é só de PNG. Ignora entradas sem "png" (ex: overlays webm
    # do karaokê HyperFrames, que são queimados em outro caminho) — evita KeyError 'png'.
    subs = [s for s in subs if isinstance(s, dict) and s.get("png")]
    if not subs:
        return False

    MAX_PER_PASS = max(max_overlays_per_pass, 100)  # Aumentado de 30 pra 100 (reduz passadas)
    batches = [subs[i:i + MAX_PER_PASS] for i in range(0, len(subs), MAX_PER_PASS)]
    temp_dir = Path(str(video_out)).parent
    temp_input = str(video_in)
    temp_outputs = []

    # Cada passada re-encoda o vídeo INTEIRO. Pra vídeos longos (recap 40min+ com
    # centenas de legendas = muitas passadas) o timeout fixo de 30min estourava e
    # o CRF empilhava perda geracional. Fix:
    #  - timeout proporcional à duração (mede via ffprobe, com folga 3x + base).
    #  - passadas INTERMEDIÁRIAS: preset veloz + CRF quase-lossless (sem perda
    #    visível ao empilhar); só a passada FINAL usa a qualidade do perfil.
    try:
        _pr = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", str(video_in)],
            capture_output=True, text=True, timeout=60,
        )
        _dur = float((_pr.stdout or "0").strip() or 0)
    except Exception:
        _dur = 0.0
    # ~3x a duração por passada + 10min de base; nunca menos que 30min.
    pass_timeout = max(1800, int(_dur * 3) + 600)

    n_batches = len(batches)
    for batch_idx, batch in enumerate(batches):
        is_last = batch_idx == n_batches - 1
        if is_last:
            # Último batch → output final (qualidade do perfil)
            current_out = str(video_out)
            preset = QP["preset"]
            crf = str(QP["crf"])
        else:
            # Batch intermediário → arquivo temporário quase-lossless e rápido
            current_out = str(temp_dir / f"_subs_batch_{batch_idx:02d}.mp4")
            temp_outputs.append(current_out)
            preset = "veryfast"
            crf = "18"  # visualmente sem perda ao empilhar, ~metade do tamanho de crf12 (poupa disco)

        inputs = ["-i", temp_input]
        for s in batch:
            inputs += ["-i", s["png"]]

        parts = []
        cur = "[0:v]"
        for idx, s in enumerate(batch, start=1):
            out = f"[v{idx}]"
            parts.append(
                f"{cur}[{idx}:v]overlay={s.get('x', 0)}:{s.get('y', 0)}:"
                f"enable='between(t,{s['start']:.2f},{s['end']:.2f})'{out}"
            )
            cur = out

        filter_complex = ";".join(parts)
        cmd = [
            "ffmpeg", "-y", *inputs,
            "-filter_complex", filter_complex,
            "-map", cur, "-map", "0:a?",
            "-c:v", "libx264", "-preset", preset, "-crf", crf, "-g", "30",
            "-c:a", "copy",
            "-movflags", "+faststart", "-pix_fmt", "yuv420p",
            current_out,
        ]
        # 21/10: o erro do ffmpeg era descartado ("burn_subtitles falhou" sem motivo, ~4 Shorts sem legenda em 20/10):
        # agora vai pro log e a passada é tentada 2x (falha passageira: disco cheio, arquivo preso)
        for tentativa in (1, 2):
            try:
                subprocess.run(cmd, check=True, capture_output=True, timeout=pass_timeout)
                if Path(current_out).exists() and Path(current_out).stat().st_size > 0:
                    break
                motivo = "saída vazia"
            except subprocess.CalledProcessError as e:
                motivo = (e.stderr or b"").decode("utf-8", "replace").strip()[-400:]
            except subprocess.TimeoutExpired:
                motivo = f"passou de {pass_timeout}s"
            import logging as _lg
            _lg.warning(f"[captions] passada {batch_idx + 1}/{n_batches} falhou (tentativa {tentativa}): {motivo}")
        else:
            return False

        # Cleanup incremental: o input desta passada (batch anterior) já foi
        # consumido — apaga JÁ pra não acumular vários intermediários de ~500MB
        # no disco ao mesmo tempo (vídeos longos = muitas passadas). Nunca apaga
        # o vídeo de entrada original (só os _subs_batch_ temporários).
        prev = temp_input
        if prev in temp_outputs:
            try:
                Path(prev).unlink()
            except Exception:
                pass

        # Próxima passada usa o output atual como input
        temp_input = current_out

    # Cleanup final: remove qualquer temporário que tenha sobrado.
    for t in temp_outputs:
        try:
            Path(t).unlink()
        except Exception:
            pass

    return Path(video_out).exists() and Path(video_out).stat().st_size > 0
