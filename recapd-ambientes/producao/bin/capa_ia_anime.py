# -*- coding: utf-8 -*-
"""capa_ia_anime.py — capa do recap de anime (§2 de MELHORIAS_PARA_TODOS_OS_PROJETOS.md).

Pose de AÇÃO/BATALHA do catálogo config/POSES_ANIME.py (filtrada pelos gêneros da obra) + protagonista PARECIDO com o
da história + a premissa do vídeo. 16:9 (1280x720) no deitado, 9:16 (720x1280) no Short.
Esquema copiado de D:\\hipercool-videos\\bin\\capa_ia.py:
- imagem pelo gateway OmniRoute (antigravity/gemini-3.1-flash-image), cache por prompt; desligado por hora (dono
  20/10, imagem_reserva.GATEWAY): vai direto pra reserva;
- checagem por VISÃO (Gemini): letra/logo/emblema desenhado, sangue, cara de menor, tela dividida -> reprova e tenta
  outra pose (até 3 imagens);
- frase grande (texto_capa do SEO) com contorno preto, linhas branco/amarelo, fonte LuckiestGuy.
Protagonista: config/capas_anime.json (animes mais comuns) > protagonista_visual do SEO > herói genérico.
Sem capa (gateway fora, tudo reprovado) devolve None: anime_publish usa o quadro do vídeo, nunca trava a postagem.

Uso: python bin/capa_ia_anime.py --anime "Berserk" --cap 1 --saida teste.jpg [--texto "TRAÍDO POR TODOS"]
         [--cena "premissa em pt"] [--protagonista "adult man, black armor..."] [--formato 9:16]
"""
import argparse
import base64
import hashlib
import json
import random
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "config"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from POSES_ANIME import POSES, POSES_GENERO, REGRAS_BATALHA, ROUPAS_BATALHA, BATALHA, REGRAS_GERAIS  # noqa: E402
import visao_capa  # noqa: E402  (COMUM: corpo malformado + visão com reserva, igual ao hipercool)
import capa_longo_v2  # noqa: E402  (01/11 dona: regras novas das capas A/B/C do longo)

# Gênero pelo texto quando o SEO não manda "generos" (16/10: Horimiya caiu no padrão ação e saiu capa de batalha)
_GENERO_RE = [
    ("romance", r"romance|romântic|romantic|amor\b|apaixon|namor|crush|casal|beij|cora[cç][aã]o"),
    ("escolar", r"escola|colegial|aula|classe|professor|ensino m[eé]dio|high school"),
    ("comedia", r"com[eé]dia|engra[cç]ad|hil[aá]ri|zoeira|rir\b|risada"),
    ("drama", r"drama|chorou|l[aá]grima|triste|despedida|luto"),
    ("misterio", r"mist[eé]rio|terror|assombr|fantasma|assassin|detetive|suspense"),
    ("esporte", r"esporte|futebol|basquete|v[oô]lei|t[eê]nis|corrida|campeonato"),
    ("acao", r"luta|batalha|poder|espada|guerra|monstro|demônio|ninja|torneio|vilão"),
]


def _generos_do_texto(*textos):
    t = " ".join(x for x in textos if x).lower()
    return [g for g, rx in _GENERO_RE if re.search(rx, t)]

CFG_PERSONAGENS = PROJECT_DIR / "config" / "capas_anime.json"
CACHE = PROJECT_DIR / "workspace" / "cache" / "capa_ia_anime"
MODELO = "antigravity/gemini-3.1-flash-image"
FONTES = Path(r"D:\hipercool-materiais\assets\fonts")
QUADRO = {"9:16": (720, 1280), "16:9": (1280, 720)}
_PERGUNTA = (
    'Quality check of a drawn YouTube thumbnail. Answer ONLY JSON: {"letras": true/false (readable letters, words, '
    'numbers, logos, emblems or franchise symbols drawn anywhere; magic runes or abstract patterns do not count), '
    '"sangue": true/false (blood, wounds, gore or a dead body), "adultos": true/false (every character looks 18 or '
    'older — young adults count as adults; false only if someone looks like a child or teenager), "dividida": '
    'true/false (looks split into two panels or has a visible seam or border), "exposto": true/false (nipples, '
    'genitals or bare buttocks visible; cleavage, bikini or lingerie that covers everything do not count), '
    '"foto": true/false (a PHOTOGRAPH of a real person or real place instead of drawn anime/manhwa art), '
    '"escura": true/false (the image is mostly dark, gloomy, night or desaturated instead of bright and colorful), '
    '"ele": [ymin, xmin, ymax, xmax] (0-1000) box of the MAIN CHARACTER\'s face (the hero at the center of the '
    'scene, may be a man, a monster, an animal or a creature) or null, "ela": same box for the most prominent '
    'WOMAN\'s face or null, "rostos": list of [ymin, xmin, ymax, xmax] (0-1000) boxes of EVERY face in the image '
    '(all characters, also the small ones in the background), "vestidas": true/false (true if ANY woman wears '
    'normal clothes - school uniform, dress, gown, shirt, skirt, robe, armor, jacket, vest, shorts or pants, also '
    'fur or animal-skin dresses and tunics - instead of only a bikini or lingerie; rule of thumb: every woman\'s '
    'BELLY must be bare, if cloth or fur covers any woman\'s belly it is true; a see-through sheer veil or gown with '
    'the bikini clearly visible underneath does NOT count), ' + visao_capa.DEFEITOS + '}')


_ROUPAS = ('Look at EVERY woman in this image, one by one. Answer ONLY JSON {"mulheres": [{"roupa": "<what she wears, '
           'short>", "so_biquini": true/false, "fundo": true/false}]}. fundo is true ONLY for tiny background extras '
           '(villagers, crowd, passers-by far behind the main characters), false for the main women near the hero. '
           'so_biquini is true ONLY if she wears just a bikini or lingerie (small '
           'accessories like hats, gloves, jewelry, wristbands, a necklace or a see-through veil are fine). Chest or '
           'hip armor plates, skirts, shorts, dresses, uniforms, jackets, shirts, vests, fur tunics or anything that '
           'covers her belly = false.')


def _vestidas(img):
    """02/11 (RRrh A de armadura e shorts passou com "vestidas": false): o campo junto com 12 outros na checagem é
    fraco; uma pergunta só sobre a roupa de cada mulher. True = alguma vestida."""
    try:
        r = visao_capa.perguntar(Path(img).read_bytes(), _ROUPAS, gateway=_gateway(), max_tokens=500) or {}
    except Exception:  # noqa: BLE001
        return None  # 04/11: None = não conseguiu olhar (quem chama decide)
    if not r:
        return None
    ms = [m for m in (r.get("mulheres") or []) if isinstance(m, dict)]
    # 05/11 (KwdN B boa reprovada por 'purple dress (background village woman)'): figurante do fundo não conta
    vest = [m.get("roupa") for m in ms if m.get("so_biquini") is False and m.get("fundo") is not True
            and not re.search(r"background|villager|crowd|passer|extra", str(m.get("roupa")), re.I)]
    if vest:
        log(f"  capa: mulher vestida -> reprovada ({vest})")
    return bool(vest)


def _reprovada_v2(c, img=None):
    """Capas do longo (regras de 01-02/11): além do normal, mulher vestida reprova — 02/11 dona: "elas estão vestidas"
    (4wuf A, RRrh B, cLF1, 2jtd...). Só no caminho v2; os Shorts seguem com _reprovada."""
    # 04/11 (RA4H B 19:37 de uniforme/armadura entrou como B.jpg): a checagem voltou None e, sem ela, a pergunta da
    # roupa nem rodava. Agora a roupa é perguntada sempre; se nem a checagem nem a roupa responderem, reprova.
    if _reprovada(c) or bool(c and c.get("vestidas")):
        return True
    if not img:
        return False
    v = _vestidas(img)
    if v is None:
        return c is None
    return v


