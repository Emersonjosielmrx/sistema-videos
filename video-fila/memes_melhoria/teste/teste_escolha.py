# -*- coding: utf-8 -*-
"""Teste a seco da escolha de memes (24/11). Importa o memes_visuais da PRODUÇÃO só para leitura (não grava nada:
registrar_uso não é chamado). fx_detect é simulado."""
import random, sys, types
sys.modules["fx_detect"] = types.SimpleNamespace(meme_proibido=lambda _p: False)
sys.path.insert(0, r"D:\recapd-ambientes\producao\bin")
import memes_visuais as mv  # noqa: E402

mv.MEMES_IMG = __import__("pathlib").Path(r"D:\hipercool-materiais\assets\memes_img")
mv.NOVOS_DIR = mv.MEMES_IMG / "memes_novos"
mv.FICHAS = mv.NOVOS_DIR / "fichas.json"
mv.HISTORICO = __import__("pathlib").Path(r"D:\video-fila\memes_melhoria\teste\_hist_vazio.json")

FRASES = [
    "Ele prometeu que nunca mais ia trair a confiança dela.",
    "Mas é claro que ele mentiu de novo, e ela descobriu tudo.",
    "O vilão riu da cara dele na frente de todo mundo.",
    "Só que o nosso garoto treinou por três anos seguidos.",
    "E num golpe só ele derrotou o exército inteiro.",
    "Ninguém sabia de onde vinha aquele poder absurdo.",
    "A mãe dele morreu protegendo a vila.",
    "Ele chorou sozinho no funeral.",
    "Ela morreu de vergonha quando ele apareceu sem camisa.",
    "O arrogante desafiou o protagonista, sem saber com quem estava mexendo.",
    "E aí chegou o irmão mais velho.",
    "Na verdade, o mestre era o pai dele o tempo todo.",
    "Ele caiu na armadilha mais óbvia do mundo.",
    "Ela disse que não estava com ciúmes, mas fingiu o tempo todo.",
    "Ele simplesmente ignorou as regras e foi embora.",
    "Pela terceira vez o mesmo cara aparece pedindo dinheiro.",
    "Os soldados mataram todos os aldeões.",
    "Ele aceitou o casamento, fazer o que.",
    "O rei teve a ousadia de exigir metade das terras dele.",
    "Ele matou a saudade da família depois de dez anos.",
]

rnd = random.Random(7)
print("frase | emoção, força | meme escolhido")
for k, t in enumerate(FRASES):
    ant = FRASES[k - 1] if k else ""
    emo, forca = mv.pede_meme(t, ant)
    cand = [m for m in mv.catalogo() if m.get("novo")]
    m = mv._por_contexto(t, cand, emo, rnd, ant) if forca else None
    nome = (m["file"].split("\\")[-1] if m else "-")
    print(f"{t[:62]:62} | {emo}, {forca} | {nome}")
print("\ncatálogo:", len(mv.catalogo()), "| fichas:", len(mv.fichas()))
print("interrupções (inicio=0, cada=3):",
      [(k, m["file"].split("\\")[-1]) for k, m in mv.escolher_interrupcoes(FRASES, inicio=0, cada=3, rnd=random.Random(7))])
