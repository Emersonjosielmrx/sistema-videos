"""teste_legenda_tempos.py — tempo real de cada palavra da legenda (karaokê) quando a voz e o roteiro não têm a
mesma contagem de palavras. Sem IA, sem rede.   python teste_legenda_tempos.py
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fx_subtitles as f  # noqa: E402


def _voz(palavras, passo=0.4):
    return [[round(k * passo, 2), round(k * passo + passo * 0.9, 2), w] for k, w in enumerate(palavras)]


def _confere(words, r):
    assert r is not None and len(r) == len(words), r
    assert [x[2] for x in r] == words
    assert all(x[0] <= x[1] for x in r) and all(a[0] <= b[0] for a, b in zip(r, r[1:])), r


def test_contagem_igual_passa_direto():
    words = "Ele abriu a porta devagar.".split()
    wt = _voz(["Ele", "abriu", "a", "porta", "devagar"])
    assert [x[:2] for x in f._alinhar_tempos(words, wt)] == [x[:2] for x in wt]


def test_voz_partiu_nome_com_hifen():
    words = "Kang Dong-su entrou na sala.".split()                       # 5 na legenda
    wt = _voz(["Kang", "Dong", "su", "entrou", "na", "sala"])            # 6 na voz
    r = f._alinhar_tempos(words, wt)
    _confere(words, r)
    assert r[0][:2] == [0.0, 0.36] and r[2][0] == 1.2 and r[4][0] == 2.0, r   # as que casam ficam no tempo REAL
    assert r[1][0] == 0.4 and abs(r[1][1] - 1.16) < 0.01, r                     # "Dong-su" pega o tempo de Dong+su


def test_fala_trocou_palavra_do_roteiro():
    words = "O vilão matou o rei ontem.".split()                         # legenda = roteiro
    wt = _voz(["O", "vilão", "tirou", "a", "vida", "do", "rei", "ontem"])  # voz = depois do anti_ban
    r = f._alinhar_tempos(words, wt)
    _confere(words, r)
    assert r[1][0] == 0.4 and r[4][0] == 2.4 and r[5][0] == 2.8, r        # vilão, rei, ontem no tempo real
    assert r[2][0] == 0.8 and r[3][1] <= 2.4 + 1e-6, r                    # "matou o" ocupa o trecho de "tirou a vida do"


def test_palavra_a_mais_na_legenda():
    words = "Ele ganhou 1.500 moedas de ouro.".split()
    wt = _voz(["Ele", "ganhou", "mil", "e", "quinhentas", "moedas", "de", "ouro"])
    r = f._alinhar_tempos(words, wt)
    _confere(words, r)
    assert r[2][0] == 0.8 and r[3][0] == 2.0, r                            # "1.500" cobre "mil e quinhentas"


def test_nada_casa_fica_estimativa():
    assert f._alinhar_tempos("uma frase bem diferente aqui".split(), _voz(["outra", "coisa", "sem", "relação"])) is None
    assert f._alinhar_tempos([], _voz(["a"])) is None and f._alinhar_tempos(["a"], []) is None
    assert f._alinhar_tempos(["a", "b"], [["x", "y", "z"]]) is None       # sidecar estragado não derruba a legenda


def test_sorteio_nunca_quebra():
    r = random.Random(7)
    vocab = "o rei caiu e a rainha gritou não mas ele voltou forte Dong-su 1.500 moedas".split()
    for _ in range(3000):
        words = [r.choice(vocab) for _ in range(r.randint(1, 12))]
        fala = [w for w in words if r.random() > 0.15] + ([r.choice(vocab)] if r.random() < 0.3 else [])
        r.shuffle(fala) if r.random() < 0.05 else None
        res = f._alinhar_tempos(words, _voz(fala)) if fala else None
        if res is not None:
            _confere(words, res)


if __name__ == "__main__":
    falhas = 0
    for nome, fn in sorted(globals().items()):
        if nome.startswith("test_"):
            try:
                fn()
                print(f"ok    {nome}")
            except AssertionError as e:
                falhas += 1
                print(f"FALHA {nome}: {e!r}"[:600])
    print("tudo certo" if not falhas else f"{falhas} teste(s) falharam")
    sys.exit(1 if falhas else 0)
