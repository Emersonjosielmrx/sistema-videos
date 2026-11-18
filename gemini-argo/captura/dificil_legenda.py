"""17/11 (dona): tarefa DIFÍCIL tirada do nosso código de vídeo (recapd bin/legenda_mix.py, blocos() da legenda MIX),
para separar Hydrogen x Argon x Gemini 3.8 com o Opus 5.5 de referência. Mesma máquina do hibridos_bench
(Claude Code CLI pelo proxy, pasta nova, testes escondidos).
    python dificil_legenda.py --ref          confere: bug falha nos testes, referência passa em todos
    python dificil_legenda.py MODELO [...]   roda os modelos (um por vez)"""
import shutil
import sys
from pathlib import Path

import hibridos_bench as hb

LEG = {
    "legenda_mix.py": '''"""Trecho da legenda cinética MIX dos Shorts (recapd bin/legenda_mix.py).
alinhadas = [(palavra, ini_s, fim_s)] vindas do Whisper, em ordem de tempo."""
import re

CURTAS = {"a", "o", "e", "é", "de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas", "um", "uma", "que",
          "com", "pra", "para", "por", "se", "seu", "sua", "te", "eu", "ao", "à", "os", "as", "ou", "mas", "não",
          "já", "tem", "vai", "só", "isso", "essa", "esse", "ela", "ele", "me", "mais", "muito", "quem", "como"}


def _limpa(w):
    return re.sub(r"^[^\\wÀ-ÿ]+|[^\\wÀ-ÿ!?%]+$", "", w)


def blocos(alinhadas):
    """[(curtas_em_cima, forte, ini, fim)] — curtas se juntam à próxima forte; cada bloco fica até o próximo."""
    bl, pre = [], []
    for w, s, e in alinhadas:
        if _limpa(w).lower() in CURTAS and len(pre) < 3:
            pre.append((w, s, e))
            continue
        bl.append(([x[0] for x in pre], w, pre[0][1] if pre else s, e))
        pre = []
    if pre:
        bl.append(([x[0] for x in pre[:-1]], pre[-1][0], pre[0][1], pre[-1][2]))
    res = []
    for i, (cima, forte, s, e) in enumerate(bl):
        prox = bl[i + 1][2] if i + 1 < len(bl) else e + 0.5
        res.append((cima, forte, s, max(min(prox, e + 0.5), s + 0.3)))
    return res
''',
}

PEDIDO = (
    "o arquivo legenda_mix.py tem a função blocos() da nossa legenda cinética dos Shorts. Reescreva blocos() para "
    "cumprir TODAS as regras abaixo ao mesmo tempo (o formato de saída continua [(curtas_em_cima, forte, ini, fim)], "
    "com curtas_em_cima = lista de palavras e ini/fim em segundos arredondados com round(x, 2)):\n"
    "1. Palavras vazias depois do _limpa (ex.: '...', '—', '') são descartadas e não contam em nada.\n"
    "2. Curta = _limpa(w).lower() em CURTAS. As curtas se juntam à PRÓXIMA forte, no máximo 3 em cima; a 4ª curta "
    "seguida vira ela mesma uma forte (com as 3 anteriores em cima).\n"
    "3. PAUSA: se entre o fim de uma palavra e o início da seguinte houver 0,6 s ou mais, as curtas acumuladas NÃO "
    "atravessam a pausa: as que estavam esperando viram um bloco antes da pausa (a última delas é a forte, as outras "
    "em cima). O mesmo vale para o fim da lista (como no código atual).\n"
    "4. PONTUAÇÃO: uma curta terminada em '.', '!' ou '?' (ex.: 'não!') fecha a frase: ela vira a forte do bloco com as "
    "curtas que esperavam em cima, sem esperar a próxima palavra.\n"
    "5. TEMPO: ini do bloco = início da primeira palavra dele. fim = mínimo entre (início do próximo bloco) e (fim da "
    "última palavra do bloco + 0,5); mas nunca menos que ini + 0,3. EXCEÇÃO: o fim nunca pode passar do início do "
    "próximo bloco (sem sobreposição), mesmo que isso deixe o bloco com menos de 0,3 s.\n"
    "6. LARGURA: se a soma dos caracteres (len) das curtas em cima passar de 14, as curtas mais ANTIGAS que estouram "
    "saem e viram um bloco próprio antes (a última delas como forte), mantendo em cima as mais recentes que cabem.\n"
    "Não mude _limpa nem CURTAS. Escreva seus próprios testes para conferir cada regra e rode-os. Não use internet.")

