"""Aplica o estilo novo de textos no monta_ffmpeg.js da V3b (copiado da V3, que fica intacta)."""
import re
from pathlib import Path

p = Path(__file__).parent / "monta_ffmpeg.js"
t = p.read_text(encoding="utf-8")


def troca(a, b):
    global t
    assert t.count(a) == 1, (t.count(a), a[:80])
    t = t.replace(a, b)


troca("input.in_textos = v.arquivo + 'textos-' + v.job + '.ass';",
      "input.in_textos = v.arquivo + 'textos-' + v.job + '.ass';\n"
      "// fonte Montserrat 900 (o servidor do ffmpeg só tem DejaVu): vai como arquivo e o filtro ass lê a pasta inputs/\n"
      "input.in_fonte = 'https://fonts.gstatic.com/s/montserrat/v31/JTUHjIg1_i6t8kCHKm4532VJOt5-QNFgpCvC70w-.ttf';")
troca("ass={{in_textos}},split=2[vid][vidc]", "ass={{in_textos}}:fontsdir=inputs,split=2[vid][vidc]")
troca("ass={{in_textos_m}}[vidm]", "ass={{in_textos_m}}:fontsdir=inputs[vidm]")
troca(".filter(k2 => !/^in_textos/.test(k2))", ".filter(k2 => !/^in_textos|^in_fonte/.test(k2))")
troca("const ext = k2 => /^in_textos/.test(k2) ? '.ass' :", "const ext = k2 => /^in_fonte/.test(k2) ? '.ttf' : /^in_textos/.test(k2) ? '.ass' :")

# estilos: uma linha "Style: Nome,..." por vez (troca do nome até o fim da linha)
ESTILOS = {
    "Manchete": "Montserrat Black,${fs(vertical ? 62 : 52)},${ass(corTexto)},${ass(corTexto)},${ass(cor)},&H80000000&,-1,0,0,0,100,100,1,0,3,${fs(22)},${fs(4)},8,40,40,${Math.round(H * 0.07)},1",
    "Preco": "Montserrat Black,${fs(vertical ? 92 : 72)},${ass(corTexto)},${ass(corTexto)},${ass(cor)},&H80000000&,-1,0,0,0,100,100,0,4,3,${fs(24)},${fs(5)},5,40,40,0,1",
    "Legenda": "Montserrat Black,${fs(vertical ? 80 : 60)},&H00FFFFFF&,&H00FFFFFF&,&H00000000&,&H96000000&,-1,0,0,0,100,100,0,0,1,${fs(6)},${fs(3)},2,${fs(60)},${fs(60)},${Math.round(H * (vertical ? 0.16 : 0.08))},1",
    "Marca": "Montserrat Black,${fs(vertical ? 76 : 60)},&H00FFFFFF&,&H00FFFFFF&,&H00000000&,&H96000000&,-1,0,0,0,100,100,2,0,1,${fs(5)},${fs(3)},5,40,40,0,1",
    "Contato": "Montserrat Black,${fs(vertical ? 50 : 40)},&H00FFFFFF&,&H00FFFFFF&,&H00000000&,&H96000000&,-1,0,0,0,100,100,0,0,1,${fs(4)},${fs(2)},5,40,40,0,1",
}
linhas = t.split("\n")
for nome, estilo in ESTILOS.items():
    achou = [i for i, l in enumerate(linhas) if ("`Style: " + nome + ",DejaVu Sans,") in l]
    assert len(achou) == 1, (nome, len(achou))
    l = linhas[achou[0]]
    ini = l.index("`Style: ") + 1
    fim = l.index("\\n", ini)          # o "\n" literal do JS (barra + n)
    linhas[achou[0]] = l[:ini] + "Style: " + nome + "," + estilo + l[fim:]
t = "\n".join(linhas)
# a fonte DejaVu ainda aparece? (não deve)
assert ",DejaVu Sans," not in t

# manchete em caixa alta e legenda com a palavra falada destacada
troca("Manchete,,0,0,0,,{\\\\fad(250,0)}${limpa(s.texto_tela)}`", "Manchete,,0,0,0,,{\\\\fad(250,0)}${limpa(s.texto_tela).toUpperCase()}`")
troca("grupos.forEach(g => { const d = fala * g.length / letras; ev.push(`Dialogue: 1,${t2(t)},${t2(t + d)},Legenda,,0,0,0,,${g}`); t += d; });",
      "// cada grupo aparece com a palavra da vez na cor de destaque (estilo karaokê), no ritmo proporcional ao tamanho\n"
      "      grupos.forEach(g => {\n"
      "        const d = fala * g.length / letras, pw = g.split(' '), tot = pw.reduce((x, w) => x + w.length + 1, 0);\n"
      "        let tw = t;\n"
      "        pw.forEach((w, j) => {\n"
      "          const dw = d * (w.length + 1) / tot;\n"
      "          const txt = pw.map((x, q) => q === j ? `{\\\\c${ass(destaqueLeg)}}${x}{\\\\c&HFFFFFF&}` : x).join(' ').toUpperCase();\n"
      "          ev.push(`Dialogue: 1,${t2(tw)},${t2(tw + dw)},Legenda,,0,0,0,,${txt}`);\n"
      "          tw += dw;\n"
      "        });\n"
      "        t += d;\n"
      "      });")
troca("const corTexto = clara(cor) ? '#111111' : '#FFFFFF';",
      "const corTexto = clara(cor) ? '#111111' : '#FFFFFF';\nconst destaqueLeg = clara(cor) ? cor : '#FFD400';   // a palavra falada precisa aparecer sobre a foto")
p.write_text(t, encoding="utf-8")
print("ok")
