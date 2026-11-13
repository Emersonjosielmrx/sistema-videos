"""teste_viralizador.py — o anti_ban não pode estragar palavra inocente e tem de continuar suavizando o que é de
strike. Sem IA, sem rede.   python teste_viralizador.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import viralizador as v  # noqa: E402

# frases de narração normal: têm de sair IGUAIS (todas saíam estragadas antes de 13/11)
INOCENTES = """Ele prometeu que voltaria para salvar a irmã.
O vilão cometeu um erro fatal.
Ela se comprometeu a treinar o garoto, prometendo nunca desistir.
O herói foi enviado para outro mundo.
Ele ficou aliviado ao ver a mãe.
O diamante brilhou na mão dela.
Ele comeu um biscoito e sorriu.
O garoto foi atropelado por um caminhão e acordou em outro mundo.
O manuscrito antigo escondia um segredo.
Ele chegou molhado da chuva.
Os soldados espiaram pela janela.
Eles violaram o tratado de paz.
Ele saiu cavalgando o dragão pelo céu.
Ele foi dominado pelo medo.
Eu pinto quadros desde criança.
A pedra rola morro abaixo.
Ele pegou um pedaço de pau e avançou.
A floresta virgem escondia ruínas.
A comida da mãe era gostosa.
As mãos deles se tocaram por um segundo.
Ele se tocou de que estava sendo enganado.
Ela era amante das artes.
O efeito retardado da poção começou.
O cavaleiro apelado destruiu todo mundo.
Ele submeteu o relatório ao rei.
Ele manuseou a lâmina com cuidado.
O desviado caminho levava à caverna.
Ela usava um vestido de gala.
A dominação do império durou cem anos.
O notário leu o testamento.
A galinha ciscava no quintal.
Ele gozava de boa saúde.
A heroína da história salvou o reino.
Em homenagem ao pai, ele lutou.
Roxana e Georgia chegaram ao castelo.
Ele ouviu um gemido de dor vindo da cela.
O vampiro chupou o sangue dela.
No seio da família real nasceu um traidor.
A exibição de força calou a arena.
Ele meteu o pé na porta e entrou.
O arqueiro nunca erra o alvo, é um craque.""".split("\n")

# (frase, pedaço que NÃO pode sobrar, pedaço que tem de aparecer ou None)
STRIKE = [
    ("Ela estava nua na cama e ele ficou excitado.", "nua", "sem roupa"),
    ("Eles fizeram sexo a noite toda.", "sexo", "vuco-vuco"),
    ("A calcinha dela apareceu.", "calcinha", "roupa de baixo"),
    ("Ele usava drogas e cocaína pra aguentar.", "cocaína", "aditivos proibidos"),
    ("Ele injetava heroína todo dia, viciado.", "heroína", "aditivos proibidos"),
    ("Que porra é essa, seu idiota?", "porra", "poxa"),
    ("Ela ficou molhada de tesão.", "molhada", None),
    ("Ele meteu nela com força na cama.", "meteu", None),
    ("Ele viu os seios dela.", "seios", "os frontais"),
    ("O filho da puta fugiu.", "puta", None),
    ("Ela era a amante do rei.", "amante", "affair"),
    ("As escravas fugiram do castelo.", "escrava", "servas"),
    ("Ela ficou excitada ao beijar ele.", "excitada", "acesa"),
    ("Ele seduziu a rainha.", "seduziu", "encantou"),
    ("O rei enforcou o traidor na praça.", "enforcou", "deu a gravata definitiva no traidor"),
    ("Ela tirou a cueca dele.", "cueca", "a peça de baixo"),
    ("Aquele viado correu.", "viado", None),
    ("Uma orgia no palácio.", "orgia", "festa privada"),
    ("O estupro chocou a vila.", "estupro", None),
    ("Ela gemeu, gemendo alto de prazer.", "gemendo", None),
    ("Os peitos dela e a bunda chamavam atenção.", "bunda", "bumbum"),
]


def test_palavra_inocente_fica_igual():
    ruins = [(s, v.anti_ban(s)) for s in INOCENTES if v.anti_ban(s) != s]
    assert not ruins, ruins


def test_termo_de_strike_continua_saindo():
    for frase, proibido, esperado in STRIKE:
        r = v.anti_ban(frase)
        assert proibido.lower() not in r.lower(), (frase, r)
        assert esperado is None or esperado in r, (frase, r)


def test_gore_continua_so_com_gore():
    assert v.anti_ban("Ele é do mesmo sangue do rei.") == "Ele é do mesmo sangue do rei."
    assert "uco de tomate" in v.anti_ban("Sangue jorrou do peito dele e formou uma poça.")
    assert v.anti_ban("Ele matou o dragão com um único golpe.") == "Ele matou o dragão com um único golpe."


def test_alternativas():
    assert v._alternativas(r"a|b(c|d)|[x|y]e|f\|g") == ["a", "b(c|d)", "[x|y]e", r"f\|g"]


if __name__ == "__main__":
    falhas = 0
    for nome, f in sorted(globals().items()):
        if nome.startswith("test_"):
            try:
                f()
                print(f"ok    {nome}")
            except AssertionError as e:
                falhas += 1
                print(f"FALHA {nome}: {e!r}"[:1500])
    print("tudo certo" if not falhas else f"{falhas} teste(s) falharam")
    sys.exit(1 if falhas else 0)
