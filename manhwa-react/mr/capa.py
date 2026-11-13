"""Capas no estilo de capa de manhwa/anime (nao um frame cru do video).

- Personagem: amostras do trecho -> folha numerada -> LLM com visao escolhe o quadro mais forte (rosto grande, emocao,
  nitidez) e diz onde esta o rosto do personagem (foco do recorte). Sem LLM: o quadro mais colorido e nitido.
  O quadro escolhido e realcado (contraste, cor, nitidez) e preenche a capa.
- Criador: maior abertura de boca no trecho (labios), rosto recortado pelo MediaPipe dentro da webcam, num circulo com
  brilho na cor do canal.
- Texto: gancho curto em letras grandes (branco/amarelo, contorno preto), tamanho ajustado para caber.
Short 1080x1920 (capa_short) e video grande 1280x720 (capa_grande).
"""
import base64
import io
import json
import re
import urllib.request
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from .common import log, load_json
from . import limitador

PROMPT_QUADRO = """Esta folha tem {n} quadros numerados (1 a {n}) de um video de {tipo}. Escolha o MELHOR para virar capa de YouTube
no estilo das capas de manhwa/anime: personagem grande e nitido, rosto expressivo, emocao forte (choque, raiva, poder, medo).
Evite: quadro com muito texto/balao, tela escura ou borrada, cena vazia, transicao.
Responda SO JSON: {{"quadro": numero, "foco_x": 0.0-1.0, "foco_y": 0.0-1.0, "motivo": "curto"}}
foco_x/foco_y = posicao do rosto do personagem DENTRO do quadro escolhido (0,0 = canto superior esquerdo)."""

# Variantes A/B/C da capa do video longo para o "Testar e comparar" do Studio (18/10, copiado de
# D:\historias-em-frames\bin\thumbnail_pro.py): A = capa de sempre (controle); B = degrade vertical na cor do genero;
# C = escurece da esquerda para a direita. Em B/C o texto vai na cor do genero.
GENRE_COLORS = {
    "superacao": {"gradient": [(255, 180, 0, 200), (255, 80, 0, 220)], "text": (255, 255, 255)},
    "terror": {"gradient": [(20, 0, 0, 220), (80, 0, 0, 200)], "text": (255, 50, 50)},
    "misterio": {"gradient": [(0, 20, 50, 220), (0, 50, 80, 200)], "text": (100, 200, 255)},
    "motivacional": {"gradient": [(0, 80, 150, 180), (0, 40, 100, 220)], "text": (255, 255, 255)},
    "curiosidades": {"gradient": [(50, 0, 100, 200), (100, 0, 180, 220)], "text": (255, 220, 50)},
    "religioso": {"gradient": [(80, 60, 0, 180), (40, 30, 0, 220)], "text": (255, 230, 150)},
    "romance": {"gradient": [(150, 0, 80, 200), (80, 0, 50, 220)], "text": (255, 180, 200)},
    "comedia": {"gradient": [(0, 100, 0, 180), (0, 60, 0, 200)], "text": (255, 255, 0)},
    "drama": {"gradient": [(30, 30, 30, 220), (60, 40, 20, 200)], "text": (255, 255, 255)},
    "fantasia": {"gradient": [(30, 0, 80, 200), (80, 0, 150, 220)], "text": (200, 150, 255)},
}
GENERO_PALAVRAS = [  # ordem importa: o primeiro que bate no titulo/tags decide
    ("terror", ("terror", "horror", "zumbi", "assombra")),
    ("romance", ("romance", "amor", "casal", "namorad", "casamento", "beijo")),
    ("comedia", ("comedia", "comédia", "engraçad", "humor", "kkk")),
    ("misterio", ("mistério", "misterio", "segredo", "investiga", "detetive")),
    ("superacao", ("superação", "superacao", "mais fraco", "vingança", "renasceu", "humilhad")),
    ("fantasia", ("fantasia", "magia", "mago", "reencarn", "isekai", "demônio", "demonio", "dragão", "dragao",
                  "sistema", "masmorra", "dungeon", "cavaleiro", "rei ")),
    ("drama", ("drama", "triste", "chor")),
]
# B tinge o painel inteiro: com o alfa do thumbnail_pro (200-220, feito para fundo atras de texto) o personagem sumia
ALFA_B = 0.45


def genero_de(*textos):
    t = " ".join(str(x) for x in textos if x).casefold() + " "
    return next((g for g, pals in GENERO_PALAVRAS if any(p in t for p in pals)), "drama")


def caminhos_ab(out):
    """[A, B, C] da capa, so os que existem (B e C ficam ao lado: <nome>_b.jpg, <nome>_c.jpg)."""
    out = Path(out)
    return [p for p in (out, out.with_name(f"{out.stem}_b{out.suffix}"), out.with_name(f"{out.stem}_c{out.suffix}"))
            if p.exists()]