PREP = "from legenda_mix import blocos\n"
CASOS = [
    # básico (o comportamento atual que continua valendo)
    "blocos([('o', 0, .2), ('rei', .2, .6)]) == [(['o'], 'rei', 0, 1.1)]",
    "blocos([('Ele', 0, .3), ('morreu', .3, .8), ('hoje', .8, 1.2)]) == [(['Ele'], 'morreu', 0, .8), ([], 'hoje', .8, 1.7)]",
    "blocos([]) == []",
    # regra 1: vazias
    "blocos([('...', 0, .1), ('rei', .1, .5)]) == [([], 'rei', .1, 1.0)]",
    "blocos([('o', 0, .2), ('—', .2, .3), ('rei', .3, .6)]) == [(['o'], 'rei', 0, 1.1)]",
    # regra 2: no máximo 3 em cima
    "blocos([('e', 0, .1), ('a', .1, .2), ('o', .2, .3), ('de', .3, .4), ('rei', .4, .8)])[0] == (['e', 'a', 'o'], 'de', 0, .4)",
    "blocos([('e', 0, .1), ('a', .1, .2), ('o', .2, .3), ('de', .3, .4), ('rei', .4, .8)])[1] == ([], 'rei', .4, 1.3)",
    # regra 3: pausa
    "blocos([('e', 0, .2), ('o', .2, .4), ('rei', 1.2, 1.6)]) == [(['e'], 'o', 0, .9), ([], 'rei', 1.2, 2.1)]",
    "blocos([('e', 0, .2), ('rei', .79, 1.0)]) == [(['e'], 'rei', 0, 1.5)]",
    "blocos([('e', 0, .2), ('rei', .8, 1.0)]) == [([], 'e', 0, .7), ([], 'rei', .8, 1.5)]",
    "blocos([('rei', 0, .4), ('de', .5, .6), ('ferro', 2.0, 2.4)]) == [([], 'rei', 0, .5), ([], 'de', .5, 1.1), ([], 'ferro', 2.0, 2.9)]",
    # regra 4: pontuação
    "blocos([('e', 0, .2), ('não!', .2, .5), ('rei', .6, .9)]) == [(['e'], 'não!', 0, .6), ([], 'rei', .6, 1.4)]",
    "blocos([('isso.', 0, .3), ('rei', .4, .7)]) == [([], 'isso.', 0, .4), ([], 'rei', .4, 1.2)]",
    "blocos([('o', 0, .2), ('rei?', .2, .5), ('sim', .6, .9)]) == [(['o'], 'rei?', 0, .6), ([], 'sim', .6, 1.4)]",
    # regra 5: tempo
    "blocos([('rei', 0, .1), ('sim', .15, .4)]) == [([], 'rei', 0, .15), ([], 'sim', .15, .9)]",
    "blocos([('rei', 0, .1), ('sim', 1.0, 1.4)]) == [([], 'rei', 0, .6), ([], 'sim', 1.0, 1.9)]",
    "blocos([('rei', 0, .05)]) == [([], 'rei', 0, .55)]",
    "blocos([('rei', 1.0, 1.02)]) == [([], 'rei', 1.0, 1.52)]",
    "all(b[3] <= c[2] for b, c in zip(blocos([('a', 0, .1), ('rei', .1, .2), ('o', .21, .3), ('mar', .3, .4)]), blocos([('a', 0, .1), ('rei', .1, .2), ('o', .21, .3), ('mar', .3, .4)])[1:]))",
    # regra 6: largura
    "blocos([('muito', 0, .1), ('muito', .1, .2), ('muito', .2, .3), ('rei', .3, .6)]) == [([], 'muito', 0, .1), (['muito', 'muito'], 'rei', .1, 1.1)]",
    "blocos([('isso', 0, .1), ('essa', .1, .2), ('esse', .2, .3), ('rei', .3, .6)]) == [(['isso', 'essa', 'esse'], 'rei', 0, 1.1)]",
    "blocos([('muito', 0, .1), ('muito', .1, .2), ('mais', .2, .3), ('rei', .3, .6)]) == [(['muito', 'muito', 'mais'], 'rei', 0, 1.1)]",
    # combinadas
    "blocos([('...', 0, .1), ('e', .1, .2), ('não.', .2, .4), ('o', 1.2, 1.3), ('rei', 1.3, 1.6)]) == [(['e'], 'não.', .1, .9), (['o'], 'rei', 1.2, 2.1)]",
    "blocos([('O', 0, .2), ('Rei', .2, .5), ('morreu!', .5, .9), ('E', 2.0, 2.1)]) == [(['O'], 'Rei', 0, .5), ([], 'morreu!', .5, 1.4), ([], 'E', 2.0, 2.6)]",
    "isinstance(blocos([('rei', 0, .333333)])[0][3], float) and blocos([('rei', 0, .333333)])[0][3] == 0.83",
]

