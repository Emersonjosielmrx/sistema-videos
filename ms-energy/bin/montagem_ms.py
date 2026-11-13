# -*- coding: utf-8 -*-
"""Montagem do short da MS Energy: clipe do Veo + frase no topo + legenda da fala + cartao final da marca.

No lugar do montar_final do Veo de memes (chiado de TV/glitch/raio no 0 s, starburst que deixava a tela preta aos
0,7 s, transicao de fogo/gelo para um cartao generico sem logo — analise 22/10, docs\\ANALISE_CAMPANHA.md).
A legenda usa o TEXTO do roteiro com os TEMPOS que o Whisper ouviu (Reels sao vistos sem som).
"""
import re
import subprocess
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

import glob as _glob
import json as _json
import random as _random

FF = r"D:\hipercool-materiais\bin\ffmpeg.exe"
FONTE_BLACK = r"D:\hipercool-materiais\assets\fonts\Montserrat-Black.ttf"
FONTE_XBOLD = r"D:\hipercool-materiais\assets\fonts\Montserrat-ExtraBold.ttf"
LOGO = Path(r"D:\ms-energy\assets\logo\perfil_instagram.jpg")
TMP = Path(r"D:\ms-energy\cache\tmp_montagem")
# 22/10: saida em 1080x1920 (letras mais nitidas no Reels); as medidas foram desenhadas em 720x1280 e escalam por px()
W, H = 1080, 1920
S = W / 720
VERMELHO = (200, 30, 55)       # vermelho do logo (161,32,56) um pouco mais vivo para o botao
VERMELHO_LOGO = (161, 32, 56)
CARTAO_S = 3.4
EMENDA_S = 0.4
CORTE_FIM_S = 0.3

# ── SFX e memes visuais (dona 01/11: "pode usar esses efeitos de som e os memes quando o vídeo não for muito sério")
_SFX_DIR = Path(r"D:\tmp_logs\sons_novos\cortados")
_SFX_RECAPD = Path(r"D:\recapd-ambientes\producao\workspace\assets")
_MEMES_CAT = Path(r"D:\recapd-ambientes\producao\config\memes_catalogo.json")
ESTILOS_LEVES = {"criativo", "historia", "comparacao", "chamada"}  # estilos que aceitam SFX/memes


def _listar_sfx():
    """SFX curtos (≤3 s) da pasta de sons novos + os de 'comedia'/'impacto' do catálogo do recapd."""
    sfx = []
    if _SFX_DIR.exists():
        for f in _SFX_DIR.iterdir():
            if f.suffix.lower() in (".wav", ".mp3") and f.stat().st_size < 600_000:
                sfx.append(str(f))
    cat_path = _SFX_RECAPD / "sfx_memes_categorized.json"
    if cat_path.exists():
        try:
            cat = _json.loads(cat_path.read_text(encoding="utf-8"))
            sfx_dir = _SFX_RECAPD / "sfx_memes"
            for nome, categoria in cat.get("files", {}).items():
                if categoria in ("comedia", "impacto"):
                    p = sfx_dir / nome
                    if p.exists():
                        sfx.append(str(p))
        except Exception:
            pass
    return sfx


def _escolher_sfx(n=1):
    """Escolhe n SFX curtos aleatórios (sem repetir)."""
    todos = _listar_sfx()
    if not todos:
        return []
    return _random.sample(todos, min(n, len(todos)))


def _listar_memes_video():
    """Memes de vídeo curtos (≤4 s, com áudio) do catálogo de memes do recapd."""
    if not _MEMES_CAT.exists():
        return []
    try:
        raw = _json.loads(_MEMES_CAT.read_text(encoding="utf-8"))
    except Exception:
        return []
    memes = []
    for m in raw.values():
        if (m.get("ok") and m.get("kind") == "video" and m.get("has_audio")
                and (m.get("duration") or 99) <= 4.0):
            f = Path(m["file"])
            if f.exists():
                memes.append({"file": str(f), "duration": m["duration"],
                              "tags": m.get("tags", []), "desc": m.get("desc", "")})
    return memes


def _escolher_meme():
    """Escolhe 1 meme de vídeo curto aleatório. None se não há."""
    todos = _listar_memes_video()
    return _random.choice(todos) if todos else None


def px(v):
    return int(round(v * S))


def _f(caminho, tam):
    return ImageFont.truetype(caminho, tam)


def _norm1(p):
    p = unicodedata.normalize("NFKD", p or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "", p)


def alinhar(fala, palavras, dur):
    """[(palavra_do_roteiro, inicio, fim)]: texto certo do roteiro com os tempos que o Whisper ouviu."""
    disp = fala.split()
    if not disp:
        return []
    tempos = [None] * len(disp)
    if palavras:
        sm = SequenceMatcher(None, [_norm1(w) for w in disp], [_norm1(p[0]) for p in palavras], autojunk=False)
        for a, b, n in sm.get_matching_blocks():
            for k in range(n):
                tempos[a + k] = (palavras[b + k][1], palavras[b + k][2])
    ini = palavras[0][1] if palavras else 0.3
    fim = palavras[-1][2] if palavras else max(dur - 0.6, 1.0)
    i = 0
    while i < len(disp):
        if tempos[i] is not None:
            i += 1
            continue
        j = i
        while j < len(disp) and tempos[j] is None:
            j += 1
        a = tempos[i - 1][1] if i > 0 else ini
        b = tempos[j][0] if j < len(disp) else fim
        passo = max(b - a, 0.2) / (j - i)
        for k in range(i, j):
            tempos[k] = (a + passo * (k - i), a + passo * (k - i + 1))
        i = j
    return [(w, round(s, 2), round(e, 2)) for w, (s, e) in zip(disp, tempos)]


def blocos(alinhadas, max_pal=3, max_chars=18):
    """Pedacos de legenda de ate 3 palavras, quebrando na pontuacao; cada um fica ate o proximo comecar."""
    grupos, cur = [], []
    for w, s, e in alinhadas:
        cur.append((w, s, e))
        if len(cur) >= max_pal or len(" ".join(x[0] for x in cur)) >= max_chars or w.endswith((".", "!", "?", ",")):
            grupos.append(cur)
            cur = []
    if cur:
        grupos.append(cur)
    res = []
    for i, g in enumerate(grupos):
        s, e = g[0][1], g[-1][2]
        prox = grupos[i + 1][0][1] if i + 1 < len(grupos) else e + 0.6
        texto = " ".join(x[0] for x in g).rstrip(".,")
        res.append((texto, s, max(min(prox, e + 0.6), s + 0.35)))
    return res