def _tratamento(canvas, variante, genero):
    W, H = canvas.size
    camada = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(camada)
    if variante == "B":
        c1, c2 = GENRE_COLORS[genero]["gradient"]
        for y in range(H):
            f = y / H
            r, g, b, a = (int(x * (1 - f) + z * f) for x, z in zip(c1, c2))
            d.line([(0, y), (W, y)], fill=(r, g, b, int(a * ALFA_B)))
    else:
        for x in range(W):
            d.line([(x, 0), (x, H)], fill=(0, 0, 0, int(240 * x / W)))
    out = canvas.copy()
    out.alpha_composite(camada)
    return out


def _hex(h, default=(255, 45, 85)):
    try:
        h = h.lstrip("#")
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    except Exception:  # noqa: BLE001
        return default


def _frame(video, t):
    import cv2
    cap = cv2.VideoCapture(str(video))
    cap.set(cv2.CAP_PROP_POS_MSEC, max(0.0, t) * 1000)
    ok, f = cap.read()
    cap.release()
    return Image.fromarray(cv2.cvtColor(f, cv2.COLOR_BGR2RGB)) if ok else None


def _caixa_conteudo(layout):
    """Regiao do conteudo sem a webcam."""
    x0, y0, x1, y1 = layout["content"]
    if layout.get("mode") == "pip" and layout.get("webcam"):
        wx0, _, wx1, _ = layout["webcam"]
        if wx0 > layout["width"] / 2:
            x1 = min(x1, wx0)
        elif wx1 < layout["width"] / 2:
            x0 = max(x0, wx1)
    return [x0, y0, x1, y1]


def _amostras(video, box, t0, t1, n=9):
    out = []
    for t in np.linspace(t0 + (t1 - t0) * 0.06, t1 - (t1 - t0) * 0.06, n):
        im = _frame(video, float(t))
        if im is not None:
            out.append((float(t), im.crop(tuple(box))))
    return out


def mascara_marca(video, box, duracao, n=14):
    """Marca d'agua/logo do canal reagido: pixels que ficam IGUAIS e com borda forte ao longo do video inteiro,
    nas faixas de cima/baixo. Devolve mascara (PIL L, do tamanho da caixa) ou None."""
    import cv2
    am = _amostras(video, box, 0, duracao, n=n)
    if len(am) < 6:
        return None
    w0, h0 = am[0][1].size
    lw = 640
    lh = int(lw * h0 / w0)
    g = np.stack([np.asarray(im.convert("L").resize((lw, lh)), np.float32) for _, im in am])
    med = np.median(g, axis=0)
    # parado na MAIORIA dos quadros (a marca pode sumir na abertura/encerramento ou quando o video e pausado)
    parado = (np.abs(g - med) < 12).mean(axis=0) > 0.7
    borda = np.hypot(*np.gradient(med)) > 22
    m = (parado & borda).astype(np.uint8)
    faixa = np.zeros_like(m)
    faixa[: int(lh * 0.22)] = 1
    faixa[int(lh * 0.8):] = 1
    m = m * faixa
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 9), np.uint8))
    n_c, lab, st, _ = cv2.connectedComponentsWithStats(m)
    out = np.zeros_like(m)
    for i in range(1, n_c):
        x, y, w, h, area = st[i]
        if area >= 40 and w >= 12 and h >= 6 and w < lw * 0.8 and w * h < lw * lh * 0.08:  # sem a linha da borda do quadro
            out[lab == i] = 255
    if not out.any():
        return None
    out = cv2.dilate(out, np.ones((7, 7), np.uint8))
    ys, xs = np.nonzero(out)
    log(f"capa: marca d'agua do video reagido em x={int(xs.min() * w0 / lw)}-{int(xs.max() * w0 / lw)}, "
        f"y={int(ys.min() * h0 / lh)}-{int(ys.max() * h0 / lh)} (sera apagada)")
    return Image.fromarray(out).resize((w0, h0))


def tirar_marca(quadro, mascara):
    if mascara is None:
        return quadro
    import cv2
    a = cv2.cvtColor(np.asarray(quadro.convert("RGB")), cv2.COLOR_RGB2BGR)
    m = np.asarray(mascara.resize(quadro.size))
    a = cv2.inpaint(a, (m > 0).astype(np.uint8) * 255, 9, cv2.INPAINT_TELEA)
    return Image.fromarray(cv2.cvtColor(a, cv2.COLOR_BGR2RGB))


def cortar_marca(quadro, mascara, fy):
    """Marca d'agua na faixa de cima/baixo: corta a faixa inteira (mais limpo que apagar letra por letra).
    No meio da imagem: apaga (inpaint). Devolve (quadro, foco_y ajustado)."""
    if mascara is None:
        return quadro, fy
    m = np.asarray(mascara.resize(quadro.size)) > 0
    ys = np.nonzero(m.any(axis=1))[0]
    if not len(ys):
        return quadro, fy
    H = quadro.height
    if ys.max() < H * 0.25:
        topo = int(ys.max()) + 12
        return quadro.crop((0, topo, quadro.width, H)), min(max((fy * H - topo) / (H - topo), 0.0), 1.0)
    if ys.min() > H * 0.75:
        base = int(ys.min()) - 12
        return quadro.crop((0, 0, quadro.width, base)), min(max(fy * H / base, 0.0), 1.0)
    return tirar_marca(quadro, mascara), fy


