# Textos das capas v2 do SNhb31ZuuFA (regras da dona 01/11 em CAPAS_REFERENCIA.md):
# A = palavras da original (INIMIGO / EXÉRCITO DO PROTA / #COMPLETO) + "BRUXAS"; B = frase provocativa;
# C = batalha com níveis (LVL 1 no inimigo x LVL 999 nele) + falas.
import sys
from pathlib import Path

from PIL import ImageDraw

from compor_real import BASE, W, abrir, c, palavra, salvar

BR = BASE / "brutas"
BRANCO, VERMELHO = (255, 255, 255), (255, 60, 40)


def larg(d, txt, tam):
    return d.textlength(txt, font=c._fonte("LuckiestGuy-Regular.ttf", tam))


def capa_a(out):
    capa = abrir(BR / "parceiro_SNhb31ZuuFA_v2_A.png")
    d = ImageDraw.Draw(capa)
    palavra(d, "INIMIGO", 30, 600, 96)
    c._seta(d, (190, 595), (190, 520), 30, 7)
    for txt, y in (("EXÉRCITO", 560), ("DO PROTA", 630)):
        palavra(d, txt, W - 22 - larg(d, txt, 64), y, 64)
    c._seta(d, (1180, 555), (1180, 470), 24, 6)
    palavra(d, "#COMPLETO", 30, 24, 60, BRANCO)
    palavra(d, "BRUXAS", 30, 300, 80)
    c._seta(d, (285, 345), (345, 345), 24, 6)
    return salvar(capa, out)


def capa_b(out):
    capa = abrir(BR / "parceiro_SNhb31ZuuFA_v2_B.png")
    d = ImageDraw.Draw(capa)
    palavra(d, "ELAS QUEREM", 24, 520, 92)
    palavra(d, "SERVIR ELE!", 24, 615, 92)
    return salvar(capa, out)


def capa_c(out):
    capa = abrir(BR / "parceiro_SNhb31ZuuFA_v2_C.png")
    d = ImageDraw.Draw(capa)
    palavra(d, "LVL 1", 300, 560, 90, VERMELHO)
    c._seta(d, (330, 565), (290, 500), 26, 6)
    palavra(d, "COMO?!", 30, 180, 80, BRANCO)
    palavra(d, "LVL 999", W - 22 - larg(d, "LVL 999", 90), 8, 90)
    c._seta(d, (1060, 95), (1015, 150), 30, 7)
    palavra(d, "FÁCIL...", 640, 640, 64, BRANCO)
    return salvar(capa, out)


if __name__ == "__main__":
    for q in sys.argv[1:] or "abc":
        print({"a": capa_a, "b": capa_b, "c": capa_c}[q](BASE / f"v2_capa_{q.upper()}.jpg"))
