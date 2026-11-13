# Textos das capas do G1_iPga6nLg + borrão em brilho branco no bumbum da B (molde Porão/hipercool, dona 01/11).
# Rótulos/falas com seta até o rosto: os rostos e o bumbum vêm da visão (capa_ia_anime._caixas, 0-1000).
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, r"D:\hipercool-materiais\capas_exemplo_01nov")
from compor_real import H, W, abrir, c, palavra, salvar  # noqa: E402

AQUI = Path(__file__).parent
BR = AQUI / "brutas"
BRANCO = (255, 255, 255)


def larg(d, txt, tam):
    return d.textlength(txt, font=c._fonte("LuckiestGuy-Regular.ttf", tam))


def caixas(img, alvos):
    cx = c._caixas(img, alvos)
    print(Path(img).name, json.dumps(dict(zip(alvos, cx)), ensure_ascii=False))
    return [None if not b else (b[1] * W / 1000, b[0] * H / 1000, b[3] * W / 1000, b[2] * H / 1000) for b in cx]


def meio(b, dy=0.5):
    return (int((b[0] + b[2]) / 2), int(b[1] + (b[3] - b[1]) * dy))


def bloco(d, linhas, x, y, tam, alinhar="esq", cor=c.AMARELO):
    """Linhas empilhadas; devolve a caixa (x0, y0, x1, y1) do bloco."""
    larg_max = max(larg(d, t, tam) for t in linhas)
    x0 = x if alinhar == "esq" else x - larg_max
    for i, t in enumerate(linhas):
        dx = 0 if alinhar == "esq" else larg_max - larg(d, t, tam)
        palavra(d, t, x0 + dx, y + i * int(tam * 1.0), tam, cor)
    return (x0, y, x0 + larg_max, y + len(linhas) * tam)


def seta_ate(d, de_bloco, alvo, esp=26, contorno=6):
    """Seta saindo do ponto da borda do bloco mais próximo do alvo (nunca cruza o texto)."""
    x0, y0, x1, y1 = de_bloco
    ini = (min(max(alvo[0], x0 - 8), x1 + 8), min(max(alvo[1], y0 - 8), y1 + 8))
    if ini == tuple(alvo):  # alvo embaixo do texto: sai de baixo, pelo meio
        ini = ((x0 + x1) // 2, y1 + 8)
    fim = (int(ini[0] + (alvo[0] - ini[0]) * 0.8), int(ini[1] + (alvo[1] - ini[1]) * 0.8))
    c._seta(d, ini, fim, esp, contorno)


def brilho(capa, b):
    """Censura estilo Porão: mancha branca difusa sobre a parte (borrão + véu branco com borda suave)."""
    x0, y0, x1, y1 = b
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    rx, ry = (x1 - x0) * 0.5, (y1 - y0) * 0.5
    mask = Image.new("L", capa.size, 0)
    ImageDraw.Draw(mask).ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(max(rx, ry) * 0.3))
    borrado = capa.filter(ImageFilter.GaussianBlur(28))
    capa.paste(borrado, (0, 0), mask)
    capa.paste(Image.new("RGB", capa.size, BRANCO), (0, 0), mask.point(lambda v: min(255, int(v * 1.15))))


def capa_a(out):
    bruta = BR / "parceiro_G1_iPga6nLg_A.png"
    capa = abrir(bruta)
    d = ImageDraw.Draw(capa)
    roxa, marg, ele = caixas(bruta, ["face of the purple-haired woman", "face of the orange or blonde haired woman",
                                     "face of the black-haired man"])
    bloco(d, ["VAMOS LEVÁ-LO", "PRA CASA?"], 24, 18, 58)  # colada nela: dispensa seta
    b = bloco(d, ["É CLARO!!!"], W - 24, 18, 80, "dir")
    if marg:
        seta_ate(d, b, meio(marg, 0.7))
    b = bloco(d, ["PRISIONEIRO"], 24, H - 105, 84)
    if ele:
        seta_ate(d, b, meio(ele, 1.1), 32, 7)
    return salvar(capa, out)


def capa_b(out):
    bruta = BR / "parceiro_G1_iPga6nLg_B.png"
    capa = abrir(bruta)
    marg, ele, bumbum = caixas(bruta, ["face of the woman on all fours (orange hair)", "face of the black-haired man",
                                       "the buttocks of the woman on all fours (her round butt on the left)"])
    if bumbum:
        brilho(capa, bumbum)
    d = ImageDraw.Draw(capa)
    bloco(d, ["AGORA VOCÊ", "É NOSSO!"], 24, 18, 58)  # fala da cavaleira roxa, colada nela
    b = bloco(d, ["SOCORRO!!!"], W - 24, 18, 80, "dir", BRANCO)
    if ele:
        seta_ate(d, b, meio(ele, 0.5))
    b = bloco(d, ["PRISIONEIRO", "DELAS"], W - 24, H - 160, 72, "dir")
    if ele:
        seta_ate(d, b, meio(ele, 0.6))
    return salvar(capa, out)


def capa_c(out):
    bruta = BR / "parceiro_G1_iPga6nLg_C.png"
    capa = abrir(bruta)
    d = ImageDraw.Draw(capa)
    marg, ele = caixas(bruta, ["face of the kneeling orange-haired knight woman", "face of the black-haired man"])
    b = bloco(d, ["COMO?!"], 24, 18, 90, cor=BRANCO)
    if marg:
        seta_ate(d, b, meio(marg, 0.4))
    b = bloco(d, ["LVL 999"], 400, 14, 96)  # céu livre entre a cavaleira e ele
    if ele:
        seta_ate(d, b, meio(ele, 0.5), 30, 7)
    bloco(d, ["DE PRISIONEIRO", "A MONSTRO"], 24, H - 160, 70)
    return salvar(capa, out)


if __name__ == "__main__":
    for q in sys.argv[1:] or "abc":
        print({"a": capa_a, "b": capa_b, "c": capa_c}[q](AQUI / f"capa_{q.upper()}.jpg"))