def _limites_painel(im, minimo=0.45):
    """Recaps de manhwa mostram o painel no meio e fundo borrado dos lados (com a marca d'agua do canal original).
    A borda do painel e uma linha vertical reta que atravessa quase a altura toda: coluna em que a maioria das linhas
    tem um degrau forte de brilho. Devolve (x0, x1) do painel, ou None se nao houver as duas bordas."""
    lw = 640
    g = np.asarray(im.convert("L").resize((lw, max(1, int(lw * im.height / im.width)))), np.float32)
    dx = np.abs(np.diff(g, axis=1))
    cont = (dx > 10).mean(axis=0)                      # fracao das linhas com degrau em cada coluna
    cont = np.maximum(cont, np.roll(cont, 1))          # borda pode cair entre duas colunas
    meio = lw // 2
    xe = int(np.argmax(cont[4:meio])) + 4
    xd = int(np.argmax(cont[meio:lw - 5])) + meio
    if cont[xe] < minimo or cont[xd] < minimo or not (0.2 * lw < xd - xe < 0.92 * lw):
        return None
    s = im.width / lw
    return int((xe + 2) * s), int((xd - 1) * s)


def _recortar_painel(quadro, fx):
    lim = _limites_painel(quadro)
    if not lim:
        return quadro, fx
    x0, x1 = lim
    log(f"capa: painel nitido em x={x0}-{x1} de {quadro.width} (fundo borrado e marca d'agua de fora)")
    fx = min(max((fx * quadro.width - x0) / max(1, x1 - x0), 0.0), 1.0)
    return quadro.crop((x0, 0, x1, quadro.height)), fx

def _nota(im):
    """Heuristica sem LLM: cor + nitidez + contraste."""
    a = np.asarray(im.convert("RGB").resize((256, int(256 * im.height / im.width))), np.float32)
    rg, yb = a[..., 0] - a[..., 1], (a[..., 0] + a[..., 1]) / 2 - a[..., 2]
    cor = np.sqrt(rg.std() ** 2 + yb.std() ** 2) + 0.3 * np.sqrt(rg.mean() ** 2 + yb.mean() ** 2)
    g = a.mean(axis=2)
    nitidez = np.abs(np.diff(g, axis=0)).mean() + np.abs(np.diff(g, axis=1)).mean()
    return cor + 2.0 * nitidez + 0.3 * g.std()