# Solução de referência (minha), só para validar os testes; o agente não vê.
REF = '''import re

CURTAS = {"a", "o", "e", "é", "de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas", "um", "uma", "que",
          "com", "pra", "para", "por", "se", "seu", "sua", "te", "eu", "ao", "à", "os", "as", "ou", "mas", "não",
          "já", "tem", "vai", "só", "isso", "essa", "esse", "ela", "ele", "me", "mais", "muito", "quem", "como"}


def _limpa(w):
    return re.sub(r"^[^\\wÀ-ÿ]+|[^\\wÀ-ÿ!?%]+$", "", w)


def blocos(alinhadas):
    pal = [(w, s, e) for w, s, e in alinhadas if _limpa(w)]
    bl, pre = [], []

    def fecha_pre():
        if pre:
            bl.append(([x[0] for x in pre[:-1]], pre[-1][0], pre[0][1], pre[-1][2]))
            pre.clear()

    ult_fim = None
    for w, s, e in pal:
        if ult_fim is not None and s - ult_fim >= 0.6 - 1e-9:
            fecha_pre()
        ult_fim = e
        curta = _limpa(w).lower() in CURTAS
        if curta and w.rstrip().endswith((".", "!", "?")):
            pre.append((w, s, e))
            fecha_pre()
            continue
        if curta and len(pre) < 3:
            pre.append((w, s, e))
            while sum(len(x[0]) for x in pre) > 14:
                velho = pre.pop(0)
                bl.append(([], velho[0], velho[1], velho[2]))
            continue
        bl.append(([x[0] for x in pre], w, pre[0][1] if pre else s, e))
        pre.clear()
    fecha_pre()
    res = []
    for i, (cima, forte, s, e) in enumerate(bl):
        fim = min(bl[i + 1][2], e + 0.5) if i + 1 < len(bl) else e + 0.5
        fim = max(fim, s + 0.3)
        if i + 1 < len(bl):
            fim = min(fim, bl[i + 1][2])
        res.append((cima, forte, round(s, 2), round(fim, 2)))
    return res
'''

TAREFA = {"legenda_blocos": (LEG, PREP, CASOS, PEDIDO)}


def conferir_ref():
    for nome, txt in (("bug", LEG["legenda_mix.py"]), ("ref", REF)):
        p = Path("_val_leg") / nome
        shutil.rmtree(p, ignore_errors=True)
        p.mkdir(parents=True)
        (p / "legenda_mix.py").write_text(txt, "utf-8")
        r = hb.nota(p, PREP, CASOS)
        print(nome, f"{r['ok']}/{len(CASOS)}", *r["falhas"][:8], sep="\n  ")
    shutil.rmtree("_val_leg", ignore_errors=True)


if __name__ == "__main__":
    hb.TAREFAS = TAREFA
    hb.PLACAR = Path(__file__).with_name("dificil_placar.json")
    hb.BASE = Path(__file__).with_name("dificil")
    if sys.argv[1:] == ["--ref"]:
        conferir_ref()
    else:
        for m in sys.argv[1:]:
            hb.rodar(m, "legenda_blocos")
