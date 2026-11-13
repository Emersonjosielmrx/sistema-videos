"""teste_impactos_longo.py — escolha das frases de impacto (curva de locutor) no Short, no capítulo e no LONGO.
Sem IA, sem rede (o LLM é de mentira).   python teste_impactos_longo.py
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import narracao_curva as nc  # noqa: E402


def _linhas(n, semente=1):
    r = random.Random(semente)
    base = ["Ele andou pela vila em silêncio.", "A irmã dele preparava o jantar.", "O céu estava limpo naquela tarde.",
            "Mas de repente o chão tremeu!", "E foi aí que ele descobriu a verdade.", "O vilão gritou e atacou sem aviso!",
            "Ninguém acreditou no que viu.", "Eles seguiram viagem até o porto.", "O mestre explicou a técnica de novo."]
    return [r.choice(base) for _ in range(n)]


def test_short_e_capitulo_nao_mudam():
    assert [nc._quantos(n) for n in (4, 6, 7, 20, 21, 48, 96)] == [1, 1, 2, 2, 2, 4, 8]


def test_longo_ganha_impactos_pelo_video_todo():
    nc._pelo_llm = lambda linhas, k: None            # sem LLM: heurística
    linhas = _linhas(1500)
    lst = nc.escolher_impactos(linhas)
    assert 60 <= len(lst) <= 80, len(lst)            # antes: 8 em 1.500 frases
    assert lst == sorted(set(lst)) and lst[0] > 0 and lst[-1] < 1500
    assert all(b - a >= 3 for a, b in zip(lst, lst[1:]))
    # espalhados: todo trecho de 150 frases tem pelo menos 2
    assert all(sum(1 for i in lst if ini <= i < ini + 150) >= 2 for ini in range(0, 1500, 150))
    na_curva = sum(1 for i in range(1500) if nc.curva_climax(i, lst, 1500) != (0, 0, 0.0))
    assert na_curva / 1500 > 0.3, na_curva            # antes ~5% das frases tinham variação de voz


def test_longo_com_llm_por_janela():
    chamadas = []

    def falso(linhas, k):
        chamadas.append((len(linhas), k))
        return sorted(random.Random(len(chamadas)).sample(range(1, len(linhas)), k))
    nc._pelo_llm = falso
    lst = nc.escolher_impactos(_linhas(1000, 2))
    assert len(chamadas) == 8 and all(t <= 130 for t, _k in chamadas), chamadas   # nunca 1.000 frases numa chamada
    assert 40 <= len(lst) <= 55, len(lst)


def test_llm_caiu_no_meio_nao_trava():
    n = {"c": 0}

    def cai(linhas, k):
        n["c"] += 1
        if n["c"] >= 2:
            raise TimeoutError("sem resposta")
        return list(range(5, 5 + 4 * k, 4))
    nc._pelo_llm = cai
    lst = nc.escolher_impactos(_linhas(1200, 3))
    assert n["c"] == 2 and len(lst) >= 45, (n, len(lst))   # 1 falha e pronto: o resto vai de heurística


def test_teto_antigo_por_env():
    nc.IMPACTOS_MAX = 8
    try:
        assert nc._quantos(1500) == 8
    finally:
        nc.IMPACTOS_MAX = 0


def test_gatilho_palavra_inteira():
    assert not nc._GATILHO.findall("A massa de chocolate ficou no morro, de acordo com a máscara.")
    assert len(nc._GATILHO.findall("Mas de repente ele descobriu a verdade e gritou!")) == 5


if __name__ == "__main__":
    falhas = 0
    for nome, f in sorted(globals().items()):
        if nome.startswith("test_"):
            try:
                f()
                print(f"ok    {nome}")
            except AssertionError as e:
                falhas += 1
                print(f"FALHA {nome}: {e!r}"[:600])
    print("tudo certo" if not falhas else f"{falhas} teste(s) falharam")
    sys.exit(1 if falhas else 0)
