"""teste_transicao_elemental.py — a transição elemental (água, gelo, sombra, glitch...) é escolhida pela palavra
INTEIRA / pelo começo da palavra, não por um pedaço dela. Sem IA, sem rede.   python teste_transicao_elemental.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import elemental_transitions as e  # noqa: E402

# antes de 13/11: marido/território/vários = água, animal/normal = sombra, ferro = glitch, índice = gelo,
# floresta = pétalas, aguardou = água
SEM_ELEMENTO = ["O marido dela chegou sério.", "Amanhã ele parte para o território inimigo.",
                "O animal era redondo e normal.", "Ele pegou a barra de ferro.", "O índice subiu.",
                "Vários soldados entraram na floresta.", "Ela amarrou o cabelo e aguardou o socorro."]
COM_ELEMENTO = [("Ele mergulhou no rio gelado.", "water"), ("O mar engoliu o navio.", "water"),
                ("As chamas tomaram a vila.", "fire"), ("Um raio cortou o céu.", "lightning"),
                ("Ela congelou de medo.", "ice"), ("A neve cobria tudo.", "snow"),
                ("Ele deu um soco na parede.", "shockwave"), ("Eles se beijaram.", "hearts"),
                ("A tela apagou com um erro.", "glitch"), ("A explosão destruiu tudo.", "shockwave"),
                ("O terror tomou conta dele.", "shadow"), ("As flores caíam devagar.", "petals")]


def test_pedaco_de_palavra_nao_dispara():
    for s in SEM_ELEMENTO:
        assert e.detect_element(s) is None, (s, e.detect_element(s))


def test_palavra_certa_dispara():
    for s, esperado in COM_ELEMENTO:
        assert e.detect_element(s) == esperado, (s, e.detect_element(s))
    assert e.detect_element("") is None and e.detect_element(None) is None


if __name__ == "__main__":
    falhas = 0
    for nome, fn in sorted(globals().items()):
        if nome.startswith("test_"):
            try:
                fn()
                print(f"ok    {nome}")
            except AssertionError as err:
                falhas += 1
                print(f"FALHA {nome}: {err!r}"[:600])
    print("tudo certo" if not falhas else f"{falhas} teste(s) falharam")
    sys.exit(1 if falhas else 0)
