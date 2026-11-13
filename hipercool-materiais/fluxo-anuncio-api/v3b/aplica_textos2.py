"""Segunda leva de ajustes nos textos da V3b: selo inclinado, cartão final maior e em caixa alta."""
from pathlib import Path

p = Path(__file__).parent / "monta_ffmpeg.js"
t = p.read_text(encoding="utf-8")


def troca(a, b):
    global t
    assert t.count(a) == 1, (t.count(a), a[:80])
    t = t.replace(a, b)


B = "\\\\"   # barra invertida dupla, como está no JS dentro da crase
troca("Preco,,0,0,0,,${pos(W / 2, H * (vertical ? 0.55 : 0.5))}${limpa(v.dados.preco)}`",
      "Preco,,0,0,0,,${pos(W / 2, H * (vertical ? 0.47 : 0.45))}{" + B + "frz4}${limpa(v.dados.preco)}`")
troca("Marca,,0,0,0,,${pos(W / 2, H * 0.28)}${limpa(v.dados.marca || v.dados.titulo)}`",
      "Marca,,0,0,0,,${pos(W / 2, H * 0.24)}{" + B + "fs${fs(vertical ? 92 : 70)}}${limpa(v.dados.marca || v.dados.titulo).toUpperCase()}`")
troca("Preco,,0,0,0,,${pos(W / 2, H * 0.42)}{" + B + "fs${fs(vertical ? 58 : 48)}}${limpa(ed.cta)}`",
      "Preco,,0,0,0,,${pos(W / 2, H * 0.4)}{" + B + "fs${fs(vertical ? 66 : 54)}}${limpa(ed.cta)}`")
troca("Marca,,0,0,0,,${pos(W / 2, H * 0.55)}${limpa(v.dados.preco)}`",
      "Marca,,0,0,0,,${pos(W / 2, H * 0.55)}{" + B + "fs${fs(vertical ? 84 : 64)}" + B + "c${ass(destaqueLeg)}}${limpa(v.dados.preco)}`")
troca("Contato,,0,0,0,,${pos(W / 2, H * (0.66 + j * 0.065))}${limpa(c)}`",
      "Contato,,0,0,0,,${pos(W / 2, H * (0.68 + j * 0.075))}${limpa(c)}`")
p.write_text(t, encoding="utf-8")
print("ok")
