# -*- coding: utf-8 -*-
"""teste_trio_gemini_a_seco.py — 14/11/2026: confere a 1ª posição do Gemini no trio do vídeo SEM gerar nada.
Reaproveita o teste_cadeia_a_seco (gera_auto falso, estado em pasta temporária) e acrescenta:
  A) TODAS as contas do Flow sem crédito + Gemini com conta -> chama o worker 1x com a sessão "gemini" e o vídeo sai
  B) TODAS sem crédito + Gemini sem conta -> pula o ciclo como antes (nenhum worker)
  C) Flow com crédito + Gemini com conta -> segue a cadeia do Flow normal (o Gemini roda DENTRO do worker)
  D) Flow sem crédito + Gemini com conta mas o worker do Gemini não entrega (exit 2) -> não marca 'gemini' como conta

    D:\\veo\\venv\\Scripts\\python.exe -X utf8 teste_trio_gemini_a_seco.py
"""
import contextlib
import io
import os
import runpy
import sys
import types

# só a MONTAGEM do teste antigo (até antes do 1º cenário): gera_auto falso, estado em pasta temporária
_arq = os.path.join(os.path.dirname(os.path.abspath(__file__)), "teste_cadeia_a_seco.py")
_src = open(_arq, encoding="utf-8").read()
_src = _src[:_src.index("# 1) PC1 em carga")]
_g = {"__name__": "teste_antigo", "__file__": _arq}
with contextlib.redirect_stdout(io.StringIO()):
    exec(compile(_src, _arq, "exec"), _g)
T = types.SimpleNamespace(**_g)
cron = T.cron
FALHAS = []


def confere(cond, txt):
    print("  ->", "OK " if cond else "FALHOU", txt)
    if not cond:
        FALHAS.append(txt)


TODAS_SEM = {k: {"saldo": 0} for k in ("aulacomia", "jornalcomia", "entrevistacomia", "seebotsia", "emersonjosiel2032")}

# A
T.preparar("A. Flow inteiro sem crédito, Gemini com conta", creditos=TODAS_SEM)
cron.todas_sessoes_esgotadas = lambda: (True, "amanhã")
cron._gemini_tem_conta = lambda: True
res, ch = T.rodar()
confere(res == "VIDEO SAIU" and ch and ch[0][0] == "gemini", "chamou o worker com a sessão 'gemini' e o vídeo saiu")
confere(len(ch) == 1, "só 1 chamada (nenhuma conta do Flow)")

# B
T.preparar("B. Flow inteiro sem crédito, Gemini SEM conta", creditos=TODAS_SEM)
cron.todas_sessoes_esgotadas = lambda: (True, "amanhã")
cron._gemini_tem_conta = lambda: False
res, ch = T.rodar()
confere("NO_ACCOUNTS" in res and not ch, "pulou o ciclo sem chamar worker (como antes)")

# C
T.preparar("C. Flow com crédito, Gemini com conta", creditos=T.SEEBOTS_NB)
cron.todas_sessoes_esgotadas = lambda: (False, None)
cron._gemini_tem_conta = lambda: True
res, ch = T.rodar()
confere(res == "VIDEO SAIU" and ch and ch[0][0] != "gemini", "usou a conta do Flow (o Gemini fica dentro do worker)")

# D
T.preparar("D. Flow sem crédito, Gemini com conta mas não entrega", creditos=TODAS_SEM,
           worker=lambda s, m: (2, "CREDITOS_ESGOTADOS padrao='gemini_sem_cota'\n"))
cron.todas_sessoes_esgotadas = lambda: (True, "amanhã")
cron._gemini_tem_conta = lambda: True
res, ch = T.rodar()
st = cron.load_sessoes_status()
confere("NO_ACCOUNTS" in res and len(ch) == 1, "1 tentativa só pelo Gemini e preservou o prompt")
confere("gemini" not in st, "'gemini' não entrou no sessoes_status das contas do Flow")

print("\nFALHAS:", FALHAS or "nenhuma")
sys.exit(1 if FALHAS else 0)
