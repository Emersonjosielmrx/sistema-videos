# -*- coding: utf-8 -*-
# PC1. Liga a escolha pelos MELHORES momentos (26/11). Uso: python otimo_patch.py <arquivo memes_visuais.py>
import shutil, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
alvo = Path(sys.argv[1])
NOVO = r'''

# 26/11 (dona: "memes nos momentos-chave, para o máximo de efeito"): antes, o 1º momento que casava depois do intervalo
# levava o meme — um momento fraco bloqueava o melhor logo depois (813 frases: frase 10, nota 9, bloqueou a 15, nota
# 16,5) e gastava o meme (o "bichão" usado na nota 6 não pôde ir na "venceu sem nenhuma dificuldade", nota 16,5);
# a 2ª metade do vídeo ficava sem meme. Agora: nota de todo par (frase, meme) do vídeo inteiro, e os momentos são
# escolhidos do MAIOR para o menor, respeitando o intervalo. O mesmo meme pode voltar uma vez se estiver a
# MEMES_REPETE_LONGE frases (~15 min) e o momento for forte (nota >= MEMES_REPETE_NOTA). MEMES_MOMENTO_OTIMO=0 volta.
def _escolher_otimo(textos, inicio, cada, rnd):
    try:
        longe = int(os.environ.get("MEMES_REPETE_LONGE", "300"))
        nota_rep = float(os.environ.get("MEMES_REPETE_NOTA", "9"))
    except ValueError:
        longe, nota_rep = 300, 9.0
    cand = [m for m in catalogo() if m.get("has_audio") and Path(m["file"]).suffix.lower() == ".mp4"
            and INTERROMPE_DUR[0] <= float(m.get("duration") or 0) <= INTERROMPE_DUR[1]]
    pares = []
    for k in range(inicio, len(textos) - 3):
        texto, anterior = textos[k], (textos[k - 1] if k else "")
        if triste(texto) or triste(anterior):
            continue
        emo, forca = pede_meme(texto, anterior)
        if forca != 2:
            continue
        for m in cand:
            p = _pontos(m, texto, anterior, emo)
            if p is None or p < 1.5:
                continue
            p -= 2.0 * _uso_recente(Path(m["file"]).name)
            if p > 0:
                pares.append((p + rnd.random() * 0.3, k, m))
    pares.sort(key=lambda x: -x[0])
    escolhidos, usos = {}, {}
    for p, k, m in pares:
        if k in escolhidos or any(abs(k - j) < cada for j in escolhidos):
            continue
        ks = usos.get(m["file"], [])
        if ks and (len(ks) >= 2 or p < nota_rep or any(abs(k - j) < longe for j in ks)):
            continue
        escolhidos[k] = m
        usos.setdefault(m["file"], []).append(k)
    return sorted(escolhidos.items())
'''
ANCORA = "    out, usados, ultimo = [], set(), -10 ** 6\n    ctx = _contexto_ligado() and bool(fichas())\n"
DESVIO = ANCORA + ('    if ctx and os.environ.get("MEMES_MOMENTO_OTIMO", "1") != "0" '
                   'and os.environ.get("MEMES_SORTEIO_GATILHO", "0") != "1":\n'
                   '        return _escolher_otimo(textos, inicio, cada, rnd)  # 26/11: melhores momentos\n')
dados = alvo.read_bytes(); crlf = b"\r\n" in dados
txt = dados.decode("utf-8").replace("\r\n", "\n")
if "_escolher_otimo" in txt:
    print("ja aplicado"); sys.exit(0)
if txt.count(ANCORA) != 1:
    print("ERRO ancora", txt.count(ANCORA)); sys.exit(1)
txt = txt.replace(ANCORA, DESVIO)
i = txt.index("\ndef escolher_interrupcoes(")
txt = txt[:i] + NOVO + txt[i:]
compile(txt, alvo.name, "exec")
bk = alvo.with_name(alvo.name + ".antes_otimo_26nov")
if "producao" in str(alvo) and not bk.exists():
    shutil.copy2(alvo, bk)
alvo.write_bytes((txt.replace("\n", "\r\n") if crlf else txt).encode("utf-8"))
print("patch ok:", alvo)