def _so_roupa_ou_letras(c):
    """06/11 dona: "tem que haver tolerância, vários vídeos estão sendo postados sem capas; se até a hora de postar
    não tiver conseguido aprovar uma capa nas exigências, posta com as rejeitadas de roupa mesmo". Tolerada = reprovada
    SÓ por roupa e/ou letras. Nunca: nudez (exposto), menor (adultos False), escura, dividida, sem checagem."""
    import os
    if os.environ.get("CAPA_TOLERANCIA", "1") == "0" or not c:
        return False
    if c.get("exposto") or c.get("adultos") is False or c.get("escura") or c.get("dividida") or c.get("sem_mulher") \
            or c.get("a_nao_dividida") or c.get("sangue") or c.get("foto"):
        return False
    return True


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _chave(nome):
    s = unicodedata.normalize("NFKD", nome or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")


def _cfg_anime(anime):
    """Config fixa do anime (capas_anime.json) ou None."""
    try:
        cfg = json.loads(CFG_PERSONAGENS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return cfg.get(_chave(anime))


def _gateway():
    """base_url/api_key do gateway: secrets/omniroute.json deste projeto (reserva: o do hipercool)."""
    for p, kb, kt in ((PROJECT_DIR / "secrets" / "omniroute.json", "base_url", "api_key"),
                      (Path(r"D:\hipercool-videos\secrets\claude_proxy.json"), "base_url", "auth_token")):
        try:
            c = json.loads(p.read_text(encoding="utf-8"))
            return c[kb].rstrip("/"), c[kt]
        except (OSError, ValueError, KeyError):
            continue
    return None, None


def _gerar(prompt, formato):
    """Imagem (Path) pro prompt — do cache, do gateway (se imagem_reserva.GATEWAY) ou da reserva (imagem_reserva:
    Cloudflare/Pollinations). None se nada gerou."""
    import imagem_reserva
    CACHE.mkdir(parents=True, exist_ok=True)
    out = CACHE / f"{hashlib.md5(prompt.encode()).hexdigest()[:16]}.png"
    if out.exists() and out.stat().st_size > 5000:
        return out
    base, tok = _gateway() if imagem_reserva.GATEWAY else (None, None)
    b64 = None
    if imagem_reserva.GATEWAY and not base:
        log("  capa IA: sem credencial do gateway")
    elif base:
        corpo = json.dumps({"model": MODELO, "prompt": prompt, "n": 1, "response_format": "b64_json",
                            "size": "1024x1792" if formato == "9:16" else "1792x1024",
                            "aspect_ratio": formato}).encode()
        req = urllib.request.Request(base + "/v1/images/generations", data=corpo,
                                     headers={"Content-Type": "application/json", "Authorization": "Bearer " + tok})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                b64 = ((json.loads(r.read()).get("data") or [{}])[0]).get("b64_json")
        except urllib.error.HTTPError as e:
            log(f"  capa IA: gateway HTTP {e.code} {e.read().decode('utf-8', 'replace')[:120]}")
        except Exception as e:  # noqa: BLE001
            log(f"  capa IA: gateway falhou ({type(e).__name__}: {str(e)[:100]})")
    if b64:
        out.write_bytes(base64.b64decode(b64))
        return out
    img, quem = imagem_reserva.gerar(prompt, formato)
    if not img:
        log(f"  capa IA: reserva também não gerou ({quem[:300]})")
        return None
    log(f"  capa IA: imagem pela reserva ({quem})")
    out.write_bytes(img)
    return out


def _checar(img):
    """Checagem por visão (Gemini; se ele falhar, Claude pelo gateway — visao_capa). None se os dois falharem (aí
    vale a imagem: as regras já vão no prompt)."""
    try:
        b = Path(img).read_bytes()
    except OSError:
        return None
    r = visao_capa.perguntar(b, _PERGUNTA, gateway=_gateway())
    if r is None:
        log("  capa IA: checagem por visão indisponível (Gemini e gateway)")
    return r


def _reprovada(c):
    """Letra/logo, sangue, cara de menor, tela dividida e (dono 20/10) corpo malformado. Multidão não reprova: faz
    parte de cena de batalha."""
    # 30/10: "exposto" — a versão sensual do teste A/B chega perto da linha; nudez nunca vai pra capa (hipercool
    # levou advertência de nudez em 16/10)
    # 01/11 dona: capa no ar com foto de homem real (05_CenaReact) e capas escuras — "foto"/"escura" reprovam
    return bool(c) and bool(c.get("letras") or c.get("sangue") or c.get("adultos") is False or c.get("dividida")
                            or c.get("exposto") or c.get("foto") or c.get("escura")
                            or visao_capa.defeitos(c, figurantes=False))


def _fonte(nome, tam):
    from PIL import ImageFont
    for n in (nome, "impact.ttf"):
        try:
            return ImageFont.truetype(str(FONTES / n), tam)
        except OSError:
            continue
    return ImageFont.load_default()


def _quebrar(d, texto, f, larg):
    linhas, cur = [], ""
    for w in texto.split():
        tst = (cur + " " + w).strip()
        if cur and d.textlength(tst, font=f) > larg:
            linhas.append(cur)
            cur = w
        else:
            cur = tst
    return linhas + ([cur] if cur else [])


# ───────── mascote na capa (dona 30/10: "adicionar também a mascote na capa") ─────────
# A mascote é chibi (cara de criança): entra COLADA por cima como figurinha (PNG com alfa), nunca desenhada pela IA
# junto das mulheres — assim a sensualidade fica só nas adultas e a checagem de "cara de menor" não reprova a capa.
# 01/11 dona: a mascote antiga (chibi roxa) sai de tudo — a figurinha agora é a Maria recortada (cosplays, PNG com
# alfa). Fora: estudante (uniforme escolar é proibido na capa) e recortes de meio corpo.
MASCOTE_DIR = Path(r"D:\hipercool-materiais\mascote_waifu_v2\cosplay_recorte")


def _colar_mascote(capa, semente="", lado="direita", alto=0.46):
    """Cola a mascote (contorno branco de figurinha + sombra) no canto de baixo. Devolve a pose usada ou None."""
    import os
    from PIL import Image, ImageFilter
    if os.environ.get("CAPA_MASCOTE", "1") == "0":
        return None
    fotos = sorted(p for p in MASCOTE_DIR.glob("*.png") if "estudante" not in p.name) if MASCOTE_DIR.exists() else []
    fotos = [p for p in fotos if Image.open(p).height >= 900]
    if not fotos:
        return None
    foto = fotos[int(hashlib.md5(str(semente).encode()).hexdigest(), 16) % len(fotos)]
    pose = foto.stem
    m = Image.open(foto).convert("RGBA")
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
    y = H - fig.height + int(fig.height * 0.06)  # pé um pouco pra fora do quadro, como figurinha colada
    base = capa.convert("RGBA")
    base.alpha_composite(sombra, (max(0, x + borda), max(0, min(H - 1, y + borda))))
    base.alpha_composite(fig, (max(0, x), max(0, y)))
    capa.paste(base.convert("RGB"))
    return pose


# ───────── etiqueta (estilo @AmericanNickas, dona 30/10: "as frases e como ele cola as frases") ─────────
# Lá é sempre UMA palavra (o arquétipo: YANDERE) gigante em amarelo com contorno preto, colada embaixo no meio por
# cima da personagem, com uma seta amarela curva subindo até o rosto dela — e a mesma palavra em vídeo após vídeo.
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
    """Rótulo DELE (o protagonista) nas capas de rótulos — o arquétipo da história, senão "PROTA"."""
    t = f"{cena} {texto}".lower()
    return next((p for p, rx in _PAPEIS if re.search(rx, t)), "PROTA")


def _etiqueta(texto="", cena=""):
    t = f"{cena} {texto}".lower()
    for palavra, rx in _ETIQUETAS:
        if re.search(rx, t):
            return palavra
    pal = re.sub(r"[^\wÀ-ú ]", " ", texto or "").split()
    return " ".join(pal[:2]).upper() if pal else ""


AMARELO, PRETO = (255, 236, 0), (0, 0, 0)


def _lua(d, p0, p2, bojo, esp, contorno):
    """Seta em meia-lua amarela (grossa no meio, fina nas pontas) de p0 até p2, bojuda pro lado `bojo` (+1/-1):
    curva de Bézier com a espessura em seno, contorno preto."""
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
    d.line(lua + [lua[0]], fill=PRETO, width=contorno, joint="curve")
    d.polygon(lua, fill=AMARELO)


def _caber(d, texto, larg_max, tam):
    while tam > 30:
        f = _fonte("LuckiestGuy-Regular.ttf", tam)
        if d.textlength(texto, font=f) <= larg_max:
            return f, tam
        tam -= 6
    return _fonte("LuckiestGuy-Regular.ttf", tam), tam


def _desenhar_etiqueta(capa, palavra, rosto=None):
    """Palavra gigante amarela embaixo no meio + meia-lua amarela subindo até o rosto dela (caixa em px; sem caixa,
    pro meio de cima da imagem)."""
    from PIL import ImageDraw
    W, H = capa.size
    d = ImageDraw.Draw(capa)
    vertical = H > W
    f, tam = _caber(d, palavra, W * (0.86 if vertical else 0.62), int(H * (0.11 if vertical else 0.2)))
    larg = d.textlength(palavra, font=f)
    x = (W - larg) / 2
    y = int(H * (0.62 if vertical else 0.66))
    p0 = (x + larg * 0.86, y + tam * 0.12)
    if rosto and rosto[3] < y:  # termina logo abaixo/ao lado do queixo dela
        p2 = (min(max(rosto[0], 20), W - 20) if (rosto[0] + rosto[2]) / 2 > p0[0] else rosto[2], rosto[3] + tam * 0.1)
    else:
        p2 = (x + larg * 0.70, y - tam * 1.25)
    _lua(d, p0, p2, -1 if p2[0] < p0[0] else 1, tam * 0.16, max(6, tam // 14))
    d.text((x, y), palavra, font=f, fill=AMARELO, stroke_width=max(8, tam // 11), stroke_fill=PRETO)


# rótulos estilo Porão/Zeni/Trigger (as capas de 35 mil a 300 mil views das referências da dona, 30/10): palavras
# curtas amarelas com contorno preto, cada uma com uma seta até o personagem — o papel dele ("PROTA") e a fala dela
FALAS_DELA = ("VEM, BONITÃO!", "VOCÊ É MEU!", "ESTÁ LIVRE HOJE?", "NÃO FOGE DE MIM!", "SÓ MEU!", "ME ESCOLHE!")


def _seta(d, ini, fim, esp, contorno):
    """Seta amarela grossa com ponta (como as das capas do Porão), levemente curva, de ini até fim; contorno preto."""
    import math
    vx, vy = fim[0] - ini[0], fim[1] - ini[1]
    n = math.hypot(vx, vy) or 1
    ux, uy = vx / n, vy / n
    cab = min(esp * 2.6, n * 0.45)  # tamanho da ponta
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
        d.line(forma + [forma[0]], fill=PRETO, width=contorno, joint="curve")
    d.polygon(corpo, fill=AMARELO)
    d.polygon(ponta, fill=AMARELO)


def _os_env(nome, padrao):
    import os
    return os.environ.get(nome, padrao)


def _rotulos(capa, rotulos, manter=False, evitar=()):
    """rotulos = [(texto, caixa do rosto em px ou None)]. Cada texto vai num lugar livre perto do rosto (acima, ao
    lado, abaixo — senão o lugar livre mais perto no quadro) com uma seta até a borda do rosto; sem rosto, sem seta.
    evitar = caixas (px) de todos os rostos da cena: 02/11 dona (SNhb A) "a frase está na cara deles"."""
    from PIL import ImageDraw
    W, H = capa.size
    d = ImageDraw.Draw(capa)

    def dentro(c):  # rosto cortado pelo enquadramento (9:16) quase todo fora = sem rosto
        if not c:
            return None
        x0, y0, x1, y1 = max(0, c[0]), max(0, c[1]), min(W, c[2]), min(H, c[3])
        return c if x1 > x0 and y1 > y0 and (x1 - x0) * (y1 - y0) >= 0.5 * (c[2] - c[0]) * (c[3] - c[1]) else None
    # rótulo sem o rosto de quem ele aponta no quadro (a visão não achou, ou o 9:16 cortou) fica de fora: a fala dela
    # boiando em cima dele confunde
    # manter (01/11, rótulos da capa original): "as palavras do original não podem faltar" — sem alvo, vai sem seta
    rotulos = [(t if dentro(c) or manter else "", dentro(c)) for t, c in rotulos]
    # o que não pode ser coberto: os rostos, o canto da mascote e os rótulos já postos
    bloqueio = [c for _, c in rotulos if c] + [c for c in evitar if c] + [(W * (0.62 if H > W else 0.85), H * 0.62, W, H)]

    def livre(r):
        return (r[0] >= W * 0.02 and r[2] <= W * 0.98 and r[1] >= H * 0.02 and r[3] <= H * 0.98
                and not any(r[0] < b[2] and b[0] < r[2] and r[1] < b[3] and b[1] < r[3] for b in bloqueio))
    for i, (txt, cx) in enumerate(rotulos):
        if not txt:
            continue
        f, tam = _caber(d, txt, W * (0.8 if H > W else 0.36), int(min(W, H) * 0.13))
        larg, alt = d.textlength(txt, font=f), tam * 1.05
        alvo = ((cx[0] + cx[2]) / 2, (cx[1] + cx[3]) / 2) if cx else (W * (0.25 + 0.5 * (i % 2)), H * 0.1)

        # 02/11 (LAei A dividida): "ANTES" apontava pro painel da esquerda mas foi escrito no da direita. Alvo bem de um
        # lado = o rótulo fica do mesmo lado (cada palavra no seu painel)
        def mesmo_lado(x, _a=alvo[0], _l=larg):
            return abs(_a - W / 2) < W * 0.12 or ((x + _l / 2) < W / 2) == (_a < W / 2)
        pos = None
        if cx:
            gap = tam * 1.3  # espaço da seta
            cmx = alvo[0] - larg / 2
            fora = cx[0] - larg - gap, cx[2] + gap  # esquerda, direita
            # acima (centrado, terminando no rosto, começando no rosto), ao lado (o de fora primeiro), abaixo
            acima = cx[1] - alt - gap
            lados = [(x, acima) for x in (cmx, cx[2] - larg, cx[0])]
            lados += [(x, alvo[1] - alt / 2) for x in (fora if alvo[0] < W / 2 else fora[::-1])]
            lados += [(x, cx[3] + gap) for x in (cmx, cx[2] - larg, cx[0])]
            pos = next(((x, y) for x, y in lados if livre((x, y, x + larg, y + alt)) and mesmo_lado(x)), None)
        if not pos:  # varre o quadro: o lugar livre mais perto do alvo, longe o bastante pra seta aparecer
            def longe(c):
                if not cx:
                    return True
                dx = max(cx[0] - (c[0] + larg), c[0] - cx[2], 0)
                dy = max(cx[1] - (c[1] + alt), c[1] - cx[3], 0)
                return (dx * dx + dy * dy) ** 0.5 >= tam * 0.8
            cands = [(W * fx - larg / 2, H * fy) for fy in (0.03, 0.12, 0.22, 0.34, 0.46, 0.58, 0.7, 0.8)
                     for fx in (0.22, 0.35, 0.5, 0.65, 0.78)]
            cands = [c for c in cands if livre((c[0], c[1], c[0] + larg, c[1] + alt)) and longe(c)]
            cands = [c for c in cands if mesmo_lado(c[0])] or cands
            pos = min(cands, key=lambda c: (c[0] + larg / 2 - alvo[0]) ** 2 + (c[1] + alt / 2 - alvo[1]) ** 2) \
                if cands else None
            # 13/11 dona (PARTE 14: "INIMIGO" escrito por cima de "EXÉRCITO DO PROTAGONISTA"): sem lugar livre, o
            # rótulo caía num canto FIXO sem olhar o que já estava lá. Agora tenta menor (70% e 50%) num lugar livre;
            # se ainda não couber, fica de fora (melhor sem a palavra do que palavra em cima de palavra).
            # CAPA_ROTULO_SEM_SOBREPOR=0 volta o canto fixo.
            if pos is None and _os_env("CAPA_ROTULO_SEM_SOBREPOR", "1") != "0":
                for esc in (0.7, 0.5):
                    f2, tam2 = _caber(d, txt, W * (0.8 if H > W else 0.36) * esc, int(min(W, H) * 0.13 * esc))
                    l2, a2 = d.textlength(txt, font=f2), tam2 * 1.05
                    c2 = [(W * fx - l2 / 2, H * fy) for fy in (0.03, 0.12, 0.22, 0.34, 0.46, 0.58, 0.7, 0.8)
                          for fx in (0.22, 0.35, 0.5, 0.65, 0.78)]
                    c2 = [c for c in c2 if livre((c[0], c[1], c[0] + l2, c[1] + a2))]
                    if c2:
                        pos = min(c2, key=lambda c: (c[0] + l2 / 2 - alvo[0]) ** 2 + (c[1] + a2 / 2 - alvo[1]) ** 2)
                        f, tam, larg, alt = f2, tam2, l2, a2
                        break
                if pos is None:
                    log(f"  rótulo '{txt}' sem lugar livre — fica de fora (não escreve por cima de outro)")
                    continue
            elif pos is None:
                pos = (W * 0.04, H * 0.04 + i * alt * 1.2)
        x, y = pos
        if cx:
            # da borda da palavra mais perto do rosto até a borda do rosto
            ini = (min(max(alvo[0], x + larg * 0.15), x + larg * 0.85),
                   y + alt if y + alt <= cx[1] else y if y >= cx[3] else y + alt / 2)
            if y + alt > cx[1] and y < cx[3]:  # ao lado
                ini = (x + larg if x + larg <= cx[0] else x, y + alt / 2)
            fx = min(max(ini[0], cx[0] + (cx[2] - cx[0]) * 0.2), cx[2] - (cx[2] - cx[0]) * 0.2)
            fy = min(max(ini[1], cx[1] + (cx[3] - cx[1]) * 0.25), cx[3] - (cx[3] - cx[1]) * 0.25)
            fim = (cx[0] - tam * 0.1 if ini[0] < cx[0] else cx[2] + tam * 0.1 if ini[0] > cx[2] else fx,
                   cx[1] - tam * 0.1 if ini[1] < cx[1] else cx[3] + tam * 0.1 if ini[1] > cx[3] else fy)
            _seta(d, ini, fim, tam * 0.3, max(5, tam // 14))
        bloqueio.append((x, y, x + larg, y + alt))
        d.text((x, y), txt, font=f, fill=AMARELO, stroke_width=max(6, tam // 10), stroke_fill=PRETO)


def _caixa_visao(v):
    """[ymin, xmin, ymax, xmax] 0-1000 da visão -> (x0, y0, x1, y1) em 0-1, ou None."""
    try:
        y0, x0, y1, x1 = [float(n) / 1000 for n in v]
        return (x0, y0, x1, y1) if x1 > x0 and y1 > y0 else None
    except (TypeError, ValueError):
        return None


def _compor(img_path, texto, out_jpg, quadro, estilo="frase", mascote=None, rostos=None, fala="", rotulos_extra=None):
    """Recorta pra preencher o quadro e escreve a frase grande (16:9: à esquerda; 9:16: no alto). JPEG < 2 MB.
    estilo="etiqueta": uma palavra só, embaixo no meio, com meia-lua até o rosto dela (AmericanNickas);
    estilo="rotulos": `texto` (papel dele) e `fala` (dela), cada um com seta pro rosto (Porão/Zeni/Trigger).
    rostos = a checagem da visão (campos "ele"/"ela"). mascote = semente da figurinha da mascote (None = sem)."""
    from PIL import Image, ImageDraw
    W, H = quadro
    img = Image.open(img_path).convert("RGB")
    sc = max(W / img.width, H / img.height)
    iw, ih = int(img.width * sc) + 1, int(img.height * sc) + 1
    img = img.resize((iw, ih), Image.LANCZOS)
    ox, oy = (img.width - W) // 2, (img.height - H) // 2
    capa = img.crop((ox, oy, ox + W, oy + H))

    def px(quem):  # caixa do rosto (0-1 da imagem gerada) -> px da capa recortada
        c = _caixa_visao((rostos or {}).get(quem))
        return (c[0] * iw - ox, c[1] * ih - oy, c[2] * iw - ox, c[3] * ih - oy) if c else None

    def px_v(v):
        c = _caixa_visao(v)
        return (c[0] * iw - ox, c[1] * ih - oy, c[2] * iw - ox, c[3] * ih - oy) if c else None
    caras = [px("ele"), px("ela")] + [px_v(v) for v in ((rostos or {}).get("rostos") or []) if isinstance(v, list)]
    if mascote is not None:
        # frase à esquerda (16:9) / no alto (9:16): a mascote fica no canto de baixo à direita; com etiqueta no meio,
        # também à direita e menor pra não cobrir a palavra
        _colar_mascote(capa, mascote, "direita", 0.46 if estilo == "frase" else 0.36)
    texto = re.sub(r"\s+", " ", texto or "").strip().upper()
    frase = None  # (fonte, linhas, altura da linha, y inicial, caixa) — medida ANTES dos rótulos
    if texto and estilo == "frase":
        d = ImageDraw.Draw(capa)
        vertical = H > W
        area = int((0.88 if vertical else 0.42) * W)
        tam = 104 if vertical else 112
        while True:
            f = _fonte("LuckiestGuy-Regular.ttf", tam)
            linhas = _quebrar(d, texto, f, area)
            if len(linhas) <= 3 or tam <= 52:
                break
            tam -= 8
        lh = int(tam * 1.1)
        y0 = int(0.06 * H) if vertical else (H - len(linhas) * lh) // 2
        larg = max(d.textlength(ln, font=f) for ln in linhas)
        x0 = (W - larg) / 2 if vertical else 40
        frase = (f, linhas, lh, y0, (x0 - 12, y0 - 12, x0 + larg + 12, y0 + len(linhas) * lh + 12))
    if rotulos_extra:  # 01/11: os rótulos da capa original, cada um com seta pro mesmo objeto na capa nova
        # 14/11 (dona, Medieval 14 e 11: "INIMIGO" por cima de "EXÉRCITO DO PROTAGONISTA", setas pra nada): os rótulos
        # do original apontavam pros NAVIOS do parceiro; na capa nova não há navio, a visão não achou o alvo e os dois
        # caíam no topo, um sobre o outro. Rótulo cujo objeto não existe na capa nova fica de fora.
        # CAPA_ROTULO_SO_COM_ALVO=0 volta a escrever sem alvo.
        lista = [(t, px_v(v)) for t, v in rotulos_extra]
        if _os_env("CAPA_ROTULO_SO_COM_ALVO", "1") != "0":
            fora = [t for t, c in lista if not c]
            lista = [(t, c) for t, c in lista if c]
            if fora:
                log(f"  rótulos sem o objeto na capa nova — ficam de fora: {', '.join(fora)}")
        # 02/11 (P-djts A): o rótulo "DEUSA" ficou embaixo da frase grande — a frase entra no bloqueio
        if lista:
            _rotulos(capa, lista, manter=True, evitar=caras + ([frase[4]] if frase else []))
    if estilo == "etiqueta":
        if texto:
            _desenhar_etiqueta(capa, texto, px("ela") or px("ele"))
        texto = ""
    elif estilo == "rotulos":
        if texto or fala:
            _rotulos(capa, [(texto, px("ele")), ((fala or "").upper(), px("ela"))], evitar=caras)
        texto = ""
    if texto and frase:
        d = ImageDraw.Draw(capa)
        vertical = H > W
        f, linhas, lh, y, _cx = frase
        for i, ln in enumerate(linhas):
            x = (W - d.textlength(ln, font=f)) / 2 if vertical else 40
            d.text((x, y), ln, font=f, fill=(255, 214, 0) if i % 2 else (255, 255, 255),
                   stroke_width=9, stroke_fill=(0, 0, 0))
            y += lh
    Path(out_jpg).parent.mkdir(parents=True, exist_ok=True)
    for q in (90, 82, 72):
        capa.save(out_jpg, "JPEG", quality=q)
        if Path(out_jpg).stat().st_size < 1_900_000:  # o YouTube aceita até 2 MB
            break
    return Path(out_jpg)


def _pronomes(txt, feminino):
    """As poses são escritas com HE/his/him; protagonista mulher troca (e o par 'HE and SHE' vira 'SHE and HE')."""
    if not feminino:
        return txt
    troca = {"HE": "SHE", "SHE": "HE", "he": "she", "she": "he", "his": "her", "him": "her", "himself": "herself"}
    return re.sub(r"\b(HE|SHE|he|she|his|him|himself)\b", lambda m: troca[m.group(1)], txt)


def _poses(generos):
    gs = set(generos or [])
    ps = [p for p in POSES if not POSES_GENERO.get(p) or gs & POSES_GENERO[p]]
    try:  # Thompson pelo placar de capas (views em 48 h, medir_48h; 21/10); sem dados = sorteio como antes
        import placar_titulos
        pl = {}
        for g in ("anime", "recapd", "parceiro"):
            for k, (t, v) in placar_titulos.taxas("capas", g).items():
                a = pl.get(k, (0, 0))
                pl[k] = (a[0] + t, a[1] + v)
        ps.sort(key=lambda p: -random.betavariate(pl.get(p, (0, 0))[1] + 1, pl.get(p, (0, 0))[0] - pl.get(p, (0, 0))[1] + 1))
    except Exception:  # noqa: BLE001
        random.shuffle(ps)
    return ps or ["segredo_revelado", "reacao_comica", "olhar_cumplice"]  # nada casou: clima neutro, nunca batalha


def _capa_do_parceiro(source_url):
    """Miniatura pública do vídeo original (i.ytimg.com, sem yt-dlp) — None se não achou."""
    m = re.search(r"(?:v=|youtu\.be/|shorts/)([\w-]{11})", source_url or "")
    if not m:
        return None
    CACHE.mkdir(parents=True, exist_ok=True)
    out = CACHE / f"parceiro_{m.group(1)}.jpg"
    if out.exists() and out.stat().st_size > 5000:
        return out
    for nome in ("maxresdefault", "sddefault", "hqdefault"):
        try:
            with urllib.request.urlopen(f"https://i.ytimg.com/vi/{m.group(1)}/{nome}.jpg", timeout=30) as r:
                dado = r.read()
            if len(dado) > 5000:  # a "sem imagem" do YouTube tem ~1 KB
                out.write_bytes(dado)
                return out
        except Exception:  # noqa: BLE001
            continue
    return None


# 30/10 teste real (formiga do nV2aNVwUL-A): com "HIM" na pose a IA trocou o protagonista-formiga por um rapaz humano
MESMO_PROTAGONISTA = ("HE / HIM = the main character EXACTLY as drawn in the reference, keeping his species and body: "
                      "if he is a monster, an animal, an insect or a creature, he stays that creature, never turned "
                      "into a human; he is large and central in the frame.")

# 29/10 dona: "a ideia sempre é pegar a capa e melhorar ela, porque muitas dessas obras os caras conhecem pelos
# personagens principais que estão nas capas; pode copiar coisas dela, tipo o personagem principal, e adicionar
# mulheres sexys sempre que possível, que combine". Capas da dona: elas vestidas, nada exposto nem borrado.
# 01/11 dona: "mesmos personagens da original só que melhorados, SEMPRE COLORIDAS e não dark, e com mulheres sensuais
# como a mascote" — a Maria (2ª referência) entra na cena com roupa reveladora + outra mulher que combine.
REFAZER = ("Recreate and IMPROVE the FIRST reference image (a YouTube thumbnail) as a brand-new {fmt} anime "
           "thumbnail. Keep the SAME main character(s) from it - same face, hair, eyes, outfit and weapon - and the "
           "same story elements, so fans instantly recognize the story. Make it more striking: one single scene "
           "(never a split screen or panels), the hero large in the frame. Colors: BRIGHT, SUNNY, VIVID and HIGHLY "
           "SATURATED, glossy lighting, sharp clean manhwa art - never dark, gloomy, desaturated or night. "
           "Add MARIA: the woman from the SECOND reference image - same face, long wavy dark-brown hair, golden-brown "
           "eyes, tanned skin, curvy grown-up adult body in her late twenties - wearing the most revealing outfit "
           "that fits this story's world (a bikini or lace lingerie in a modern story; a jeweled bikini-armor or a "
           "low-cut gown with a high slit in a fantasy or historical story), clinging to the hero's arm and smiling "
           "at the viewer. Add one more gorgeous curvy ADULT woman that fits the story, also in a revealing outfit, "
           "flirting with the hero. Blushing and flirty, nothing private exposed, no nudity. {cena}Remove ALL text, "
           "letters, logos, channel marks and watermarks. {vazio} {mesmo}")
MARIA_DIR = Path(r"D:\hipercool-materiais\mascote_waifu_v2\andando_16x9")


def _maria(semente):
    """Foto da Maria (mascote) de corpo inteiro pra 2ª referência, em rodízio pela semente — None se a pasta sumiu."""
    fotos = sorted(p for p in MARIA_DIR.glob("*.png") if not p.name.startswith("amiga_")) if MARIA_DIR.exists() else []
    return fotos[int(hashlib.md5(str(semente).encode()).hexdigest(), 16) % len(fotos)] if fotos else None


def _gerar_com_ref(prompt, ref, formato, extras=()):
    """Imagem a partir da capa do parceiro pelo Flow (Nano Banana, por HTTP, 0 crédito) — None se não gerou.
    extras = mais referências depois da capa (a Maria)."""
    CACHE.mkdir(parents=True, exist_ok=True)
    extras = [str(e) for e in extras if e]
    chave = hashlib.md5(prompt.encode() + Path(ref).read_bytes() + "|".join(extras).encode()).hexdigest()[:16]
    out = CACHE / f"ref_{chave}.png"
    feitos = sorted(CACHE.glob(f"ref_{chave}*.png"))
    if feitos and feitos[0].stat().st_size > 5000:
        return feitos[0]
    import os
    import subprocess
    try:
        r = subprocess.run([r"D:\veo\venv\Scripts\python.exe", r"D:\flow-imagens\gera_imagem.py", prompt, str(out),
                            "--ref", str(ref), *extras, "--formato", formato, "--quantidade", "1", "--maquinas",
                            # 01/11 23h: sem pc1 — o Chrome daqui (sem memória virtual) ficava 50 min preso
                            # 12/11: + STI (i5 16 GB, portas extras) — sem ele as capas só tinham as máquinas
                            # ocupadas pelo telão/Veo e saía ~1 capa a cada 10 h (o STI gerava 25 img/h pra outros)
                            os.environ.get("CAPA_MAQUINAS", "sti,desktop,x200ma,acer,pc2"), "--max-contas", "6"],
                           capture_output=True, timeout=1500, creationflags=0x08000000)
        if r.returncode != 0:
            err = (r.stderr or b"").decode("utf-8", "replace").strip()[-200:] if r.stderr else "(sem stderr)"
            log(f"  capa: Flow retornou erro rc={r.returncode} — {err}")
    except subprocess.TimeoutExpired:
        log("  capa: Flow sem resposta em 25 min")
    feitos = sorted(CACHE.glob(f"ref_{chave}*.png"))
    if not feitos or feitos[0].stat().st_size <= 5000:
        return None
    # 31/10: o Flow devolveu pra capa B 16:9 do -E5o1Q1JrPE uma foto VERTICAL de um homem real (imagem de outro
    # pedido) e a checagem aprovou. Proporção diferente da pedida = imagem que não é desta capa: descarta.
    try:
        from PIL import Image
        with Image.open(feitos[0]) as im:
            prop = im.width / im.height
        quer = 9 / 16 if formato == "9:16" else 16 / 9
        if abs(prop / quer - 1) > 0.2:
            log(f"  imagem do Flow com proporção {prop:.2f} (pedida {quer:.2f}) — não é desta capa, descartada")
            feitos[0].unlink(missing_ok=True)
            return None
    except OSError:
        return None
    return feitos[0]


_TEXTO_ORIGINAL = (
    'Read the text written on this YouTube thumbnail (ignore channel logos, watermarks and tiny unreadable marks). '
    'Answer ONLY JSON: {"rotulos": [{"texto": "<label translated to Brazilian Portuguese, UPPERCASE, max 4 words>", '
    '"alvo": "<in English, the thing or person the label/arrow points to, e.g. old wooden sailing ship>"}], '
    '"titulo": "<any other text (title/caption) translated to Brazilian Portuguese, UPPERCASE, max 6 words, or empty>"}. '
    'Labels are short words placed next to or with an arrow to something; use [] when there are none. '
    # 02/11 dona (C6YG A "MUNDO NATAL"): "não pode ter natal e sim origem, porque natal remete à data e não ao lugar"
    'Translate by MEANING, never with a word that in Portuguese suggests something else: homeworld / home world / '
    'hometown = "MUNDO DE ORIGEM" / "TERRA DE ORIGEM" (NEVER "NATAL", which means Christmas); MC = "PROTAGONISTA".'
    # 12/11 dona (GRVG A "ENTEDIADO" vindo de "BORED"): "o que tem a ver? não é chamativo; talvez se fosse a mulher
    # entediada eu entenderia". Adjetivo solto e morno, sem dono, não chama clique: vira gancho com o mesmo sentido.
    ' The label must work as a CLICK HOOK in Portuguese, not a dry dictionary translation: a lone mild adjective or '
    'state word (bored, tired, lazy, calm, sleepy, normal) becomes a short punchy phrase with the same meaning that says '
    'WHO and WHY, e.g. BORED -> "TÃO FORTE QUE SE ENTEDIA" or "ENTEDIADO DE TÃO FORTE"; LAZY -> "PREGUIÇOSO MAS O MAIS '
    'FORTE"; WEAK -> "O MAIS FRACO?". Keep strong single words as they are (YANDERE, SSS, LEVEL 999, TRAIDORA).')


_MORNO = {  # 12/11 dona (GRVG "ENTEDIADO"): palavra morna sozinha na capa não chama clique -> gancho, mesmo sentido
    "ENTEDIADO": "TÃO FORTE QUE SE ENTEDIA", "ENTEDIADA": "ELA ESTÁ ENTEDIADA?", "CANSADO": "CANSADO DE VENCER",
    "PREGUIÇOSO": "PREGUIÇOSO MAS O MAIS FORTE", "CALMO": "CALMO DEMAIS", "SONOLENTO": "DORME E VENCE",
    "NORMAL": "NADA NORMAL", "FRACO": "O MAIS FRACO?", "TRISTE": "ELE NÃO CHORA MAIS",
}


def _sem_ambiguo(s):
    """02/11 dona: "natal" remete à data (Natal), não ao lugar -> "ORIGEM". Rede de segurança depois da visão.
    12/11: palavra morna sozinha (_MORNO) vira gancho. CAPA_SEM_MORNO=0 desliga."""
    import os
    if os.environ.get("CAPA_SEM_MORNO", "1") != "0" and (s or "").strip() in _MORNO:
        return _MORNO[s.strip()]
    s = re.sub(r"\bMUNDO NATAL\b", "MUNDO DE ORIGEM", s or "")
    s = re.sub(r"\bTERRA NATAL\b", "TERRA DE ORIGEM", s)
    return re.sub(r"\bNATAL\b", "DE ORIGEM", s)
_ACHAR = ('Find these things in the image and answer ONLY JSON {"caixas": [[ymin, xmin, ymax, xmax] or null, ...]} '
          '(0-1000, same order): ')


def _sem_mojibake(s):
    """01/11: a visão (via OmniRoute) às vezes devolve UTF-8 lido como cp1252 ("EXÃ‰RCITO" na capa A do SNhb):
    desfaz a dupla codificação quando é isso; senão devolve igual."""
    # 02/11 (RRrh A "GÃŠNIO"): o "Š" (Ê maiúsculo lido em cp1252) não estava na lista -> todos os de cp1252
    if not s or not re.search(r"[ÃÂ][\x80-\xbf€‚ƒ„…†‡ˆ‰Š‹ŒŽ‘’“”•–—˜™š›œžŸ¡-¿]", s):
        return s
    for enc in ("cp1252", "latin-1"):
        try:
            return s.encode(enc).decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue
    return s


def _texto_da_original(ref):
    """01/11 dona: "as palavras que tem no original não podem faltar" — {"rotulos": [{texto, alvo}], "titulo"} da capa
    do parceiro, em português. {} se não leu."""
    try:
        r = visao_capa.perguntar(Path(ref).read_bytes(), _TEXTO_ORIGINAL, gateway=_gateway(), max_tokens=400) or {}
    except Exception:  # noqa: BLE001
        return {}
    rot = [{"texto": _sem_ambiguo(_sem_mojibake(re.sub(r"\s+", " ", str(x.get("texto") or "")).strip()).upper()),
            "alvo": str(x.get("alvo") or "")}
           for x in (r.get("rotulos") or []) if isinstance(x, dict)]
    rot = [x for x in rot if x["texto"] and len(x["texto"].split()) <= 5][:3]
    tit = _sem_ambiguo(_sem_mojibake(re.sub(r"\s+", " ", str(r.get("titulo") or "")).strip()).upper())
    return {"rotulos": rot, "titulo": tit if 0 < len(tit.split()) <= 8 else ""}


def _caixas(img, alvos):
    """Caixas (formato da visão, 0-1000) de cada alvo na imagem gerada; None onde não achou."""
    try:
        r = visao_capa.perguntar(Path(img).read_bytes(), _ACHAR + json.dumps(alvos), gateway=_gateway(),
                                 max_tokens=300) or {}
        cx = list(r.get("caixas") or [])
    except Exception:  # noqa: BLE001
        cx = []
    return (cx + [None] * len(alvos))[:len(alvos)]


def _ficha_v2(ref, cena, formato):
    """Ficha da obra pras regras de 01/11 (capa_longo_v2) — só 16:9 (longo); None = segue o jeito antigo.
    CAPA_LONGO_V2=0 desliga."""
    import os
    if formato != "16:9" or os.environ.get("CAPA_LONGO_V2", "1") == "0":
        return None
    # 11/11 (Slave Mage h1Ol-zUsJ-w): a ficha falhou 1x (visão sem cota) e o LONGO saiu com a capa antiga de Short
    # (2 homens lutando + mascote, sem as mulheres) — fora do padrão A/B/C. Tenta até CAPA_FICHA_TENTATIVAS (3) vezes.
    import time as _t
    f = None
    for tentativa in range(int(os.environ.get("CAPA_FICHA_TENTATIVAS", "3"))):
        try:
            f = capa_longo_v2.ficha(ref, cena, visao_capa.perguntar, _gateway(), CACHE)
        except Exception as e:  # noqa: BLE001
            log(f"  capa v2: ficha falhou ({type(e).__name__}: {str(e)[:80]}) — tentativa {tentativa + 1}")
            f = None
        if f:
            break
        _t.sleep(60)
    if not f:
        log("  capa v2: ficha falhou em todas as tentativas — jeito antigo")
        return None
    if f:
        log(f"  capa v2: ficha da obra {json.dumps(f, ensure_ascii=False)[:300]}")
    return f


def _original_dividida(ref):
    """A capa original é tela dividida (2 painéis)? Pergunta à visão uma vez por capa e guarda no cache."""
    f = CACHE / f"dividida_{hashlib.md5(str(ref).encode()).hexdigest()[:16]}.json"
    try:
        return json.loads(f.read_text("utf-8"))["dividida"]
    except (OSError, ValueError, KeyError):
        pass
    chk = _checar(str(ref))
    if chk is None:
        return False
    div = bool(chk.get("dividida"))
    f.write_text(json.dumps({"ref": str(ref), "dividida": div}), "utf-8")
    log(f"  capa A: original {'DIVIDIDA' if div else 'inteira'} ({Path(ref).name})")
    return div


def capa_melhorada(source_url, saida, texto="", cena="", formato="16:9"):
    """A capa do parceiro refeita e melhorada (mesmo protagonista + mulheres que combinem). Path ou None."""
    ref = _capa_do_parceiro(source_url)
    if not ref:
        return None
    original = _texto_da_original(ref) if texto else {}  # língua sem texto na capa chega com texto "" e segue sem
    if original.get("rotulos") or original.get("titulo"):
        log(f"  capa A: palavras da capa original {original}")
        texto = original.get("titulo") or ""
    prompt = REFAZER.format(fmt="vertical 9:16" if formato == "9:16" else "16:9",
                            cena=f"Story premise (Portuguese, context only - never write it): {cena}. " if cena else "",
                            vazio="Top area less busy." if formato == "9:16" else "Left third of the image less busy.",
                            mesmo=MESMO_PROTAGONISTA)
    maria = _maria(source_url)
    refs = [maria]
    v2 = _ficha_v2(ref, cena, formato)
    dividida = False
    if v2:  # 01/11 dona: regras novas (capa_longo_v2) — a Maria vai descrita no prompt com a fantasia da obra
        prompt, maria = capa_longo_v2.prompt_letra(v2, "A", source_url), None
        # 02/11 21h dona (X90): herói bebê/criança = sem mulher -> sem a pose e o corpo de referência
        refs = [] if capa_longo_v2.sem_mulheres(v2) else capa_longo_v2.refs_extras(source_url, "A")
        if refs:  # 03/11: rostos das mulheres tirados do próprio vídeo (banco_mulheres)
            b = capa_longo_v2.banco(source_url)
            prompt += capa_longo_v2.texto_banco(b, len(refs) + 2)
            refs = list(refs) + [f for f, _ in b]
        # 02/11 dona (C6YG): "quando o original é de tela dividida a versão A também deve ser; não precisa na B ou C"
        dividida = _original_dividida(ref)
        if dividida:
            prompt += (" SPLIT-SCREEN (overrides the single-scene and pose rules above): the FIRST reference is a "
                       "split-screen thumbnail, so this image keeps the SAME split layout - the same panels in the same "
                       "positions with the same divider line; each panel shows what that panel of the FIRST reference "
                       "shows (same hero, places and objects), and the women in their costume-bikinis are placed inside "
                       "the panels, the main woman big in the panel where the hero is. "
                       # 02/11 dona (LAei A): "quando é dividido e tem antes e depois, o antes tem que ser ruim"
                       "If the panels are a BEFORE / AFTER (then / now, weak / strong) comparison, the BEFORE panel "
                       "must look clearly BAD: the hero weak, poor, beaten or humiliated, sad face, ragged clothes, a "
                       "bleak place - and the AFTER panel glorious, powerful and full of happy women; the contrast "
                       "between the two panels is the whole point. "
                       # 02/11 dona (KJ5F A): "de novo faltou a parte do antes" — o 1º painel (orfanato, com
                       # crianças) sumiu e virou mais mulher. Cada painel mantém a CENA do painel da original.
                       "Keep the SAME NUMBER of panels as the FIRST reference and the SAME SCENE in each panel - never "
                       "replace a panel by more women. The FIRST (left) panel is the BEFORE: keep its place and its "
                       "sad or bad mood from the reference (poverty, orphanage, prison, rejection...); if that panel "
                       "has children in the reference, show ONLY the place and objects (building, toys, empty beds) "
                       "with NO children and NO women in bikinis there. "
                       # 11/11 dona (nd67 A com 'BEFORE / AFTER' escrito em inglês): "não faz sentido estar em
                       # inglês" — o Flow copiava as palavras do pedido. Nenhum texto nos painéis.
                       "Do NOT write any word on the image: no 'BEFORE', no 'AFTER', no labels or captions in the "
                       "panels - the contrast is shown only by the drawings.")
    tolerada = None  # 06/11 dona: sem aprovada até postar = usa a reprovada só por roupa/letras
    for _ in range(2):
        img = _gerar_com_ref(prompt, ref, formato, refs)
        if not img:
            break
        chk = _checar(img)
        if chk and dividida:  # a original é dividida: a A dividida é o certo, não defeito; a A INTEIRA é que reprova
            # (02/11 dona: C6YG e hJaA saíram inteiras — "tudo isso tem que estar documentado pra não passar no filtro")
            chk = dict(chk, dividida=False, a_nao_dividida=not chk.get("dividida"))
        if chk and chk.get("a_nao_dividida"):
            log("  capa A: original dividida e a A saiu inteira — reprovada")
            Path(img).unlink(missing_ok=True)
            continue
        if chk and capa_longo_v2.sem_mulheres(v2):  # o herói é o bebê da história: sem mulher é o certo
            chk = dict(chk, adultos=False if chk.get("ela") else True, vestidas=False)
        elif chk and not chk.get("ela"):  # 01/11 dona: capa sem mulher sensual não é o que ela pediu
            chk = dict(chk, sem_mulher=True)
        # 13/11 dona (prints: "o protagonista não se parece", "nem tem protagonista"): sem o rosto do herói na imagem
        # reprova também (antes só faltar mulher reprovava). CAPA_EXIGE_HEROI=0 desliga.
        import os as _os
        if chk and not chk.get("ele") and _os.environ.get("CAPA_EXIGE_HEROI", "1") != "0":
            log("  capa A: sem o protagonista na imagem — reprovada")
            Path(img).unlink(missing_ok=True)
            continue
        if not (chk or {}).get("sem_mulher") and not (_reprovada_v2(chk, img) if v2 else _reprovada(chk)):
            # a Maria já está na cena: sem a figurinha por cima
            rot = original.get("rotulos") or []
            extra = list(zip([x["texto"] for x in rot], _caixas(img, [x["alvo"] for x in rot]))) if rot else None
            out = _compor(img, texto, saida, QUADRO.get(formato, QUADRO["16:9"]),
                          mascote=None if (maria or v2) else source_url, rotulos_extra=extra, rostos=chk)
            Path(out).with_suffix(".capa.json").write_text(json.dumps(
                {"pose": ("v2_" + capa_longo_v2.pose_de(source_url, "A")) if v2 else "capa_do_parceiro_melhorada", "ref": str(ref), "source_url": source_url, "texto": texto,
                 "formato": formato, "checagem": chk, "prompt": prompt}, ensure_ascii=False, indent=1),
                encoding="utf-8")
            log(f"  capa IA: {Path(out).name} (capa do parceiro melhorada, texto '{texto}')")
            return out
        log(f"  capa do parceiro melhorada reprovada na checagem ({chk})")
        # 12/11 (ronda: capas dos longos caindo em sem_capa sem prova do porquê): a A reprovada também vai pra
        # reprovadas_auto com o motivo no nome, como a B/C. CAPA_GUARDA_A_REPROVADA=0 desliga.
        import os as _os
        if _os.environ.get("CAPA_GUARDA_A_REPROVADA", "1") != "0":
            try:
                import shutil as _sh
                rep = Path(saida).parent / "reprovadas_auto"
                rep.mkdir(exist_ok=True)
                motivo = "_".join(k for k in ("letras", "vestidas", "exposto", "adultos", "dividida", "escura",
                                              "sem_mulher", "a_nao_dividida") if (chk or {}).get(k) not in (None, False)
                                  and not (k == "adultos" and (chk or {}).get(k) is True)) or "sem_checagem"
                _sh.copy2(img, rep / f"A_{time.strftime('%d%m_%H%M%S')}_{motivo}.jpg")
            except Exception:  # noqa: BLE001
                pass
        if tolerada is None and _so_roupa_ou_letras(chk):
            tolerada = (img, chk)  # guarda (não apaga) pra usar se nenhuma passar
        else:
            Path(img).unlink(missing_ok=True)
        prompt += " Different composition."
    if tolerada:
        img, chk = tolerada
        out = _compor(img, texto, saida, QUADRO.get(formato, QUADRO["16:9"]), mascote=None if (maria or v2) else
                      source_url, rostos=chk)
        Path(out).with_suffix(".capa.json").write_text(json.dumps(
            {"pose": "tolerada_" + (("v2_" + capa_longo_v2.pose_de(source_url, "A")) if v2 else "parceiro"),
             "tolerada": True, "ref": str(ref), "source_url": source_url, "texto": texto, "formato": formato,
             "checagem": chk, "prompt": prompt}, ensure_ascii=False, indent=1), encoding="utf-8")
        log(f"  capa A: nenhuma passou — TOLERADA (só roupa/letras) {Path(out).name} (dona 06/11)")
        return out
    return None


# ───────── teste A/B: mais capas a partir da do parceiro (dona 30/10) ─────────
# "a capa sempre baseada na original mantendo o personagem (muitas pessoas conhecem a obra pelo personagem principal),
# adicionar mulheres sexys, mascote e sensualidade se possível; o YouTube permite colocar mais de uma capa, então
# colocar várias, sendo uma delas a mais sensual; fazer todas as poses que essas permitem". A capa A é a
# capa_melhorada; aqui saem a B (a MAIS SENSUAL, com a etiqueta do AmericanNickas) e a C (o mesmo protagonista numa
# pose do catálogo, em rodízio pelo placar). O teste do Studio aceita até 3.
# 01/11 dona: "a capa B que é a sensual deve ser como as que mandei dos canais" (Porão/Zeni/Doinsuka/NoiManhwa...,
# D:\hipercool-videos\config\capas_referencia) — o catálogo de poses dela de 15/10 (feedback_capas), não abraço comportado
POSES_SENSUAIS = {
    "pernas_pescoco": "one woman lying on the floor wraps her long legs around HIS neck in a playful headlock, smiling "
                      "smugly at the viewer, while HE panics comically",
    "de_quatro_por_cima": "one woman on all fours over HIM pinning him to the floor, her long hair falling around his "
                          "face, teasing smile; he blushes and sweats",
    "sentada_no_peito": "one woman sits on HIS chest pinning him down, leaning forward with a smug teasing smile; he "
                        "looks up terrified and blushing",
    "harem_cama": "a harem: three gorgeous women on a big bed around HIM, one hugging him from behind, one clinging to "
                  "his arm, one leaning over him; he is shocked and blushing",
    "close_rosto": "extreme close-up of ONE woman's face filling most of the frame, flushed cheeks, mouth wide open "
                   "with her tongue out teasingly, eyes half-closed; HIM smaller in the corner, shocked",
    "colo_harem": "one woman sits facing HIM on his lap with her arms around his neck while two other women cling to "
                  "his arms jealously",
}
REFAZER_SENSUAL = (
    "Recreate the attached YouTube thumbnail as a brand-new {fmt} anime thumbnail, MUCH MORE SEDUCTIVE. Keep the SAME "
    "main character(s) from it - same face, hair, eyes and outfit - so fans instantly recognize the story. Scene: {pose}. "
    "The women are gorgeous voluptuous grown-up ADULT anime women in their late twenties, blushing, wearing ONLY lace "
    "lingerie, a bikini, a short silk nightgown or a babydoll (in a fantasy or historical story: a jeweled bikini-armor "
    "or a sheer short slip in that style) - never regular clothes, dresses or gowns - that still covers everything "
    "private: no nudity, no sexual act. Bright, sunny, clean manhwa-recap thumbnail style like 'O Porao da Cidadela': "
    "one single continuous scene (never panels), soft glossy lighting, vibrant saturated colors, never dark. "
    "{cena}Remove ALL text, letters, logos, channel marks and watermarks. Faces in the upper half of the frame; the "
    "lower-middle part will hold one big word. {mesmo}")
REFAZER_POSE = (
    "Recreate the attached YouTube thumbnail as a brand-new {fmt} anime thumbnail with a NEW composition. Keep the SAME "
    "main character from it - same face, hair, eyes, outfit and weapon - so fans instantly recognize the story. New "
    "scene: {pose}. Add one gorgeous, attractive ADULT anime woman that fits this story's world close to him, alluring "
    "but fully clothed. {regras} {cena}Remove ALL text, letters, logos, channel marks and watermarks. {vazio} {mesmo}")


def _rodizio(chave, opcoes):
    """Pose em rodízio pelo placar de capas (Thompson, como _poses); sem placar, pelo hash do vídeo — assim, vídeo após
    vídeo, todas as poses são testadas."""
    try:
        import placar_titulos
        pl = {}
        for g in ("anime", "recapd", "parceiro"):
            for k, (t, v) in placar_titulos.taxas("capas", g).items():
                a = pl.get(k, (0, 0))
                pl[k] = (a[0] + t, a[1] + v)
        if any(k in pl for k in opcoes):
            return max(opcoes, key=lambda p: random.betavariate(pl.get(p, (0, 0))[1] + 1,
                                                                 pl.get(p, (0, 0))[0] - pl.get(p, (0, 0))[1] + 1))
    except Exception:  # noqa: BLE001
        pass
    return opcoes[int(hashlib.md5(chave.encode()).hexdigest(), 16) % len(opcoes)]


# L-F4 (LONGOS_MELHORIAS.md): capas A/B/C do longo de parceiro + teste A/B no Studio
def capas_ab(source_url, saida, texto="", cena="", generos=None, formato="16:9", orcamento_s=2400):
    """Capas B (a mais sensual, etiqueta) e C (pose do catálogo) ao lado de `saida` (capa_b.jpg, capa_c.jpg), as duas
    com o protagonista da capa do parceiro e a mascote. Devolve a lista das que saíram (0 a 2). Nunca levanta erro:
    o teste A/B é extra, a capa A já basta pra postar."""
    import os
    import time as _t
    if os.environ.get("CAPA_AB", "1") == "0":
        return []
    ref = _capa_do_parceiro(source_url)
    if not ref:
        return []
    fmt = "vertical 9:16" if formato == "9:16" else "16:9"
    ctx = f"Story premise (Portuguese, context only - never write it): {cena}. " if cena else ""
    vazio = "Top area less busy." if formato == "9:16" else "Left third of the image less busy."
    gens = generos or _generos_do_texto(cena, texto) or ["acao", "fantasia"]
    p_sens = _rodizio(source_url + "|s", list(POSES_SENSUAIS))
    p_pose = _rodizio(source_url + "|p", [p for p in _poses(gens) if p in POSES][:6] or list(POSES))
    # sem texto na capa (línguas de _SEM_TEXTO_CAPA chegam com texto ""): B e C também saem sem palavra
    fala = FALAS_DELA[int(hashlib.md5(source_url.encode()).hexdigest(), 16) % len(FALAS_DELA)] if texto else ""
    variantes = [
        ("b", "sensual_" + p_sens, REFAZER_SENSUAL.format(fmt=fmt, pose=POSES_SENSUAIS[p_sens], cena=ctx,
                                                                   mesmo=MESMO_PROTAGONISTA), "etiqueta",
         _etiqueta(texto, cena) if texto else "", ""),
        ("c", "parceiro_pose_" + p_pose, REFAZER_POSE.format(
            fmt=fmt, pose=POSES[p_pose][1], cena=ctx, vazio=vazio, mesmo=MESMO_PROTAGONISTA,
            regras=REGRAS_BATALHA if p_pose in BATALHA else REGRAS_GERAIS), "rotulos",
         _papel(texto, cena) if texto else "", fala),
    ]
    v2 = _ficha_v2(ref, cena, formato)
    if v2:  # 01/11 dona: B = a mais sensual (cômica), C = batalha + humilhação, nas regras novas (capa_longo_v2)
        variantes = [(l, "v2_" + capa_longo_v2.nome_pose(source_url, l.upper()),
                      capa_longo_v2.prompt_letra(v2, l.upper(), source_url), e, t, f)
                     for (l, _p, _pr, e, t, f) in variantes]
    t0, feitas = _t.time(), []
    base = Path(saida)
    for letra, pose, prompt, estilo, txt, fala in variantes:
        if _t.time() - t0 > orcamento_s:
            log(f"  capas A/B: passou de {orcamento_s // 60} min — fica sem a capa {letra.upper()}")
            break
        out = base.with_name(f"{base.stem}_{letra}.jpg")
        try:
            maria = None if v2 else _maria(f"{source_url}|{letra}")
            so_heroi = bool(v2) and capa_longo_v2.sem_mulheres(v2)
            refs = ([] if so_heroi else capa_longo_v2.refs_extras(source_url, letra.upper())) if v2 else [maria]
            if v2 and refs:  # 03/11: rostos das mulheres tirados do próprio vídeo (banco_mulheres)
                b = capa_longo_v2.banco(source_url)
                prompt += capa_longo_v2.texto_banco(b, len(refs) + 2)
                refs = list(refs) + [f for f, _ in b]
            if maria:  # 01/11 dona: a Maria entra como uma das mulheres, colorido e nunca escuro
                prompt += (" One of the women is MARIA from the SECOND reference image (same face, long wavy "
                           "dark-brown hair, golden-brown eyes, tanned curvy adult body) in a revealing outfit. "
                           "Bright, sunny, vivid saturated colors - never dark or gloomy.")
            tolerada = None  # 06/11 dona: nenhuma passou = posta a reprovada só por roupa/letras
            for _ in range(2):
                img = _gerar_com_ref(prompt, ref, formato, refs)
                if not img:
                    log(f"  capa {letra.upper()}: Flow não gerou (sem máquinas ou timeout) — pula esta capa")
                    continue
                chk = _checar(img)
                if chk and so_heroi:  # herói bebê: a criança é ele; mulher na imagem reprova
                    chk = dict(chk, adultos=False if chk.get("ela") else True, vestidas=False)
                if not ((_reprovada(chk) if so_heroi else _reprovada_v2(chk, img)) if v2 else _reprovada(chk)):
                    _compor(img, txt, out, QUADRO.get(formato, QUADRO["16:9"]), estilo=estilo,
                            mascote=None if (maria or v2) else f"{source_url}|{letra}", rostos=chk, fala=fala)
                    out.with_suffix(".capa.json").write_text(json.dumps(
                        {"pose": pose, "variante_ab": letra, "estilo_texto": estilo, "texto": txt, "fala": fala,
                         "ref": str(ref),
                         "source_url": source_url, "formato": formato, "checagem": chk, "prompt": prompt},
                        ensure_ascii=False, indent=1), encoding="utf-8")
                    log(f"  capa {letra.upper()} do teste A/B: {out.name} ({pose}, texto '{txt}')")
                    feitas.append(out)
                    break
                log(f"  capa {letra.upper()} reprovada na checagem ({chk})")
                # 04/11: a B nunca passa (letras=True em todas). Guarda as reprovadas pra ver o motivo
                try:
                    import shutil
                    rep = base.parent / "reprovadas_auto"
                    rep.mkdir(exist_ok=True)
                    motivo = "_".join(k for k in ("letras", "vestidas", "exposto", "adultos", "dividida", "escura")
                                      if (chk or {}).get(k) is (k != "adultos")) or "outro"
                    destino = rep / f"{letra.upper()}_{time.strftime('%d%m_%H%M%S')}_{motivo}.jpg"
                    shutil.move(img, destino)
                    if tolerada is None and _so_roupa_ou_letras(chk):
                        tolerada = (destino, chk)
                except Exception:  # noqa: BLE001
                    Path(img).unlink(missing_ok=True)
                prompt += " Different composition."
            if tolerada and out not in feitas:
                img, chk = tolerada
                _compor(img, txt, out, QUADRO.get(formato, QUADRO["16:9"]), estilo=estilo,
                        mascote=None if (maria or v2) else f"{source_url}|{letra}", rostos=chk, fala=fala)
                out.with_suffix(".capa.json").write_text(json.dumps(
                    {"pose": "tolerada_" + pose, "tolerada": True, "variante_ab": letra, "estilo_texto": estilo,
                     "texto": txt, "fala": fala, "ref": str(ref), "source_url": source_url, "formato": formato,
                     "checagem": chk, "prompt": prompt}, ensure_ascii=False, indent=1), encoding="utf-8")
                log(f"  capa {letra.upper()}: nenhuma passou — TOLERADA (só roupa/letras) {out.name} (dona 06/11)")
                feitas.append(out)
        except Exception as e:  # noqa: BLE001
            log(f"  capa {letra.upper()} falhou ({type(e).__name__}: {str(e)[:100]})")
    return feitas


def gerar_capa(anime, capitulo, saida, texto="", cena="", protagonista="", generos=None, formato="16:9",
               source_url=""):
    """Capa pronta (Path do .jpg) ou None. Grava <saida>.capa.json com pose/texto/checagem (pra medir depois).
    source_url (29/10): primeiro tenta melhorar a capa do parceiro; falhou = pose do catálogo como antes."""
    if source_url:
        try:
            out = capa_melhorada(source_url, saida, texto, cena, formato)
            if out:
                return out
        except Exception as e:  # noqa: BLE001 — nunca trava a postagem
            log(f"  capa do parceiro falhou ({type(e).__name__}: {str(e)[:100]}) — pose do catálogo")
        # 11/11 (Slave Mage h1Ol e Little Orc gUsq): no LONGO (16:9 com capa do parceiro) a "pose do catálogo" é a capa
        # antiga de SHORT (2 homens/orc + mascote, sem as mulheres) — fora do padrão A/B/C da dona. Sem capa melhorada,
        # devolve None: o capas_depois tenta de novo na próxima rodada (o vídeo segue com a capa que já tem).
        # CAPA_LONGO_SEM_CATALOGO=0 volta ao antigo.
        import os
        if formato == "16:9" and os.environ.get("CAPA_LONGO_SEM_CATALOGO", "1") != "0":
            log("  capa do longo: capa melhorada não saiu — NÃO uso a pose do catálogo (Short); tenta de novo depois")
            return None
    cfg = _cfg_anime(anime) or {}
    prot = cfg.get("protagonista") or protagonista or "adult anime hero in his twenties with a determined expression"
    feminino = cfg.get("genero") == "F" or (not cfg and bool(re.search(r"\b(woman|girl|female|she)\b", prot, re.I)))
    generos = cfg.get("generos") or generos or _generos_do_texto(cena, texto, anime) or ["acao", "fantasia"]
    quadro = QUADRO.get(formato, QUADRO["16:9"])
    for pose in _poses(generos)[:3]:
        luta = pose in BATALHA
        roupa = "" if (cfg or protagonista or not luta) else f", wearing {random.choice(ROUPAS_BATALHA)}"
        prompt = (f"{_pronomes(POSES[pose][1], feminino)}. Main character design: {prot}{roupa}. "
                  + (f"Story premise (Portuguese, context only - never write it): {cena}. " if cena else "")
                  + (f"{REGRAS_BATALHA} Anime art style, dynamic action composition, " if luta else
                     f"{REGRAS_GERAIS} Anime art style, expressive emotional composition, ")
                  + f"cinematic lighting, vibrant "
                  f"colors, eye-catching {'vertical 9:16' if formato == '9:16' else '16:9'} YouTube thumbnail, "
                  "characters large in frame, "
                  + ("top area less busy." if formato == "9:16" else "left third of the image less busy."))
        chk = None
        for _ in range(2):  # dono 20/10: capa com defeito é refeita, não aceita
            img = _gerar(prompt, formato)
            if not img:
                break  # gateway fora e o filtro da reserva recusou esta pose: outra pode passar
            chk = _checar(img)
            if not _reprovada(chk):
                break
            log(f"  capa IA: pose {pose} reprovada na checagem ({chk})")
            Path(img).unlink(missing_ok=True)  # sai do cache: senão a mesma imagem ruim volta
            img = None
        if not img:
            continue
        out = _compor(img, texto, saida, quadro, mascote=f"{anime}|{capitulo}")
        Path(out).with_suffix(".capa.json").write_text(json.dumps(
            {"anime": anime, "capitulo": capitulo, "pose": pose, "texto": texto, "formato": formato,
             "protagonista": prot, "checagem": chk, "prompt": prompt}, ensure_ascii=False, indent=1),
            encoding="utf-8")
        log(f"  capa IA: {out.name} (pose {pose}, texto '{texto}')")
        return out
    log("  capa IA: todas as tentativas reprovadas — sem capa")
    return None


def registrar_vencedora_ab(pasta, vencedora, video_id=""):
    """Registra a variante vencedora do teste A/B no placar compartilhado de capas e variantes.
    pasta: pasta do vídeo longo ou caminho para postar.json
    vencedora: 'a', 'b', 'c' ou índice 0, 1, 2
    """
    p = Path(pasta)
    if p.is_file():
        p = p.parent
    if isinstance(vencedora, int):
        vencedora = ["a", "b", "c"][vencedora] if 0 <= vencedora < 3 else "a"
    vencedora = str(vencedora).lower().strip()

    variantes = [
        ("a", p / "capa.capa.json"),
        ("b", p / "capa_b.capa.json"),
        ("c", p / "capa_c.capa.json"),
    ]

    try:
        import placar_titulos
    except ImportError:
        sys.path.insert(0, r"D:\postador-de-videos\bin")
        import placar_titulos

    registrados = []
    for letra, cj in variantes:
        if not cj.exists():
            continue
        try:
            d = json.loads(cj.read_text("utf-8"))
            pose = d.get("pose")
        except Exception:
            pose = None
        ganhou = (letra == vencedora)
        # chave própria do resultado do Studio: o medidor de 48 h já usa <vid>_<letra> e o placar recusa chave repetida
        vid_ref = f"{video_id}_ab_{letra}" if video_id else ""
        if pose:
            placar_titulos.registrar_item("capas", "parceiro", pose, ganhou, vid_ref)
            registrados.append((letra, pose, ganhou))
        # placar próprio: "capas_variante" é o do TRATAMENTO da capa (anime_publish._tratar_capa), outra coisa
        placar_titulos.registrar_item("capas_ab", "parceiro", letra.upper(), ganhou, vid_ref)

    try:
        (p / "vencedora_ab.json").write_text(json.dumps({
            "vencedora": vencedora,
            "registrados": registrados,
            "video_id": video_id
        }, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass
    log(f"  teste A/B registrado: vencedora '{vencedora}' em {p.name} ({registrados})")
    return registrados


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Capa IA do recap de anime")
    ap.add_argument("--anime", required=True)
    ap.add_argument("--cap", type=int, default=1)
    ap.add_argument("--saida", required=True)
    ap.add_argument("--texto", default="")
    ap.add_argument("--cena", default="")
    ap.add_argument("--protagonista", default="")
    ap.add_argument("--formato", default="16:9", choices=list(QUADRO))
    ap.add_argument("--source-url", default="", help="vídeo do parceiro: a capa dele melhorada")
    ap.add_argument("--ab", action="store_true", help="também as capas B (sensual) e C (pose) do teste A/B")
    ap.add_argument("--so-compor", help="(teste) imagem pronta: só aplica texto/etiqueta/mascote em --saida")
    ap.add_argument("--estilo", default="frase", choices=("frase", "etiqueta", "rotulos"))
    ap.add_argument("--checar", action="store_true", help="(teste) com --so-compor: pede os rostos à visão")
    a = ap.parse_args()
    if a.so_compor:
        txt = {"etiqueta": _etiqueta, "rotulos": _papel}.get(a.estilo, lambda t, c: t)(a.texto, a.cena)
        chk = _checar(a.so_compor) if a.checar else None
        print(chk)
        print(_compor(a.so_compor, txt, a.saida, QUADRO[a.formato], estilo=a.estilo, mascote=a.so_compor,
                      rostos=chk, fala=FALAS_DELA[0] if a.estilo == "rotulos" else ""))
        return
    ok = gerar_capa(a.anime, a.cap, a.saida, a.texto, a.cena, a.protagonista, formato=a.formato,
                    source_url=a.source_url)
    if ok and a.ab and a.source_url:
        print(capas_ab(a.source_url, a.saida, a.texto, a.cena, formato=a.formato))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