def _visao(cfg, jpeg, prompt, tier="sonnet"):
    from .llm import _proxy, extract_json
    px = _proxy(cfg)
    base, key = (px.get("base_url") or "").rstrip("/"), px.get("auth_token")
    models = dict(cfg["editorial"].get("models", {}))
    models.update({k: v for k, v in (px.get("models") or {}).items() if v})
    model = models.get(tier) or models.get("sonnet")
    if not base or not key or not model or limitador.restante(f"proxy_{tier}"):
        return None
    body = {"model": model, "max_tokens": 300, "temperature": 0.2, "messages": [{"role": "user", "content": [
        {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": base64.b64encode(jpeg).decode()}},
        {"type": "text", "text": prompt}]}]}
    req = urllib.request.Request(base + "/v1/messages", data=json.dumps(body).encode("utf-8"), headers={
        "x-api-key": key, "Authorization": f"Bearer {key}", "anthropic-version": "2023-06-01", "content-type": "application/json"})
    try:
        d = json.loads(urllib.request.urlopen(req, timeout=120).read().decode("utf-8"))
    except Exception as e:  # noqa: BLE001
        log(f"capa: visao falhou ({str(e)[:100]})")
        if not any(c in str(e) for c in ("401", "403", "404")):
            limitador.falhou(f"proxy_{tier}", str(e))
        return None
    limitador.ok(f"proxy_{tier}")
    return extract_json("".join(b.get("text", "") for b in d.get("content", []) if b.get("type") == "text"))


def escolher_quadro(cfg, amostras, tipo="react de manhwa/anime"):
    """(imagem, foco_x, foco_y) do melhor quadro."""
    cw, ch = 400, 300
    cols = 3
    rows = (len(amostras) + cols - 1) // cols
    folha = Image.new("RGB", (cw * cols, ch * rows), (0, 0, 0))
    d = ImageDraw.Draw(folha)
    try:
        f = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 44)
    except Exception:  # noqa: BLE001
        f = ImageFont.load_default()
    for i, (_, im) in enumerate(amostras):
        c = im.copy()
        c.thumbnail((cw - 6, ch - 6))
        x, y = (i % cols) * cw, (i // cols) * ch
        folha.paste(c, (x + (cw - c.width) // 2, y + (ch - c.height) // 2))
        d.rectangle([x + 4, y + 4, x + 58, y + 56], fill=(255, 220, 0))
        d.text((x + 14, y + 6), str(i + 1), font=f, fill=(0, 0, 0))
    buf = io.BytesIO()
    folha.save(buf, "JPEG", quality=85)
    r = _visao(cfg, buf.getvalue(), PROMPT_QUADRO.format(n=len(amostras), tipo=tipo))
    try:
        i = int(r["quadro"]) - 1
        if 0 <= i < len(amostras):
            fx = min(max(float(r.get("foco_x", 0.5)), 0.0), 1.0)
            fy = min(max(float(r.get("foco_y", 0.4)), 0.0), 1.0)
            log(f"capa: quadro {i + 1}/{len(amostras)} escolhido pela visao ({r.get('motivo', '')[:60]})")
            return amostras[i][1], fx, fy
    except Exception:  # noqa: BLE001
        pass
    melhor = max(amostras, key=lambda a: _nota(a[1]))
    return melhor[1], 0.5, 0.4


def _realcar(im):
    im = ImageEnhance.Contrast(im).enhance(1.15)
    im = ImageEnhance.Color(im).enhance(1.3)
    im = im.filter(ImageFilter.UnsharpMask(radius=2, percent=110, threshold=2))
    return im


def _cover_foco(im, w, h, fx=0.5, fy=0.5, zoom=1.0):
    esc = max(w / im.width, h / im.height) * zoom
    nw, nh = int(im.width * esc + 0.5), int(im.height * esc + 0.5)
    im = im.resize((nw, nh), Image.LANCZOS)
    x = int(min(max(fx * nw - w / 2, 0), nw - w))
    y = int(min(max(fy * nh - h / 2, 0), nh - h))
    return im.crop((x, y, x + w, y + h))


def _tempos_reacao(work, t0, t1, n=8):
    """Momentos de boca mais aberta do criador no trecho (lips.json do pipeline), do maior para o menor, espacados;
    sem lips: pontos espalhados no trecho."""
    p = Path(work) / "lips.json" if work else None
    tempos = []
    if p and p.exists():
        serie = sorted(((t, v) for t, v in load_json(p) if v is not None and t0 <= t <= t1), key=lambda x: -x[1])
        for t, _ in serie:
            if all(abs(t - u) > 2.0 for u in tempos):
                tempos.append(t)
            if len(tempos) >= n:
                break
    return tempos + [float(x) for x in np.linspace(t0, t1, n + 2)[1:-1]]


def rosto_criador(cfg, video, layout, tempos, lado):
    """Rosto do criador no primeiro momento (da lista) em que o rosto aparece de verdade na webcam."""
    from .channels import _face_box
    if not layout.get("webcam"):
        return None
    for t in tempos:
        im = _frame(video, t)
        if im is None:
            continue
        cam = im.crop(tuple(layout["webcam"]))
        box = _face_box(cfg, cam)
        if box and (box[2] - box[0]) > cam.width * 0.08:
            break
    else:
        return None
    x0, y0, x1, y1 = box
    s = int(max(x1 - x0, y1 - y0) * 1.9)
    cx, cy = (x0 + x1) / 2, y0 + (y1 - y0) * 0.45
    s = min(s, cam.width, cam.height)
    x = int(min(max(cx - s / 2, 0), cam.width - s))
    y = int(min(max(cy - s / 2, 0), cam.height - s))
    face = _realcar(cam.crop((x, y, x + s, y + s)).resize((lado, lado), Image.LANCZOS))
    return face


def _circulo_com_brilho(face, cor, borda=12):
    s = face.width
    pad = 60
    out = Image.new("RGBA", (s + 2 * pad, s + 2 * pad), (0, 0, 0, 0))
    glow = Image.new("RGBA", out.size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse([pad - 16, pad - 16, pad + s + 16, pad + s + 16], fill=cor + (230,))
    out.alpha_composite(glow.filter(ImageFilter.GaussianBlur(22)))
    mask = Image.new("L", (s * 4, s * 4), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, s * 4 - 1, s * 4 - 1], fill=255)
    mask = mask.resize((s, s), Image.LANCZOS)
    out.paste(face, (pad, pad), mask)
    ImageDraw.Draw(out).ellipse([pad, pad, pad + s - 1, pad + s - 1], outline=cor, width=borda)
    return out


def _fonte(cfg, size):
    p = Path(cfg["paths"]["assets"]) / "fonts" / cfg.get("thumb", {}).get("font", "LuckiestGuy-Regular.ttf")
    try:
        return ImageFont.truetype(str(p), size)
    except Exception:  # noqa: BLE001
        return ImageFont.truetype("C:/Windows/Fonts/impact.ttf", size)


def _quebrar(draw, texto, fonte, largura, max_linhas=3):
    """Menor numero de linhas que cabe; entre as divisoes possiveis, a de linhas mais parecidas
    ("PRISAO DO / REI DEMONIO" em vez de "PRISAO DO REI / DEMONIO")."""
    from itertools import combinations
    ws = texto.split()
    if not ws:
        return []
    for k in range(1, min(max_linhas, len(ws)) + 1):
        melhor = None
        for cortes in combinations(range(1, len(ws)), k - 1):
            idx = (0,) + cortes + (len(ws),)
            linhas = [" ".join(ws[a:b]) for a, b in zip(idx, idx[1:])]
            larg = max(draw.textlength(ln, font=fonte) for ln in linhas)
            if larg <= largura and (melhor is None or larg < melhor[0]):
                melhor = (larg, linhas)
        if melhor:
            return melhor[1]
    linhas, cur = [], ""
    for w in ws:
        tt = (cur + " " + w).strip()
        if draw.textlength(tt, font=fonte) <= largura or not cur:
            cur = tt
        else:
            linhas.append(cur)
            cur = w
    return linhas + ([cur] if cur else [])


def _texto(cfg, canvas, texto, caixa, tam_max, tam_min, max_linhas=3, cores=((255, 255, 255), (255, 212, 0))):
    """Escreve o gancho dentro da caixa (x0, y0, x1, y1), do maior tamanho que cabe; linhas alternam branco/amarelo."""
    if not texto:
        return
    x0, y0, x1, y1 = caixa
    d = ImageDraw.Draw(canvas)
    texto = texto.upper().strip()
    for size in range(tam_max, tam_min - 1, -6):
        f = _fonte(cfg, size)
        linhas = _quebrar(d, texto, f, x1 - x0, max_linhas)
        lh = int(size * 1.05)
        if len(linhas) <= max_linhas and lh * len(linhas) <= y1 - y0:
            break
    linhas = linhas[:max_linhas]
    y = y1 - lh * len(linhas)
    traco = max(6, size // 10)
    for i, ln in enumerate(linhas):
        tw = d.textlength(ln, font=f)
        x = x0 + ((x1 - x0) - tw) / 2
        d.text((x + 6, y + 8), ln, font=f, fill=(0, 0, 0), stroke_width=traco, stroke_fill=(0, 0, 0))
        d.text((x, y), ln, font=f, fill=cores[i % len(cores)], stroke_width=traco, stroke_fill=(0, 0, 0))
        y += lh


def _degrade(w, h, y_ini, alfa_max=215):
    g = Image.new("L", (1, h), 0)
    for y in range(h):
        g.putpixel((0, y), 0 if y < y_ini else int(alfa_max * min(1.0, (y - y_ini) / max(1, (h - y_ini) * 0.55))))
    preto = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    preto.putalpha(g.resize((w, h)))
    return preto


MASCOTE_DIR = Path(r"D:\hipercool-materiais\assets\mascote")
MASCOTE_POSES = ("point", "shock", "love", "cheer", "shy", "laugh", "popcorn", "angry", "thumbsup")


def _largura_mascote(W, H, alto):
    """Largura (px) do canto que a mascote ocupa: a pose mais larga do banco tem ~0,58 da altura + contorno e margem.
    O texto da capa fica fora dessa coluna (31/10: no Short e na capa A o título saía embaixo da figurinha)."""
    return int(H * alto * 0.62 + W * 0.03)


def _colar_mascote(capa, semente="", lado="direita", alto=0.42):
    """Cola a mascote (contorno branco de figurinha + sombra) no canto da imagem."""
    import hashlib
    import os
    if os.environ.get("CAPA_MASCOTE", "1") == "0":
        return None
    poses = [p for p in MASCOTE_POSES if (MASCOTE_DIR / f"pose_{p}.png").exists()]
    if not poses:
        return None
    pose = poses[int(hashlib.md5(str(semente).encode()).hexdigest(), 16) % len(poses)]
    m = Image.open(MASCOTE_DIR / f"pose_{pose}.png").convert("RGBA")
    m = m.crop(m.getbbox() or (0, 0, m.width, m.height))
    W, H = capa.size
    h = int(H * alto)
    m = m.resize((max(1, int(m.width * h / m.height)), h), Image.LANCZOS)
    borda = max(4, h // 60)
    a = m.getchannel("A").filter(ImageFilter.MaxFilter(borda * 2 + 1))
    fig = Image.new("RGBA", (m.width + 2 * borda, m.height + 2 * borda), (0, 0, 0, 0))
    branco = Image.new("RGBA", fig.size, (255, 255, 255, 255))
    alfa = Image.new("L", fig.size, 0)
    alfa.paste(a, (borda, borda))
    fig.paste(branco, (0, 0), alfa)
    fig.alpha_composite(m, (borda, borda))
    sombra = Image.new("RGBA", fig.size, (0, 0, 0, 0))
    sombra.putalpha(alfa.point(lambda v: v * 0.55).filter(ImageFilter.GaussianBlur(borda * 2)))
    x = W - fig.width - int(W * 0.015) if lado == "direita" else int(W * 0.015)
    y = H - fig.height + int(fig.height * 0.06)
    base = capa.convert("RGBA")
    base.alpha_composite(sombra, (max(0, int(x + borda)), max(0, min(H - 1, int(y + borda)))))
    base.alpha_composite(fig, (max(0, int(x)), max(0, int(y))))
    if capa.mode == "RGBA":
        capa.paste(base, (0, 0))
    else:
        capa.paste(base.convert("RGB"), (0, 0))
    return pose


_ETIQUETAS = [
    ("YANDERE", r"yandere|obcecad|obsess|possessiv"), ("HARÉM", r"har[eé]m|esposas|noivas"),
    ("RANK S", r"rank[- ]?s\b|classe s|s-rank"), ("ISEKAI", r"isekai|outro mundo|transportad|invocad"),
    ("REGRESSÃO", r"regress|voltou no tempo|segunda chance"), ("REENCARNOU", r"renasc|reencarn"),
    ("VILÃ", r"\bvil[ãa]\b"),
    ("DEMÔNIA", r"dem[ôo]ni[ao]|s[uú]cubo"), ("ELFA", r"\belf[ao]s?\b"), ("RAINHA", r"rainha|imperatriz|princesa"),
    ("DEUSA", r"\bdeusa"), ("ASSASSINA", r"assassin"), ("NERD", r"\bnerd\b"), ("O MAIS FRACO", r"mais frac|fracot"),
    ("APAIXONADA", r"apaixon|se apaixonou|amor"),
]

_PAPEIS = [("RANK S", r"rank[- ]?s\b|classe s|s-rank|mais forte|invenc"), ("O MAIS FRACO", r"mais frac|fracot|n[ií]vel 1|level 1"),
           ("REGRESSOR", r"regress|voltou no tempo|segunda chance"), ("REENCARNADO", r"renasc|reencarn"),
           ("NERD", r"\bnerd\b"), ("VILÃO", r"\bvil[ãa]o\b"), ("GÊNIO", r"g[eê]nio"), ("REI", r"\brei\b|imperador")]


def _papel(texto="", cena=""):
    t = f"{cena} {texto}".lower()
    return next((p for p, rx in _PAPEIS if re.search(rx, t)), "PROTA")


def _etiqueta(texto="", cena=""):
    t = f"{cena} {texto}".lower()
    for palavra, rx in _ETIQUETAS:
        if re.search(rx, t):
            return palavra
    pal = re.sub(r"[^\wÀ-ú ]", " ", texto or "").split()
    return " ".join(pal[:2]).upper() if pal else ""


def _lua(d, p0, p2, bojo, esp, contorno):
    import math
    mx, my = (p0[0] + p2[0]) / 2, (p0[1] + p2[1]) / 2
    vx, vy = p2[0] - p0[0], p2[1] - p0[1]
    n = math.hypot(vx, vy) or 1
    p1 = (mx - vy / n * n * 0.35 * bojo, my + vx / n * n * 0.35 * bojo)
    pts = []
    for i in range(41):
        t = i / 40
        bx = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0]
        by = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]
        dx = 2 * (1 - t) * (p1[0] - p0[0]) + 2 * t * (p2[0] - p1[0])
        dy = 2 * (1 - t) * (p1[1] - p0[1]) + 2 * t * (p2[1] - p1[1])
        k = math.hypot(dx, dy) or 1
        w = esp * math.sin(math.pi * t) + 2
        pts.append(((bx - dy / k * w, by + dx / k * w), (bx + dy / k * w, by - dx / k * w)))
    lua = [a for a, _ in pts] + [b for _, b in reversed(pts)]
    d.line(lua + [lua[0]], fill=(0, 0, 0), width=contorno, joint="curve")
    d.polygon(lua, fill=(255, 236, 0))


def _desenhar_etiqueta_react(cfg, capa, palavra, foco=(0.5, 0.5)):
    d = ImageDraw.Draw(capa)
    W, H = capa.size
    vertical = H > W
    tam = int(H * (0.11 if vertical else 0.2))
    larg_max = W * (0.86 if vertical else 0.62)
    while tam > 30:
        f = _fonte(cfg, tam)
        if d.textlength(palavra, font=f) <= larg_max:
            break
        tam -= 6
    larg = d.textlength(palavra, font=f)
    x = (W - larg) / 2
    y = int(H * (0.62 if vertical else 0.66))
    p0 = (x + larg * 0.86, y + tam * 0.12)
    p2 = (foco[0] * W, foco[1] * H) if foco else (x + larg * 0.70, y - tam * 1.25)
    _lua(d, p0, p2, -1 if p2[0] < p0[0] else 1, tam * 0.16, max(6, tam // 14))
    d.text((x, y), palavra, font=f, fill=(255, 236, 0), stroke_width=max(8, tam // 11), stroke_fill=(0, 0, 0))


def _seta(d, ini, fim, esp, contorno):
    import math
    vx, vy = fim[0] - ini[0], fim[1] - ini[1]
    n = math.hypot(vx, vy) or 1
    ux, uy = vx / n, vy / n
    cab = min(esp * 2.6, n * 0.45)
    base = (fim[0] - ux * cab, fim[1] - uy * cab)
    ctrl = ((ini[0] + base[0]) / 2 - uy * n * 0.12, (ini[1] + base[1]) / 2 + ux * n * 0.12)
    lados_a, lados_b = [], []
    for i in range(25):
        t = i / 24
        bx = (1 - t) ** 2 * ini[0] + 2 * (1 - t) * t * ctrl[0] + t * t * base[0]
        by = (1 - t) ** 2 * ini[1] + 2 * (1 - t) * t * ctrl[1] + t * t * base[1]
        dx = 2 * (1 - t) * (ctrl[0] - ini[0]) + 2 * t * (base[0] - ctrl[0])
        dy = 2 * (1 - t) * (ctrl[1] - ini[1]) + 2 * t * (base[1] - ctrl[1])
        k = math.hypot(dx, dy) or 1
        w = esp * (0.55 + 0.45 * t) / 2
        lados_a.append((bx - dy / k * w, by + dx / k * w))
        lados_b.append((bx + dy / k * w, by - dx / k * w))
    dx, dy = (base[0] - ctrl[0]), (base[1] - ctrl[1])
    k = math.hypot(dx, dy) or 1
    px_, py_ = -dy / k, dx / k
    ponta = [(base[0] + px_ * esp * 1.25, base[1] + py_ * esp * 1.25), fim,
             (base[0] - px_ * esp * 1.25, base[1] - py_ * esp * 1.25)]
    corpo = lados_a + list(reversed(lados_b))
    for forma in (corpo, ponta):
        d.line(forma + [forma[0]], fill=(0, 0, 0), width=contorno, joint="curve")
    d.polygon(corpo, fill=(255, 236, 0))
    d.polygon(ponta, fill=(255, 236, 0))


def _rotulos_react(cfg, capa, rotulos):
    d = ImageDraw.Draw(capa)
    W, H = capa.size
    bloqueio = [(W * (0.62 if H > W else 0.85), H * 0.62, W, H)]

    def livre(r):
        return (r[0] >= W * 0.02 and r[2] <= W * 0.98 and r[1] >= H * 0.02 and r[3] <= H * 0.98
                and not any(r[0] < b[2] and b[0] < r[2] and r[1] < b[3] and b[1] < r[3] for b in bloqueio))

    for i, (txt, alvo) in enumerate(rotulos):
        if not txt:
            continue
        tam = int(min(W, H) * 0.13)
        while tam > 30:
            f = _fonte(cfg, tam)
            if d.textlength(txt, font=f) <= W * (0.8 if H > W else 0.36):
                break
            tam -= 6
        larg, alt = d.textlength(txt, font=f), tam * 1.05
        pos = (W * 0.04, H * 0.06 + i * alt * 1.3)
        x, y = pos
        if alvo:
            ini = (x + larg, y + alt / 2)
            _seta(d, ini, alvo, tam * 0.3, max(5, tam // 14))
        bloqueio.append((x, y, x + larg, y + alt))
        d.text((x, y), txt, font=f, fill=(255, 236, 0), stroke_width=max(6, tam // 10), stroke_fill=(0, 0, 0))


def capa_short(cfg, video, layout, t0, t1, texto, cor, out, work=None, tipo="react de manhwa/anime", duracao=None):
    W, H = 1080, 1920
    cor = _hex(cor)
    caixa = _caixa_conteudo(layout)
    am = _amostras(video, caixa, t0, t1)
    if not am:
        return None
    quadro, fx, fy = escolher_quadro(cfg, am, tipo)
    quadro, fy = cortar_marca(quadro, mascara_marca(video, caixa, duracao or t1), fy)
    quadro, fx = _recortar_painel(quadro, fx)
    quadro = _realcar(quadro)
    # fundo: o proprio quadro desfocado; personagem inteiro em cima, um pouco ampliado em volta do rosto
    canvas = _cover_foco(quadro, W, H, fx, fy).filter(ImageFilter.GaussianBlur(22)).convert("RGBA")
    canvas.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, 90)))
    esc = W * 1.22 / quadro.width
    ph = min(int(quadro.height * esc), int(H * 0.72))
    painel = _cover_foco(quadro, W, ph, fx, fy, zoom=max(1.0, (W * 1.22 / quadro.width) / max(W / quadro.width, ph / quadro.height)))
    canvas.paste(painel, (0, int(H * 0.08)))
    canvas.alpha_composite(_degrade(W, H, int(H * 0.55)))
    face = rosto_criador(cfg, video, layout, _tempos_reacao(work, t0, t1), 430)
    if face is not None:
        c = _circulo_com_brilho(face, cor)
        canvas.alpha_composite(c, (W - c.width + 10, int(H * 0.47)))
    lado, alto = ("esquerda" if face is not None else "direita"), 0.24
    res = _largura_mascote(W, H, alto)
    _texto(cfg, canvas, texto, (60 + res, int(H * 0.70), W - 60, H - 90) if lado == "esquerda" else
           (60, int(H * 0.70), W - 60 - res, H - 90), 170, 66)
    _colar_mascote(canvas, semente=str(out), lado=lado, alto=alto)
    canvas.convert("RGB").save(out, quality=92)
    log(f"capa short: {Path(out).name}")
    return Path(out)


def capa_grande(cfg, video, layout, t0, t1, texto, cor, out, work=None, tipo="react de manhwa/anime", genero=None):
    """genero (chave de GENRE_COLORS): grava tambem as variantes B e C ao lado (caminhos_ab) para o teste A/B."""
    W, H = 1280, 720
    cor = _hex(cor)
    caixa = _caixa_conteudo(layout)
    am = _amostras(video, caixa, t0, t1, n=12)
    if not am:
        return None
    quadro, fx, fy = escolher_quadro(cfg, am, tipo)
    quadro, fy = cortar_marca(quadro, mascara_marca(video, caixa, t1), fy)
    quadro, fx = _recortar_painel(quadro, fx)
    quadro = _realcar(quadro)
    # fundo: o proprio painel ampliado, desfocado e escurecido; painel nitido inteiro no centro (sem ampliar demais)
    canvas = _cover_foco(quadro, W, H, fx, fy).filter(ImageFilter.GaussianBlur(18)).convert("RGBA")
    canvas.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, 120)))
    ph = H
    pw = int(quadro.width * ph / quadro.height)
    if pw > W * 0.62:  # painel largo: corta nas laterais em volta do foco
        pw = int(W * 0.62)
    painel = _cover_foco(quadro, pw, ph, fx, fy)
    px = int(W * 0.44 - pw / 2)
    sombra = Image.new("RGBA", (pw + 80, ph + 80), (0, 0, 0, 0))
    ImageDraw.Draw(sombra).rectangle([40, 40, pw + 40, ph + 40], fill=(0, 0, 0, 200))
    canvas.alpha_composite(sombra.filter(ImageFilter.GaussianBlur(20)), (px - 40, -40))
    canvas.paste(painel, (px, 0))
    canvas.alpha_composite(_degrade(W, H, int(H * 0.45), alfa_max=200))
    face = rosto_criador(cfg, video, layout, _tempos_reacao(work, t0, t1), 330)
    c = _circulo_com_brilho(face, cor) if face is not None else None
    variantes = [("A", Path(out))]
    if genero in GENRE_COLORS:
        variantes += [(v, Path(out).with_name(f"{Path(out).stem}_{v.lower()}{Path(out).suffix}")) for v in ("B", "C")]
    for v, destino in variantes:
        tela = canvas.copy() if v == "A" else _tratamento(canvas, v, genero)
        if c is not None:
            tela.alpha_composite(c, (W - c.width + 20, H - c.height + 20))
        if v == "B":
            _desenhar_etiqueta_react(cfg, tela, _etiqueta(texto), foco=(fx, fy))
        elif v == "C":
            _rotulos_react(cfg, tela, [(_papel(texto), (int(W * fx), int(H * fy)))])
        else:
            cores = ((255, 255, 255), (255, 212, 0)) if v == "A" else (GENRE_COLORS[genero]["text"], (255, 255, 255))
            _texto(cfg, tela, texto, (40 + _largura_mascote(W, H, 0.42), int(H * 0.45), W - 330, H - 36), 118, 60,
                   max_linhas=2, cores=cores)
        _colar_mascote(tela, semente=f"{out}_{v}", lado="esquerda")
        tela.convert("RGB").save(destino, quality=92)
    log(f"capa grande: {Path(out).name}" + (f" + variantes B/C ({genero})" if len(variantes) > 1 else ""))
    return Path(out)


def refazer_capas(cfg, so=None):
    """Refaz as capas dos videos ja prontos (shorts/, cortes/, grandes/ em hipercool-materiais/manhwa-react) com o estilo novo,
    usando o cache do pipeline (work/<slug>: probe, layout, lips, editorial). Nao re-renderiza video nenhum."""
    import re
    import shutil
    from .pipeline import _channel
    pastas = [cfg["paths"].get(k) for k in ("ready", "ready_cortes", "ready_grandes") if cfg["paths"].get(k)]
    feitas = 0
    for pasta in pastas:
        for pj in sorted(Path(pasta).glob("*/*.postar.json")):
            d = load_json(pj)
            stem = Path(d["arquivo"]).stem
            if so and not any(s in stem for s in so):
                continue
            m = re.match(r"(.+?)(?:_p(\d+))?$", stem)
            slug, parte = m.group(1), int(m.group(2) or 1)
            w = Path(cfg["paths"]["work"]) / slug
            try:
                probe, layout = load_json(w / "probe.json"), load_json(w / "layout.json")
            except FileNotFoundError:
                log(f"capas: sem cache de {slug}, pulando")
                continue
            video = probe["path"]
            if not Path(video).exists():
                log(f"capas: video original sumiu ({video}), pulando")
                continue
            canal = _channel(cfg, d.get("canal_slug"))
            out = pj.parent / (d.get("thumb") or f"{stem}_thumb.jpg")
            try:
                if d.get("tipo") == "completo":
                    gm = load_json(w / "grande_meta.json") if (w / "grande_meta.json").exists() else {}
                    capa_grande(cfg, video, layout, 0, probe["duration"], gm.get("thumb_texto") or d.get("titulo", ""), canal.get("color"), out, work=w)
                else:
                    ed = load_json(w / "editorial.json")
                    p = ed["parts"][min(parte, len(ed["parts"])) - 1]
                    capa_short(cfg, video, layout, p["start"], p["end"], p.get("hook") or "", canal.get("color"), out, work=w, duracao=probe["duration"])
                saida = Path(cfg["paths"]["output"]) / slug / out.name
                if saida.parent.exists():
                    shutil.copy2(out, saida)
                feitas += 1
            except Exception as e:  # noqa: BLE001
                log(f"capas: {stem} falhou ({e})")
    log(f"capas: {feitas} refeita(s)")
    return feitas