def _quebrar(draw, texto, fonte, largura):
    linhas, cur = [], ""
    for p in texto.split():
        t = (cur + " " + p).strip()
        if draw.textlength(t, font=fonte) <= largura or not cur:
            cur = t
        else:
            linhas.append(cur)
            cur = p
    if cur:
        linhas.append(cur)
    return linhas


AMARELO = (255, 214, 10)


def _png_legenda(texto, destino, destaque=None):
    """destaque = índice da palavra falada agora, pintada de amarelo (25/10, aprendizado com parceiros #6/#20/#33
    ffb4c8fe/62c7ec8c/e4fbdf10: legenda "karaokê" segura o olho no centro); None = tudo branco, como antes."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    fonte = _f(FONTE_XBOLD, px(56))
    linhas = _quebrar(d, texto, fonte, W - px(80))
    y = int(H * 0.64)
    idx = 0
    for ln in linhas:
        lw = d.textlength(ln, font=fonte)
        x = (W - lw) / 2
        for p in ln.split():
            d.text((x, y), p, font=fonte, fill=AMARELO if destaque == idx else "white", stroke_width=px(6),
                   stroke_fill="black")
            x += d.textlength(p + " ", font=fonte)
            idx += 1
        y += px(68)
    im.save(destino)


def blocos_palavras(alinhadas, max_pal=3, max_chars=18):
    """Os mesmos pedaços do blocos(), com o tempo de CADA palavra: [(texto, ini, fim, [(palavra, ini, fim)])]."""
    grupos, cur = [], []
    for w, s, e in alinhadas:
        cur.append((w, s, e))
        if len(cur) >= max_pal or len(" ".join(x[0] for x in cur)) >= max_chars or w.endswith((".", "!", "?", ",")):
            grupos.append(cur)
            cur = []
    if cur:
        grupos.append(cur)
    res = []
    for i, g in enumerate(grupos):
        s, e = g[0][1], g[-1][2]
        prox = grupos[i + 1][0][1] if i + 1 < len(grupos) else e + 0.6
        res.append((" ".join(x[0] for x in g).rstrip(".,"), s, max(min(prox, e + 0.6), s + 0.35), g))
    return res


# ───────── legenda CINÉTICA (dona 01/11: "legendas criativas mudando de forma e tamanho", ref. edit AMV
# youtube sPyd8I220GI): 1 palavra forte por vez em letra condensada, tamanho conforme o peso da palavra, palavras
# curtas pequenas em cima, separação de cor (RGB), leve giro e um "pulo" de tamanho ao entrar. Variante medida no
# placar (insta_estilos <conta>:legenda) contra o karaokê.
FONTE_COND = r"D:\hipercool-materiais\assets\fonts\impact.ttf"
CURTAS = {"a", "o", "e", "é", "de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas", "um", "uma", "que",
          "com", "pra", "para", "por", "se", "seu", "sua", "te", "you", "eu", "ao", "à", "os", "as", "ou", "mas", "não",
          "já", "tem", "vai", "só", "isso", "essa", "esse", "ela", "ele", "me", "mais", "muito", "quem", "como"}
FORTES = {"conta", "luz", "economia", "economizar", "grátis", "solar", "sol", "energia", "orçamento", "telhado",
          "parcela", "zero", "nunca", "erro", "verdade", "mito", "noite", "dinheiro", "inversor", "placas", "painéis",
          "advance", "globo", "ms", "pará", "castanhal", "concórdia", "belém", "calor", "chuva"}


def blocos_cineticos(alinhadas):
    """[(curtas_em_cima, palavra_forte, ini, fim)]: palavras curtas se juntam à próxima palavra forte (como "TO /
    FORGET" na referência); cada bloco fica até o próximo começar."""
    blocos_, pre = [], []
    for w, s, e in alinhadas:
        limpa = w.strip(".,!?;:\"'").lower()
        if limpa in CURTAS and len(pre) < 3:
            pre.append((w, s, e))
            continue
        ini = pre[0][1] if pre else s
        blocos_.append(([x[0] for x in pre], w, ini, e))
        pre = []
    if pre:  # sobrou palavra curta no fim: vira a forte do último bloco
        ini = pre[0][1]
        blocos_.append(([x[0] for x in pre[:-1]], pre[-1][0], ini, pre[-1][2]))
    res = []
    for i, (cima, forte, s, e) in enumerate(blocos_):
        prox = blocos_[i + 1][2] if i + 1 < len(blocos_) else e + 0.5
        res.append((cima, forte, s, max(min(prox, e + 0.5), s + 0.3)))
    return res


def _texto_rgb(d, xy, texto, fonte, cor, desl):
    """Texto com separação de cor (vermelho/ciano deslocados) + contorno escuro fino."""
    x, y = xy
    d.text((x - desl, y), texto, font=fonte, fill=(255, 40, 60, 170))
    d.text((x + desl, y), texto, font=fonte, fill=(40, 230, 255, 170))
    d.text((x, y), texto, font=fonte, fill=cor, stroke_width=px(3), stroke_fill=(0, 0, 0, 230))


# 01/11 (dona: "as legendas têm que ser dessa forma ou melhor, como o vídeo longo está implementando: cores e lugares
# diferentes da tela, tamanhos e fontes diferentes, impactante, palavra por palavra" — ref.
# hipercool-materiais\teste_legenda_abertura\abertura_v3_legenda_falada.mp4): cada palavra vira um ADESIVO — fonte
# própria, preenchimento em degradê, contorno escuro grosso + brilho da mesma cor, leve giro, e muda de lugar na tela.
_FONTES_DIR = Path(r"D:\hipercool-materiais\assets\fonts")
FONTES_ADESIVO = [str(_FONTES_DIR / f) for f in ("LuckiestGuy-Regular.ttf", "Bangers-Regular.ttf", "impact.ttf",
                                                  "Montserrat-Black.ttf")]
CORES_ADESIVO = [(60, 200, 255), (255, 214, 10), (255, 80, 170), (255, 70, 50), (70, 120, 255), (60, 230, 120),
                 (255, 150, 30), (255, 255, 255)]
CONTORNO = (14, 18, 40)


def _clarear(c, k=0.55):
    return tuple(int(v + (255 - v) * k) for v in c)


def _adesivo(texto, fonte, cor):
    """Palavra como adesivo RGBA: degradê (claro em cima -> cor embaixo), contorno escuro grosso e brilho colorido."""
    s = max(4, fonte.size // 9)
    bb = ImageDraw.Draw(Image.new("L", (1, 1))).textbbox((0, 0), texto, font=fonte, stroke_width=s)
    pad = s * 4
    w, h = bb[2] - bb[0] + 2 * pad, bb[3] - bb[1] + 2 * pad
    org = (pad - bb[0], pad - bb[1])
    letra = Image.new("L", (w, h), 0)
    ImageDraw.Draw(letra).text(org, texto, font=fonte, fill=255)
    borda = Image.new("L", (w, h), 0)
    ImageDraw.Draw(borda).text(org, texto, font=fonte, fill=255, stroke_width=s, stroke_fill=255)
    brilho = borda.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(s * 1.6))
    out = Image.new("RGBA", (w, h), cor + (0,))
    out.putalpha(brilho.point(lambda a: int(a * 0.85)))
    out = Image.alpha_composite(out, Image.composite(Image.new("RGBA", (w, h), CONTORNO + (255,)),
                                                     Image.new("RGBA", (w, h), (0, 0, 0, 0)), borda))
    topo, base = _clarear(cor), cor
    grad = Image.new("RGBA", (1, h))
    for y in range(h):
        k = min(1.0, max(0.0, (y - pad) / max(1, h - 2 * pad)))
        grad.putpixel((0, y), tuple(int(topo[i] + (base[i] - topo[i]) * k) for i in range(3)) + (255,))
    grad = grad.resize((w, h))
    out = Image.alpha_composite(out, Image.composite(grad, Image.new("RGBA", (w, h), (0, 0, 0, 0)), letra))
    return out


def _degrade(w, h, pad, cor):
    topo = _clarear(cor)
    grad = Image.new("RGBA", (1, h))
    for y in range(h):
        k = min(1.0, max(0.0, (y - pad) / max(1, h - 2 * pad)))
        grad.putpixel((0, y), tuple(int(topo[i] + (cor[i] - topo[i]) * k) for i in range(3)) + (255,))
    return grad.resize((w, h))


def _sombra(img):
    """Sombra escura projetada embaixo/à direita do adesivo."""
    s = Image.new("RGBA", img.size, (0, 0, 0, 0))
    s.paste(Image.new("RGBA", img.size, (0, 0, 0, 160)), (0, 0), img.split()[3])
    s = s.filter(ImageFilter.GaussianBlur(px(8)))
    out = Image.new("RGBA", (img.width + px(12), img.height + px(12)), (0, 0, 0, 0))
    out.alpha_composite(s, (px(8), px(10)))
    out.alpha_composite(img, (0, 0))
    return out


def _adesivo_contorno_duplo(texto, fonte, cor):
    """Degradê + contorno escuro + contorno branco por fora + brilho."""
    s = max(4, fonte.size // 9)
    s2 = s + max(3, s // 2)
    bb = ImageDraw.Draw(Image.new("L", (1, 1))).textbbox((0, 0), texto, font=fonte, stroke_width=s2)
    pad = s2 * 4
    w, h = bb[2] - bb[0] + 2 * pad, bb[3] - bb[1] + 2 * pad
    org = (pad - bb[0], pad - bb[1])
    ext, inte, letra = (Image.new("L", (w, h), 0) for _ in range(3))
    ImageDraw.Draw(ext).text(org, texto, font=fonte, fill=255, stroke_width=s2, stroke_fill=255)
    ImageDraw.Draw(inte).text(org, texto, font=fonte, fill=255, stroke_width=s, stroke_fill=255)
    ImageDraw.Draw(letra).text(org, texto, font=fonte, fill=255)
    vazio = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out = Image.new("RGBA", (w, h), cor + (0,))
    out.putalpha(ext.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(s2 * 1.6))
                 .point(lambda a: int(a * 0.85)))
    out = Image.alpha_composite(out, Image.composite(Image.new("RGBA", (w, h), (255, 255, 255, 255)), vazio, ext))
    out = Image.alpha_composite(out, Image.composite(Image.new("RGBA", (w, h), CONTORNO + (255,)), vazio, inte))
    return Image.alpha_composite(out, Image.composite(_degrade(w, h, pad, cor), vazio, letra))


def _adesivo_recorte(texto, fonte, cor):
    """Figurinha recortada: degradê, contorno escuro fino, borda BRANCA grossa e sombra."""
    s = max(3, fonte.size // 14)
    b = max(8, fonte.size // 6)
    bb = ImageDraw.Draw(Image.new("L", (1, 1))).textbbox((0, 0), texto, font=fonte, stroke_width=s + b)
    pad = (s + b) * 2
    w, h = bb[2] - bb[0] + 2 * pad, bb[3] - bb[1] + 2 * pad
    org = (pad - bb[0], pad - bb[1])
    branca, escura, letra = (Image.new("L", (w, h), 0) for _ in range(3))
    ImageDraw.Draw(branca).text(org, texto, font=fonte, fill=255, stroke_width=s + b, stroke_fill=255)
    branca = branca.filter(ImageFilter.MaxFilter(3))
    ImageDraw.Draw(escura).text(org, texto, font=fonte, fill=255, stroke_width=s, stroke_fill=255)
    ImageDraw.Draw(letra).text(org, texto, font=fonte, fill=255)
    vazio = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    camada = Image.composite(Image.new("RGBA", (w, h), (255, 255, 255, 255)), vazio, branca)
    camada = Image.alpha_composite(camada, Image.composite(Image.new("RGBA", (w, h), CONTORNO + (255,)), vazio, escura))
    camada = Image.alpha_composite(camada, Image.composite(_degrade(w, h, pad, cor), vazio, letra))
    return _sombra(camada)


def _adesivo_caixa(texto, fonte, cor):
    """Palavra branca com contorno escuro numa caixa arredondada da cor (branco vira vermelho)."""
    if cor == (255, 255, 255):
        cor = (255, 70, 50)
    s = max(3, fonte.size // 14)
    bb = ImageDraw.Draw(Image.new("L", (1, 1))).textbbox((0, 0), texto, font=fonte, stroke_width=s)
    padx, pady = px(26), px(14)
    w, h = bb[2] - bb[0] + 2 * padx, bb[3] - bb[1] + 2 * pady
    caixa = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(caixa)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=px(22), fill=cor + (240,), outline=CONTORNO + (255,),
                        width=px(4))
    d.text((padx - bb[0], pady - bb[1]), texto, font=fonte, fill="white", stroke_width=s, stroke_fill=CONTORNO)
    return _sombra(caixa)


def _sublinhar(img, cor):
    out = Image.new("RGBA", (img.width, img.height + px(16)), (0, 0, 0, 0))
    out.alpha_composite(img, (0, 0))
    y = img.height - px(20)
    ImageDraw.Draw(out).rounded_rectangle((px(18), y, img.width - px(18), y + px(10)), radius=px(5),
                                          fill=cor + (230,))
    return out


DESENHOS = {"degrade": _adesivo, "sombra": lambda t, f, c: _sombra(_adesivo(t, f, c)),
            "contorno_duplo": _adesivo_contorno_duplo, "recorte": _adesivo_recorte, "caixa": _adesivo_caixa}
QUENTES = [(255, 214, 10), (255, 70, 50), (255, 80, 170), (255, 150, 30)]


def _peso(forte):
    limpa = forte.strip(".,!?;:\"'")
    return 3 if limpa.lower() in FORTES or forte.endswith(("!", "?")) else (2 if len(limpa) >= 7 else 1)


def escolher_mix():
    """01/11 (dona: "mesclar todos, combinações diferentes em cada palavra"): 'inteligente' (o desenho e os efeitos
    seguem o peso da palavra) ou 'livre' (tudo sorteado por palavra). MS_LEGENDA_MIX força; senão 50/50 no placar."""
    import os
    forc = os.environ.get("MS_LEGENDA_MIX", "").strip().lower()
    return forc if forc in ("inteligente", "livre") else _random.choice(["inteligente", "livre"])


def plano_legenda(blocos_, semente, modo="inteligente"):
    """Um estilo por bloco: desenho, desenho das curtas, cor, pop, giro, sublinhado e rastro (palavra anterior
    apagada). Nunca o mesmo desenho 2x seguidas. Mesma semente = mesmo plano (o quadro do pop bate com o normal)."""
    rng = _random.Random(str(semente))
    nomes = list(DESENHOS)
    plano, ant = [], None
    for i, (cima, forte, s, e) in enumerate(blocos_):
        p = _peso(forte)
        if modo == "livre":
            ops, cor = nomes, rng.choice(CORES_ADESIVO)
            pop_k, giro_k = rng.choice((1.18, 1.35, 1.40)), rng.choice((1.0, 1.0, 1.7))
            sub, rastro = rng.random() < 0.25, rng.random() < 0.35
        else:
            ops = {3: ["recorte", "caixa", "contorno_duplo"], 2: ["recorte", "contorno_duplo", "sombra", "degrade"],
                   1: ["degrade", "sombra", "recorte"]}[p]
            cor = rng.choice(QUENTES) if p == 3 else CORES_ADESIVO[(i * 3) % len(CORES_ADESIVO)]
            pop_k = {3: 1.40, 2: 1.35, 1: 1.18}[p]
            giro_k = 1.7 if p == 3 and rng.random() < 0.5 else 1.0
            sub = p >= 2 and rng.random() < (0.5 if p == 3 else 0.25)
            # rastro só quando a fala corre (bloco anterior acabou de sair): dá contexto sem poluir as pausas
            rastro = i > 0 and s - blocos_[i - 1][3] < 0.25 and not (plano and plano[-1]["rastro"]) \
                and rng.random() < 0.5
        des = rng.choice([d for d in ops if d != ant] or ops)
        if des == "caixa":
            sub = False
        cima_des = "caixa" if des != "caixa" and rng.random() < 0.35 else ("recorte" if des == "caixa" else des)
        plano.append({"desenho": des, "cima_desenho": cima_des, "cor": cor, "pop_k": pop_k, "giro_k": giro_k,
                      "sublinhado": sub, "rastro": bool(rastro) and i > 0})
        ant = des
    return plano


def _encostam(a, b, folga=None):
    """Caixas (x0,y0,x1,y1) se tocam (com folga)? Rastro em cima da palavra nova embola as duas (quadro 01/11)."""
    if not a or not b:
        return False
    f = px(20) if folga is None else folga
    return not (a[2] + f < b[0] or b[2] + f < a[0] or a[3] + f < b[1] or b[3] + f < a[1])


def _com_rastro(destino, anterior):
    """Põe o bloco anterior (35%) por baixo do PNG atual."""
    fundo = anterior.copy()
    fundo.putalpha(fundo.split()[3].point(lambda a: int(a * 0.35)))
    fundo.alpha_composite(Image.open(destino).convert("RGBA"))
    fundo.save(destino)


# lugares na tela (fração de W, H) — o bloco muda de lugar a cada palavra, sempre fora do rosto
_LUGARES = [(0.50, 0.74), (0.30, 0.66), (0.70, 0.80), (0.36, 0.84), (0.66, 0.68), (0.50, 0.30), (0.30, 0.22),
            (0.70, 0.26)]


def _png_cinetica(cima, forte, destino, n, rosto=None, pop=False, topo_livre=True, estilo=None):
    """1 quadro da legenda (adesivos). n = nº do bloco (troca fonte, cor, giro e lugar); pop = quadro de entrada.
    estilo = item do plano_legenda (desenho/efeitos desta palavra); None = adesivo em degradê, como antes."""
    est = estilo or {}
    limpa = forte.strip(".,!?;:\"'")
    peso = _peso(forte)
    tam = {1: px(92), 2: px(110), 3: px(138)}[peso]
    if pop:
        tam = int(tam * est.get("pop_k", 1.18))
    fp = FONTES_ADESIVO[n % len(FONTES_ADESIVO)]
    cor = tuple(est.get("cor") or CORES_ADESIVO[(n * 3) % len(CORES_ADESIVO)])
    desenho = DESENHOS[est.get("desenho", "degrade")]
    texto = limpa.upper()
    fonte = _f(fp, tam)
    medir = ImageDraw.Draw(Image.new("L", (1, 1)))
    larg_max = W * (0.80 if est.get("desenho", "degrade") in ("degrade", "sombra") else 0.72)
    while medir.textlength(texto, font=fonte) > larg_max and tam > px(40):
        tam -= px(4)
        fonte = _f(fp, tam)
    principal = desenho(texto, fonte, cor)
    if est.get("sublinhado"):
        principal = _sublinhar(principal, cor)
    partes = [principal]
    cima_txt = " ".join(c.strip(".,") for c in cima).upper()
    if cima_txt:  # palavras curtas: adesivo menor, outra fonte e outra cor, em cima (como "QUANDO / ELE")
        fc = _f(FONTES_ADESIVO[(n + 1) % len(FONTES_ADESIVO)], max(px(40), int(tam * 0.55)))
        partes.insert(0, DESENHOS[est.get("cima_desenho", est.get("desenho", "degrade"))](
            cima_txt, fc, CORES_ADESIVO[(n * 3 + 2) % len(CORES_ADESIVO)]))
    bw = max(p.width for p in partes)
    bh = sum(p.height for p in partes) - px(18) * (len(partes) - 1)
    bloco = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    y = 0
    for k, p in enumerate(partes):
        dx = (bw - p.width) // 2 + (int(bw * 0.12) * (-1 if n % 2 else 1) if k == 0 and len(partes) > 1 else 0)
        bloco.alpha_composite(p, (max(0, min(bw - p.width, dx)), y))
        y += p.height - px(18)
    giro = (-7, 5, -3, 8, -5, 3, -8, 6)[n % 8] * est.get("giro_k", 1.0)
    bloco = bloco.rotate(giro, resample=Image.BICUBIC, expand=True)
    margem = px(26)
    if bloco.width > W - 2 * margem:  # borda branca/caixa + giro podem passar da tela
        k = (W - 2 * margem) / bloco.width
        bloco = bloco.resize((int(bloco.width * k), int(bloco.height * k)), Image.LANCZOS)
    # lugar: gira pela lista; se cair no rosto (ou no topo ocupado pelo balão/faixa), vai para o próximo
    lim_x0, lim_x1 = margem, W - margem
    for t in range(len(_LUGARES)):
        fx, fy = _LUGARES[(n + t) % len(_LUGARES)]
        x0 = int(min(max(fx * W - bloco.width / 2, lim_x0), lim_x1 - bloco.width))
        y0 = int(min(max(fy * H - bloco.height / 2, px(40)), H * 0.90 - bloco.height))
        if not topo_livre and y0 < H * 0.40:
            continue
        if rosto and not (y0 + bloco.height < rosto[0] - px(10) or y0 > rosto[1] + px(30)):
            continue
        break
    else:  # nenhum lugar livre: embaixo do rosto, centralizado
        x0 = (W - bloco.width) // 2
        y_min = (rosto[1] + px(30)) if rosto else int(H * 0.70)
        livre = int(H * 0.93) - y_min
        if rosto and bloco.height > livre > 0:  # não cabe embaixo do queixo: encolhe em vez de subir no rosto
            k = max(livre / bloco.height, 0.55)
            bloco = bloco.resize((int(bloco.width * k), int(bloco.height * k)), Image.LANCZOS)
            x0 = (W - bloco.width) // 2
        y0 = int(min(y_min, H * 0.93 - bloco.height))
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    im.alpha_composite(bloco, (max(0, x0), max(0, y0)))
    im.save(destino)


# ───────── layout "AULA" (dona 01/11: "esse estilo do agentesdeia_ia_20261030_232120 — por que não postou na
# Advance e na Globo?"): depois do balão de abertura, faixa de título fixa na cor da marca + etiqueta da etapa
# (1 O problema / 2 Como funciona / 3 O resultado) trocando por terços do vídeo, como o vídeo profissional de produto.
ETAPAS_AULA = ("O problema", "Como funciona", "O resultado")


def _png_aula(titulo, etapa, destino, rosto=None):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    fonte = _f(FONTE_BLACK, px(42))
    linhas = _quebrar(d, titulo.upper(), fonte, W - px(140))[:2]
    alto_l = px(52)
    y0 = px(36)
    caixa_h = alto_l * len(linhas) + px(28)
    lw = max(d.textlength(ln, font=fonte) for ln in linhas)
    x0 = (W - lw) / 2 - px(26)
    d.rounded_rectangle((x0, y0, W - x0, y0 + caixa_h), radius=px(14), fill=VERMELHO + (245,))
    for k, ln in enumerate(linhas):
        d.text(((W - d.textlength(ln, font=fonte)) / 2, y0 + px(14) + k * alto_l), ln, font=fonte, fill="white")
    # etiqueta da etapa: círculo com o número + texto, logo abaixo da faixa (some se encostar no rosto)
    fe = _f(FONTE_XBOLD, px(22))
    n = ETAPAS_AULA.index(etapa) + 1
    ey = y0 + caixa_h + px(14)
    eh = px(40)
    if not rosto or ey + eh + px(6) < rosto[0]:
        tx = d.textlength(etapa, font=fe)
        ex0 = x0
        d.rounded_rectangle((ex0, ey, ex0 + eh + tx + px(30), ey + eh), radius=eh // 2, fill=(20, 24, 30, 225))
        d.ellipse((ex0 + px(6), ey + px(6), ex0 + eh - px(6), ey + eh - px(6)), fill=VERMELHO + (255,))
        d.text((ex0 + eh / 2, ey + eh / 2), str(n), font=fe, fill="white", anchor="mm")
        d.text((ex0 + eh + px(8), ey + eh / 2), etapa, font=fe, fill="white", anchor="lm")
    im.save(destino)


def escolher_layout():
    """'normal' ou 'aula'. MS_LAYOUT força; senão 50/50 até o placar (<conta>:layout) mostrar o melhor."""
    import os
    import random
    forc = os.environ.get("MS_LAYOUT", "").strip().lower()
    if forc in ("normal", "aula"):
        return forc
    return random.choice(["normal", "aula"])


def escolher_legenda():
    """'cinetica' (adesivos) em TODOS desde 01/11 (dona: "as legendas têm que ser dessa forma"); MS_LEGENDA=karaoke
    volta à antiga."""
    import os
    forc = os.environ.get("MS_LEGENDA", "").strip().lower()
    if forc in ("karaoke", "cinetica"):
        return forc
    return "cinetica"


ROTULO_PERGUNTA = "Pergunta que a gente sempre recebe"


LEGENDA_Y = 0.64  # a legenda começa aqui (_png_legenda)


def rosto_faixa(clip, ate_s=2.6):
    """31/10 (dona: "a pergunta ficou na cara dele, isso não pode acontecer nos próximos"): (topo, base) do rosto nos
    primeiros `ate_s` s do vídeo, em pixels da tela final (mesmo scale/crop da montagem), com folga para cabelo e
    queixo. None = nenhum rosto achado (ou detector indisponível)."""
    try:
        import sys
        if r"D:\veo\beta" not in sys.path:
            sys.path.append(r"D:\veo\beta")
        import foto_na_hora
    except Exception:  # noqa: BLE001
        return None
    TMP.mkdir(parents=True, exist_ok=True)
    topo, base = None, None
    tempos = (0.2, 0.9, 1.6, max(0.2, ate_s - 0.3)) if ate_s <= 3 else \
        tuple(round(0.2 + k * (ate_s - 0.5) / 5, 2) for k in range(6))
    for i, t in enumerate(tempos):
        q = TMP / f"_rosto_{Path(clip).stem}_{i}.jpg"
        try:
            subprocess.run([FF, "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", str(clip), "-frames:v", "1", "-vf",
                            f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}", str(q)],
                           capture_output=True, timeout=60)
        except subprocess.TimeoutExpired:
            continue
        try:
            achados = foto_na_hora.rostos(str(q)) if q.exists() else []
        except Exception:  # noqa: BLE001
            achados = []
        finally:
            q.unlink(missing_ok=True)
        for _emb, _area, (x, y, w, h), _giro in achados[:1]:  # o rosto maior (apresentador)
            topo = min(topo if topo is not None else H, y - int(h * 0.45))
            base = max(base or 0, y + int(h * 1.15))
    return (max(0, topo), min(H, base)) if topo is not None else None


def _y_pergunta(alto, meio, rosto):
    """Altura do cartão: sem rosto conhecido, o lugar de antes; com rosto, o lugar livre que menos encosta nele
    (em cima do rosto ou entre o queixo e a legenda), nunca sobre a legenda."""
    padrao = int(H * 0.42) if meio else px(150)
    if not rosto:
        return padrao
    ft, fb = rosto
    limite = int(H * LEGENDA_Y) - px(12) - alto
    cands = [px(150), px(70), fb + px(20), padrao, ft - px(20) - alto]
    cands = [c for c in cands if 0 <= c <= limite] or [px(70)]
    return min(cands, key=lambda c: (max(0, min(c + alto, fb) - max(c, ft)), c != px(150)))


def _png_pergunta(texto, destino, meio=False, rosto=None):
    """25/10 (aprendizado com parceiros #12 c9627e2c: a dúvida do público na tela, logo no começo, prende e puxa
    comentário): pergunta no topo vira um cartão branco no estilo da figurinha "responder comentário" do Instagram, com
    um rótulo honesto (não inventa seguidor nem @). meio=True (apresentador): o cartão desce pro peito — no topo, com
    2 linhas, cobria o rosto (quadro de teste 25/10); fica acima da legenda (64% da altura).
    31/10: com `rosto` (rosto_faixa do vídeo) o cartão vai para onde o rosto NÃO está (no 1º Reel da Globo os 42%
    caíram em cima da cara do dono)."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f_rot, f_q = _f(FONTE_XBOLD, px(25)), _f(FONTE_BLACK, px(54))
    linhas = _quebrar(d, texto, f_q, W - px(200))
    larg = max(max(d.textlength(ln, font=f_q) for ln in linhas), d.textlength(ROTULO_PERGUNTA, font=f_rot) + px(56))
    alto = px(66) + px(66) * len(linhas) + px(20) + px(24)
    x0, y0 = (W - larg) / 2 - px(30), _y_pergunta(alto, meio, rosto)
    x1, y1 = x0 + larg + px(60), y0 + px(66) + px(66) * len(linhas) + px(20)
    sombra = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sombra).rounded_rectangle((x0 + px(3), y0 + px(6), x1 + px(3), y1 + px(6)), radius=px(28),
                                             fill=(0, 0, 0, 120))
    im.alpha_composite(sombra.filter(ImageFilter.GaussianBlur(px(7))))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((x0, y0, x1, y1), radius=px(28), fill=(255, 255, 255, 246))
    d.polygon([(x0 + px(58), y1 - 1), (x0 + px(92), y1 - 1), (x0 + px(62), y1 + px(24))], fill=(255, 255, 255, 246))
    r = px(15)
    cx, cy = x0 + px(28) + r, y0 + px(33)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=VERMELHO + (255,))
    d.text((cx + r + px(12), cy - px(15)), ROTULO_PERGUNTA, font=f_rot, fill=(105, 105, 115))
    y = y0 + px(62)
    for ln in linhas:
        lw = d.textlength(ln, font=f_q)
        d.text(((W - lw) / 2, y), ln, font=f_q, fill=(22, 22, 26))
        y += px(66)
    im.save(destino)


def _png_gancho(texto, destino, tipo=None, rosto=None):
    if (texto or "").strip().endswith("?"):
        return _png_pergunta(texto.strip(), destino, meio=(tipo == "apresentador"), rosto=rosto)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    fonte = _f(FONTE_BLACK, px(60))
    linhas = _quebrar(d, texto, fonte, W - px(140))
    alt = px(74) * len(linhas)
    larg = max(d.textlength(ln, font=fonte) for ln in linhas)
    x0 = (W - larg) / 2 - px(34)
    y0 = _y_pergunta(alt + px(36), False, rosto)  # 31/10: a faixa do gancho também desvia do rosto
    d.rounded_rectangle((x0, y0, x0 + larg + px(68), y0 + alt + px(36)), radius=px(26), fill=VERMELHO + (235,))
    y = y0 + px(16)
    for ln in linhas:
        lw = d.textlength(ln, font=fonte)
        d.text(((W - lw) / 2, y), ln, font=fonte, fill="white")
        y += px(74)
    im.save(destino)


def _logo_rgba(largura):
    """Logo do perfil sem o fundo preto (alfa pelo brilho), para assentar sobre a foto escurecida."""
    from PIL import ImageEnhance
    lg = ImageEnhance.Brightness(Image.open(LOGO).convert("RGB")).enhance(1.35)
    # o logo do perfil tem 206 px: ampliado ~3x fica borrado -> realce de borda (e grafico de cor chapada)
    lg = lg.resize((largura, int(lg.height * largura / lg.width)), Image.LANCZOS)
    lg = lg.filter(ImageFilter.UnsharpMask(radius=px(2), percent=180, threshold=2))
    alfa = lg.convert("L").point(lambda v: max(0, min(255, (v - 28) * 5)))
    out = lg.convert("RGBA")
    out.putalpha(alfa)
    return out


def cartao(foto_fundo, destino):
    """Cartao final: foto real escurecida + logo + oferta + WhatsApp. Sem preco, sem promessa de economia."""
    if foto_fundo and Path(foto_fundo).exists():
        fundo = ImageOps.fit(Image.open(foto_fundo).convert("RGB"), (W, H)).filter(ImageFilter.GaussianBlur(px(3)))
        fundo = Image.blend(fundo, Image.new("RGB", (W, H), (8, 8, 12)), 0.70)
    else:
        fundo = Image.new("RGB", (W, H), (12, 12, 16))
    im = fundo.convert("RGBA")
    grad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    for y in range(H):
        gd.line([(0, y), (W, y)], fill=(0, 0, 0, int(140 * (y / H) ** 1.5)))
    im = Image.alpha_composite(im, grad)
    lg = _logo_rgba(px(470))
    im.alpha_composite(lg, ((W - lg.width) // 2, px(120)))
    d = ImageDraw.Draw(im)

    def caber(texto, caminho, tam, largura):
        while tam > px(18) and d.textlength(texto, font=_f(caminho, tam)) > largura:
            tam -= 2
        return _f(caminho, tam)

    def centro(texto, fonte, y, cor="white"):
        lw = d.textlength(texto, font=fonte)
        d.text(((W - lw) / 2, y), texto, font=fonte, fill=cor)

    y = px(120) + lg.height + px(40)
    centro("Orçamento grátis", caber("Orçamento grátis", FONTE_BLACK, px(76), W - px(70)), y)
    y += px(106)
    for ln in _quebrar(d, "Energia solar para casa, comércio e campo", _f(FONTE_XBOLD, px(36)), W - px(100)):
        centro(ln, _f(FONTE_XBOLD, px(36)), y)
        y += px(48)
    y += px(10)
    linha = "Projeto • Instalação • Manutenção"
    centro(linha, caber(linha, FONTE_XBOLD, px(29), W - px(80)), y, (225, 225, 225))
    y += px(92)
    txt = "Chame no WhatsApp"
    fb = caber(txt, FONTE_BLACK, px(44), W - px(170))
    lw = d.textlength(txt, font=fb)
    d.rounded_rectangle(((W - lw) / 2 - px(44), y - px(18), (W + lw) / 2 + px(44), y + px(70)), radius=px(44),
                        fill=VERMELHO)
    centro(txt, fb, y)
    y += px(116)
    linha = "Instagram @msenergycap"
    centro(linha, caber(linha, FONTE_XBOLD, px(36), W - px(80)), y)
    y += px(56)
    linha = "Quase 10 anos no mercado • Pará"
    centro(linha, caber(linha, FONTE_XBOLD, px(28), W - px(80)), y, (215, 215, 215))
    im.convert("RGB").save(destino, quality=95)
    return destino


def montar(clip, roteiro, palavras, out_path, foto_fundo=None, log=print, karaoke=None, legenda=None):
    """Gera o short final em out_path. True se o ffmpeg terminou com arquivo valido.
    karaoke (25/10): a palavra falada fica amarela; None = liga, salvo MS_KARAOKE=0. Se o ffmpeg falhar com ele, a
    montagem e refeita sem (nunca perde o video por causa do destaque).
    legenda (01/11): 'karaoke' ou 'cinetica' (escolher_legenda); a cinética que falhar é refeita em karaokê."""
    import os
    if karaoke is None:
        karaoke = os.environ.get("MS_KARAOKE", "1") != "0"
    if legenda is None:
        legenda = roteiro.get("legenda") or escolher_legenda()
    cinetica = legenda == "cinetica"
    layout = roteiro.get("layout") or escolher_layout()
    roteiro["layout"] = layout  # a 2a tentativa (ffmpeg falhou) mantém o mesmo layout
    TMP.mkdir(parents=True, exist_ok=True)
    stem = Path(out_path).stem
    for velho in TMP.glob(f"{stem}_*"):
        velho.unlink()
    from qa_ms import probe
    # corta os 0,3 s finais: o Veo as vezes estraga o ultimo quadro (faixa preta lateral no teste de 22/10)
    dur = probe(clip)[0] - CORTE_FIM_S
    alinhadas = alinhar(roteiro["fala_final"], palavras, dur)
    pedacos = [b for b in blocos_palavras(alinhadas) if b[1] < dur - EMENDA_S - 0.1]
    pngs = []
    gancho = TMP / f"{stem}_gancho.png"
    rosto = rosto_faixa(clip)
    _png_gancho(roteiro["gancho_tela"], gancho, tipo=roteiro.get("tipo"), rosto=rosto)
    if rosto:
        log(f"  [MONTAGEM] rosto entre {rosto[0]} e {rosto[1]} px: gancho posto fora dele")
    if layout == "aula":
        a, b = 2.6, dur - EMENDA_S
        if b - a > 1.5:
            terco = (b - a) / 3
            for k, etapa in enumerate(ETAPAS_AULA):
                p = TMP / f"{stem}_aula{k}.png"
                _png_aula(roteiro.get("titulo_aula") or roteiro["gancho_tela"], etapa, p, rosto=rosto)
                pngs.append((p, a + k * terco, a + (k + 1) * terco))
    mix = None
    if cinetica:
        mix = roteiro.get("legenda_mix") or escolher_mix()
        roteiro["legenda_mix"] = mix
        bc = blocos_cineticos(alinhadas)
        plano = plano_legenda(bc, stem, mix)
        # 01/11 (quadros): o apresentador desce/mexe depois dos 2,6 s e o queixo com barba passa da estimativa —
        # para a legenda, o rosto é medido no vídeo inteiro e com folga extra embaixo
        rl = rosto_faixa(clip, ate_s=dur)
        rosto_leg = (min(rl[0], rosto[0]) if rosto else rl[0], min(H, max(rl[1], rosto[1] if rosto else 0) + px(50))) \
            if rl else rosto
        anterior = None
        for i, (cima, forte, s, e) in enumerate(bc):
            fim = min(e, dur - EMENDA_S)
            if s >= dur - EMENDA_S - 0.1 or fim - s < 0.05:
                continue
            p_pop, p = TMP / f"{stem}_cin{i:02d}_p.png", TMP / f"{stem}_cin{i:02d}.png"
            topo = s > 2.8 and layout != "aula"  # o balão de abertura e a faixa da aula ocupam o topo
            _png_cinetica(cima, forte, p_pop, i, rosto=rosto_leg, pop=True, topo_livre=topo, estilo=plano[i])
            _png_cinetica(cima, forte, p, i, rosto=rosto_leg, topo_livre=topo, estilo=plano[i])
            puro = Image.open(p).convert("RGBA")
            if plano[i]["rastro"] and anterior is not None and not _encostam(anterior.getbbox(), puro.getbbox()):
                _com_rastro(p_pop, anterior)
                _com_rastro(p, anterior)
            anterior = puro
            meio = min(s + 0.09, fim)
            pngs.append((p_pop, s, meio - 0.01))
            if fim - meio >= 0.04:
                pngs.append((p, meio, fim - 0.02))  # sem quadro com 2 palavras na troca (between é fechado)
        pedacos = []
    for i, (texto, s, e, pal) in enumerate(pedacos):
        # termina quando a emenda com o cartao comeca (22/10: "MS Energy" ficava por cima do cartao entrando)
        fim = min(e, dur - EMENDA_S)
        n_txt = len(texto.split())
        if not karaoke or n_txt != len(pal):
            p = TMP / f"{stem}_leg{i:02d}.png"
            _png_legenda(texto, p)
            pngs.append((p, s, fim))
            continue
        for k in range(n_txt):  # 1 imagem por palavra: a falada em amarelo, do inicio dela ate a proxima
            ini_k = s if k == 0 else pal[k][1]
            fim_k = fim if k == n_txt - 1 else min(pal[k + 1][1], fim)
            if fim_k - ini_k < 0.05:
                continue
            p = TMP / f"{stem}_leg{i:02d}_{k}.png"
            _png_legenda(texto, p, destaque=k)
            pngs.append((p, ini_k, fim_k))
    pedacos = ([(t, s, e) for t, s, e, _pal in pedacos] if not cinetica else
               [((" ".join(c) + " " + f).strip(), s, e) for c, f, s, e in blocos_cineticos(alinhadas)])
    card = cartao(foto_fundo, TMP / f"{stem}_cartao.jpg")

    # SFX: estilos leves ganham 1-2 efeitos de som em palavras fortes (dona 01/11)
    usar_sfx = roteiro.get("estilo") in ESTILOS_LEVES and os.environ.get("MS_SFX", "1") != "0"
    sfx_entradas, sfx_momentos = [], []
    if usar_sfx:
        fortes_idx = [(w, s) for w, s, _e in alinhadas
                      if w.strip(".,!?;:\"'").lower() in FORTES and 1.5 < s < dur - 1.5]
        if not fortes_idx and alinhadas:
            meio = len(alinhadas) // 2
            fortes_idx = [(alinhadas[meio][0], alinhadas[meio][1])]
        n_sfx = min(2, len(fortes_idx))
        sfx_files = _escolher_sfx(n_sfx)
        if fortes_idx and sfx_files:
            escolhidas = _random.sample(fortes_idx, min(n_sfx, len(fortes_idx)))
            for sf, (_, momento) in zip(sfx_files, escolhidas):
                sfx_entradas.append(sf)
                sfx_momentos.append(max(0.0, momento - 0.15))

    entradas = ["-i", str(clip), "-loop", "1", "-framerate", "30", "-t", f"{CARTAO_S}", "-i", str(card),
                "-i", str(gancho)]
    for p, _, _ in pngs:
        entradas += ["-i", str(p)]
    n_sil = 3 + len(pngs)
    for sf in sfx_entradas:
        entradas += ["-i", str(sf)]
    n_sfx_base = n_sil + len(sfx_entradas)
    entradas += ["-f", "lavfi", "-t", f"{CARTAO_S}", "-i", "anullsrc=r=48000:cl=stereo"]
    fc = [f"[0:v]trim=0:{dur:.2f},setpts=PTS-STARTPTS,scale={W}:{H}:force_original_aspect_ratio=increase,"
          f"crop={W}:{H},fps=30,setsar=1,format=yuv420p[v0]",
          "[v0][2:v]overlay=0:0:enable='between(t,0,2.6)'[g0]"]
    atual = "g0"
    for i, (_, s, e) in enumerate(pngs):
        fc.append(f"[{atual}][{3 + i}:v]overlay=0:0:enable='between(t,{s:.2f},{e:.2f})'[l{i}]")
        atual = f"l{i}"
    fc.append(f"[{atual}]settb=AVTB,format=yuv420p[vc]")
    fc.append(f"[1:v]scale={W}:{H},fps=30,setsar=1,format=yuv420p,settb=AVTB[vk]")
    fc.append(f"[vc][vk]xfade=transition=fade:duration={EMENDA_S}:offset={dur - EMENDA_S:.2f}[v]")
    fc.append(f"[0:a]atrim=0:{dur:.2f},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,"
              f"afade=t=out:st={max(dur - 0.6, 0):.2f}:d=0.6[a0]")
    # Mixar SFX sobre o áudio da fala (volume reduzido para não abafar)
    audio_label = "a0"
    for k, (sf, momento) in enumerate(zip(sfx_entradas, sfx_momentos)):
        idx = n_sil + k
        # 01/11: SFX longo + duration=longest deixava o áudio com 17,6 s num vídeo de 10,6 s (fim preto, reprovado) e o
        # amix normalizado baixava a fala pela metade — agora cada SFX tem no máx. 2,5 s, o áudio acaba com a fala e a
        # fala fica no volume dela
        fc.append(f"[{idx}:a]atrim=0:2.5,afade=t=out:st=2.2:d=0.3,aresample=48000,aformat=channel_layouts=stereo,"
                  f"volume=0.45,adelay={int(momento * 1000)}|{int(momento * 1000)}[sfx{k}]")
        out = f"amx{k}"
        fc.append(f"[{audio_label}][sfx{k}]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[{out}]")
        audio_label = out
    fc.append(f"[{audio_label}][{n_sfx_base}:a]acrossfade=d={EMENDA_S}[a]")
    cmd = [FF, "-y", "-v", "error"] + entradas + ["-filter_complex", ";".join(fc), "-map", "[v]", "-map", "[a]",
                                                 "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt",
                                                 "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "160k",
                                                 "-movflags", "+faststart", str(out_path)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=600, encoding="utf-8", errors="replace")
    ok = r.returncode == 0 and Path(out_path).exists() and Path(out_path).stat().st_size > 200_000
    if not ok:
        log(f"  [MONTAGEM] ffmpeg falhou (exit {r.returncode}): {r.stderr[-600:]}")
        if sfx_entradas:
            log("  [MONTAGEM] refazendo SEM os SFX")
            os.environ["MS_SFX"] = "0"
            try:
                return montar(clip, roteiro, palavras, out_path, foto_fundo, log, karaoke=karaoke, legenda=legenda)
            finally:
                os.environ.pop("MS_SFX", None)
        if cinetica:
            log("  [MONTAGEM] refazendo com a legenda karaokê")
            return montar(clip, roteiro, palavras, out_path, foto_fundo, log, karaoke=karaoke, legenda="karaoke")
        if karaoke:
            log("  [MONTAGEM] refazendo SEM o destaque palavra por palavra")
            return montar(clip, roteiro, palavras, out_path, foto_fundo, log, karaoke=False, legenda="karaoke")
    else:
        sfx_info = f" | {len(sfx_entradas)} SFX" if sfx_entradas else ""
        log(f"  [MONTAGEM] ok: {Path(out_path).name} | {len(pedacos)} legendas"
            f"{f' CINÉTICAS mix {mix}' if cinetica else (' (palavra falada em amarelo)' if karaoke else '')}"
            f"{' | layout AULA' if layout == 'aula' else ''}{sfx_info}"
            f" | gancho '{roteiro['gancho_tela']}'")
    return ok, {"legendas": [(t, s, e) for t, s, e in pedacos], "cartao": str(card), "karaoke": bool(karaoke),
                "legenda_estilo": legenda, "layout": layout,
                "legenda_versao": "mix_0111" if cinetica else None, "legenda_mix": mix,
                "sfx": len(sfx_entradas)}
