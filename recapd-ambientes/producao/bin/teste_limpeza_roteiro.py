"""teste_limpeza_roteiro.py — limpeza das linhas que a IA devolve (roteiro e balões). Sem IA, sem rede.
    python teste_limpeza_roteiro.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import anime_script as a  # noqa: E402
import claude_client as c  # noqa: E402

CASOS = {
    # número que faz parte da frase FICA (antes sumia: "300 soldados" -> "soldados")
    "300 soldados cercaram a vila naquela noite.": "300 soldados cercaram a vila naquela noite.",
    "2 anos depois, ele voltou mais forte.": "2 anos depois, ele voltou mais forte.",
    "1995 foi o ano em que tudo mudou.": "1995 foi o ano em que tudo mudou.",
    "10.000 moedas sumiram do cofre.": "10.000 moedas sumiram do cofre.",
    "3.5 segundos foi o que ele precisou.": "3.5 segundos foi o que ele precisou.",
    "- 10 mil moedas de ouro era o preço.": "10 mil moedas de ouro era o preço.",
    # marcador de lista e markdown SAEM
    "1. Ele acordou no hospital sem memória.": "Ele acordou no hospital sem memória.",
    "12) A irmã dele sorriu pela primeira vez.": "A irmã dele sorriu pela primeira vez.",
    "* **Ele caiu de joelhos no chão.**": "Ele caiu de joelhos no chão.",
    "## O garoto abriu os olhos devagar.": "O garoto abriu os olhos devagar.",
    "...e então ele caiu no chão.": "e então ele caiu no chão.",
    # aspas: em volta da frase inteira saem; fala no meio fica com as DUAS
    '"Ele nunca mais voltou pra casa."': "Ele nunca mais voltou pra casa.",
    '"Você não é nada", disse ela.': '"Você não é nada", disse ela.',
    'Ele gritou: "sai daqui agora!"': 'Ele gritou: "sai daqui agora!"',
    '"E foi aí que o nosso garoto entendeu': "E foi aí que o nosso garoto entendeu",
    # não estraga
    "-chan chamou por ele de novo ali.": "-chan chamou por ele de novo ali.",
    "O gota d'água foi a risada dela.": "O gota d'água foi a risada dela.",
    "O arquivo save_01 tinha sumido dali.": "O arquivo save_01 tinha sumido dali.",
}


def test_linhas_do_roteiro():
    for entrada, saida in CASOS.items():
        assert a._clean_lines(entrada) == [saida], (entrada, a._clean_lines(entrada))


def test_frases_com_tempo_mantem_numero():
    frases, tempos = a._frases_com_tempo("[3s] 300 soldados cercaram a vila naquela noite.\n"
                                         "[9s] 2 anos depois, o nosso garoto voltou.", 30)
    assert tempos == [3.0, 9.0] and frases[0].startswith("300 ") and frases[1].startswith("2 anos"), frases


def test_baloes():
    r = c._balloon_lines("1. Você voltou?\n100 anos se passaram...\n- Saia daqui!\n...\n3... 2... 1...\nSEM TEXTO\n-Não!")
    assert r == ["Você voltou?", "100 anos se passaram...", "Saia daqui!", "3... 2... 1...", "Não!"], r


def test_onomatopeia_nao_apaga_nome_nem_palavra():
    import _tts_filter as t
    fica = {"Kang Dong-su entrou na sala e encarou o presidente.": "Kang Dong-su entrou na sala e encarou o presidente",
            "A cantora de K-pop Ann chegou com o Sr. Bang.": "A cantora de K-pop Ann chegou com o Sr. Bang",
            "O boom do mercado deixou ele rico.": "O boom do mercado deixou ele rico",
            "Com um click, o portal abriu.": "Com um click, o portal abriu",
            "Zhang Dong venceu o torneio.": "Zhang Dong venceu o torneio",
            "Lee Tum e Park Ang são rivais.": "Lee Tum e Park Ang são rivais"}
    sai = {"DING DONG! A campainha tocou.": "A campainha tocou",
           "BANG! A porta caiu.": "A porta caiu",
           "Bang! A porta caiu.": "A porta caiu",
           "POP POP a bolha estourou.": "a bolha estourou",
           "Ugh, que nojo, disse ela.": "que nojo, disse ela",
           "Ele roncava, zzz, a noite toda.": "Ele roncava, a noite toda"}
    for entrada, saida in {**fica, **sai}.items():
        assert t.clean_for_tts(entrada) == saida, (entrada, t.clean_for_tts(entrada))


def test_sigla_numero_e_janela_de_sistema_ficam():
    import _tts_filter as t
    casos = {"O NPC entregou a missão secreta.": "O NPC entregou a missão secreta",
             "O HP dele caiu pra 10 e o MP zerou.": "O HP dele caiu pra 10 e o MP zerou",
             "Ela ligou a TV e viu o CEO da empresa.": "Ela ligou a TV e viu o CEO da empresa",
             "RPG de mesa era o hobby dele.": "RPG de mesa era o hobby dele",
             "O prêmio era de 10000000 de wons.": "O prêmio era de 10000000 de wons",
             "[Missão concluída] Recompensa: 300 moedas.": "Missão concluída Recompensa: 300 moedas",
             "[CORTE] Ele acordou.": "Ele acordou",               # a diretiva sai, a frase fica (antes a linha toda sumia)
             "return para casa era o plano dele.": "return para casa era o plano dele",
             "if ele perder, tudo acaba.": "if ele perder, tudo acaba"}
    for entrada, saida in casos.items():
        assert t.clean_for_tts(entrada) == saida, (entrada, t.clean_for_tts(entrada))
    assert "SSS" in t.clean_for_tts("Ele virou um caçador rank SSS em uma semana.")
    # código e ruído continuam saindo
    for lixo in ("if (x == 1) { return y; }", "for i in range(10):", "import os", "return x", "const a = 5",
                 '{"a": 1}', "<div>oi</div>", "[1, 2, 3]"):
        assert t.clean_for_tts(lixo) == "", (lixo, t.clean_for_tts(lixo))
    assert t.clean_for_tts("SSP NNG ele gemeu de dor.") == "ele gemeu de dor"
    assert "DEADBEEF1234" not in t.clean_for_tts("O id era DEADBEEF1234 no sistema.")


def test_romano_so_quando_e_numero():
    import anime_tts as tts
    casos = {"Ele era um caçador Rank X, o mais raro.": "Rank X,", "O X da questão era o dinheiro.": "O X da",
             "O Projeto X foi cancelado.": "Projeto X ", "O Sr. X apareceu de novo.": "Sr. X ",
             "Capítulo V: a queda.": "Capítulo 5:", "Henrique V subiu ao trono.": "Henrique 5 ",
             "Luís XIV mandou prender todos.": "Luís 14 ", "Temporada II chegou.": "Temporada 2 ",
             "Parte X do torneio.": "Parte 10 "}
    for entrada, pedaco in casos.items():
        assert pedaco in tts._seguro(entrada), (entrada, tts._seguro(entrada))


def test_erro_da_ia_nao_confunde_com_narracao():
    narracao = ["O prompt certo muda tudo no resultado da IA.", "Ele escreveu um prompt de três linhas e faturou dez mil.",
                "A generative AI mudou o mercado em 2026.", "Sem a api key, o robô não funciona.",
                "Ele bateu no rate limit e perdeu o cliente.", "Envie a transcrição do áudio pro cliente em um clique.",
                "Cole o texto no ChatGPT e veja a mágica.", "Mande o vídeo pro grupo da família.",
                "A exception: ele nunca perdia.", "O conteúdo sensível não aparece no feed.",
                "Me passe o vídeo, disse o chefe.", "Isso viola as diretrizes do reino, disse o rei.",
                "Como ia sair dali, ninguém sabia.", "Ele repetiu o erro 100 vezes."]
    erro = ["I'm sorry, but I can't help with that request.", "As an AI language model, I cannot write this.",
            "Não posso ajudar com esse pedido.", "Como modelo de linguagem, não tenho acesso ao vídeo.",
            "Error 429: rate limit exceeded", "Invalid API key provided", "HTTP 503 Service Unavailable",
            "Traceback (most recent call last):", "RuntimeError: quota exceeded", "Internal Server Error",
            "Envie a transcrição para que criar o roteiro completo no estilo do narrador, garantindo perfeita para o loop.",
            "Por favor, cole o texto aqui para eu reescrever.", "Aqui está o roteiro:\nFrase um.",
            "Mande o vídeo original e eu faço o roteiro.", "Isso viola as diretrizes de uso da plataforma.",
            "Please provide the transcript.", "O prompt acima não trouxe a transcrição.",
            "This request was blocked by the safety filter."]
    for s in narracao:
        assert not a.resposta_de_erro(s), s
    for s in erro:
        assert a.resposta_de_erro(s), s


def test_frase_curta_e_abreviacao_nao_somem():
    f, t = a._frases_com_tempo("[12s] Ele abriu a porta. Vazio. Ninguém estava lá.", 60)
    assert f == ["Ele abriu a porta. Vazio.", "Ninguém estava lá."] and t == [12.0, 16.0], (f, t)
    f, _t = a._frases_com_tempo("[5s] O Sr. Kim chegou cedo. A Dra. Lee já esperava.", 60)
    assert f == ["O Sr. Kim chegou cedo.", "A Dra. Lee já esperava."], f
    f, _t = a._frases_com_tempo("[3s] Não! Ele gritou e correu pra fora.", 60)
    assert f == ["Não! Ele gritou e correu pra fora."], f
    f, t = a._frases_com_tempo("[3s] Primeira frase do trecho aqui.\n[9s] Segunda frase do trecho aqui.", 60)
    assert f == ["Primeira frase do trecho aqui.", "Segunda frase do trecho aqui."] and t == [3.0, 9.0]
    assert a._sentencas("") == [] and a._sentencas("...") == []
    assert a._clean_lines("Ele abriu a porta devagar.\nVazio.\n---\nNinguém estava lá dentro.") == \
        ["Ele abriu a porta devagar. Vazio.", "Ninguém estava lá dentro."]
    assert a._clean_lines("Fim\nOk\n1.") == []          # lixo curto continua saindo


if __name__ == "__main__":
    falhas = 0
    for nome, f in sorted(globals().items()):
        if nome.startswith("test_"):
            try:
                f()
                print(f"ok    {nome}")
            except AssertionError as e:
                falhas += 1
                print(f"FALHA {nome}: {e!r}")
    print("tudo certo" if not falhas else f"{falhas} teste(s) falharam")
    sys.exit(1 if falhas else 0)
