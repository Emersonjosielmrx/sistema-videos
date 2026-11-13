# Capas do the-greatest-estate-developer_cap1_20261101 (dona 01/11): A = original melhorada COM as palavras da
# original (ENEMY / MC ARMY / #COMPLETED em português, setas amarelas); B = sensual com UMA palavra colada com
# meia-lua até o rosto dela (AmericanNickas). Sem a mascote antiga.
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, r"D:\recapd-ambientes\producao\bin")
import capa_ia_anime as c  # noqa: E402

BASE = Path(r"D:\hipercool-materiais\capas_exemplo_01nov")
W, H = 1280, 720


def abrir(p):
    img = Image.open(p).convert("RGB")
    sc = max(W / img.width, H / img.height)
    img = img.resize((int(img.width * sc) + 1, int(img.height * sc) + 1), Image.LANCZOS)
    ox, oy = (img.width - W) // 2, (img.height - H) // 2
    return img.crop((ox, oy, ox + W, oy + H))


def palavra(d, txt, x, y, tam, cor=c.AMARELO):
    f = c._fonte("LuckiestGuy-Regular.ttf", tam)
    d.text((x, y), txt, font=f, fill=cor, stroke_width=max(6, tam // 9), stroke_fill=c.PRETO)
    return d.textlength(txt, font=f)


def salvar(capa, out):
    for q in (92, 85, 75):
        capa.save(out, "JPEG", quality=q)
        if Path(out).stat().st_size < 1_900_000:
            return out


def capa_a(bruta, out):
    capa = abrir(bruta)
    d = ImageDraw.Draw(capa)
    # INIMIGO embaixo à esquerda, seta pro galeão
    palavra(d, "INIMIGO", 40, 600, 96)
    c._seta(d, (215, 595), (215, 520), 30, 7)
    # EXÉRCITO DO PROTA embaixo à direita, seta pro encouraçado
    f = c._fonte("LuckiestGuy-Regular.ttf", 64)
    for txt, y in (("EXÉRCITO", 560), ("DO PROTA", 630)):
        palavra(d, txt, W - 22 - d.textlength(txt, font=f), y, 64)
    c._seta(d, (1150, 555), (1150, 500), 24, 6)
    palavra(d, "#COMPLETO", 40, 30, 60, (255, 255, 255))
    return salvar(capa, out)


def capa_b(bruta, out, txt="OBCECADA"):
    chk = c._checar(bruta)
    print("checagem B:", chk)
    return c._compor(bruta, txt, out, (W, H), estilo="etiqueta", mascote=None, rostos=chk)


if __name__ == "__main__":
    qual = sys.argv[1]
    if qual == "a":
        print(capa_a(BASE / "brutas" / "pjOoN03xa0k_a.png", BASE / "real_capa_A.jpg"))
    else:
        print(capa_b(BASE / "brutas" / f"parceiro_SNhb31ZuuFA_{qual}.png", BASE / f"real_capa_B_{qual}.jpg",
                     {"harem": "HARÉM", "obcecada": "OBCECADAS"}[qual]))
