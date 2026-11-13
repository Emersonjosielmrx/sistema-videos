"""Achados A1 e A3 do agente online (13/11): frase comum não vira gore nem impacto. Sem IA, sem rede.
    python teste_gore_e_impacto.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fx_detect  # noqa: E402
import viralizador  # noqa: E402

FICAM = ["Os membros da guilda choraram quando ele morreu.",
         "Depois do banho, ela viu sangue na toalha.",
         "Ele arrancou o carro e o pai morreu de susto.",
         "O rei morreu e o reino ficou coberto de neve.",
         "Ela lavou a roupa e o sangue saiu.",
         "Ele foi morto no Rio de Janeiro.",
         "O assassino esmagou a concorrência nas vendas.",
         "Ela cuspiu o chá quando soube que ele morreu."]
TROCAM = ["Sangue jorrou do peito dele e formou uma poça.",
          "Ele arrancou a cabeça do monstro e o matou.",
          "O chão ficou coberto de sangue depois que ele morreu."]


def _limpar(txt):
    return viralizador.anti_ban(txt)


def test_gore():
    for f in FICAM:
        s = _limpar(f)
        assert "desviv" not in s and "suco de tomate" not in s and "criminoso" not in s and "perdeu a vida" not in s, (f, s)
    for f in TROCAM:
        s = _limpar(f)
        assert s != f, f"deveria trocar: {f}"


def test_impacto_por_lista():
    casa = lambda txt, l: fx_detect._casa_lista(txt.lower(), l)  # noqa: E731
    for calma in ("O gato caiu da caixa", "Eles debateram o plano", "Ele tirou a espada da bainha devagar"[:13],
                  "Ela teve coragem", "Uma vitória absoluta", "Pouco depois"):
        assert not casa(calma, fx_detect.IMPACT_KEYWORDS), calma
    for acao in ("Ele deu um soco no rosto", "A parede quebrou", "Um tiro acertou o ombro", "Ele cai do penhasco",
                 "A explosão destruiu tudo", "Luta na arena"):
        assert casa(acao, fx_detect.IMPACT_KEYWORDS), acao
    assert casa("ela está assustada no quarto", fx_detect.TENSION_KEYWORDS)
    assert casa("silêncio pesado na sala", fx_detect.TENSION_KEYWORDS)
    assert not casa("ele tomou o remédio", fx_detect.TENSION_KEYWORDS)


if __name__ == "__main__":
    test_gore()
    test_impacto_por_lista()
    print("tudo certo")
