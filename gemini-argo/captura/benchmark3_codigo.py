#!/usr/bin/env python3
"""Benchmark de CÓDIGO real: 4 tarefas do nosso código, testes executados de verdade.

Rodada 1 = resposta direta (pass@1). Rodadas 2-3 = o modelo recebe a saída dos testes que falharam e corrige
(o laço que um agente com ferramentas faz: escreve, roda, lê o erro, conserta).
    python benchmark3_codigo.py            # todos os modelos
    python benchmark3_codigo.py argon      # só os que contêm 'argon' no nome
"""
import io
import json
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
TOKEN = "<SEGREDO_REMOVIDO>"
OMNI = "http://157.173.207.22:20128/v1/chat/completions"
MODELOS = [
    ("Argon (HTTP)", "http://127.0.0.1:20141/v1/chat/completions", "gemini-4-argon"),
    ("Opus 5.5", OMNI, "cc/claude-opus-5-5"),
    ("Kiro Sonnet 4.5", OMNI, "kr/claude-sonnet-4.5"),
    ("Gemini 3.8 Flash", OMNI, "agy/gemini-3.8-flash-high"),
]
RODADAS = 3
SAIDA = Path(__file__).with_suffix(".json")

# ───────────────────────────── tarefas ─────────────────────────────

T_NUMERO = {
    "nome": "numero_youtube",
    "pedido": """Escreva em Python a função `numero(txt)` que converte textos de contagem do YouTube em int.
Regras:
- Aceita formatos em português: "1,2 mil visualizações" -> 1200, "3,4 mi de inscritos" -> 3400000,
  "2,5 bi" -> 2500000000, "12.345 visualizações" -> 12345 (ponto é separador de milhar), "987 visualizações" -> 987.
- Aceita também sufixos K/M/B maiúsculos ou minúsculos: "1,5K views" -> 1500, "2.3M" -> 2300000 (aqui o ponto
  ANTES de um sufixo é decimal).
- "Nenhuma visualização", "Sem inscritos" e textos sem número mas com "nenhum"/"sem" -> 0.
- Texto vazio, None ou sem número (e sem "nenhum"/"sem") -> None.
- O resultado tem que ser EXATO (cuidado com erro de ponto flutuante: 3,4 mi tem que dar 3400000, não 3399999).
- "\\xa0" (espaço não separável) pode aparecer no lugar do espaço.""",
    "testes": r'''
from sol import numero as n
casos = [(n("1,2 mil visualizações"),1200),(n("3,4 mi de inscritos"),3400000),(n("12.345 visualizações"),12345),
 (n("Nenhuma visualização"),0),(n("1 inscrito"),1),(n("10 mil"),10000),(n("1.234.567 views"),1234567),(n(""),None),
 (n(None),None),(n("2,5 bi"),2500000000),(n("987 visualizações"),987),(n("1,5K views"),1500),(n("Sem inscritos"),0),
 (n("2.3M"),2300000),(n("4,1\xa0mi de inscritos"),4100000),(n("8,7 mil"),8700),(n("assista agora"),None),
 (n("1,1 mi"),1100000),(n("0,3 mil"),300),(n("5k"),5000)]
''',
}

T_HORARIO = {
    "nome": "proximo_horario",
    "pedido": """Escreva em Python a função `proximo_horario(horarios, agora, margem_min=25, ocupados=())`.
- `horarios`: lista de strings "HH:MM" (horários diários de postagem, podem vir fora de ordem).
- `agora`: datetime (sem fuso).
- Retorna o PRIMEIRO datetime futuro, em qualquer dia a partir de hoje, cujo horário está em `horarios`, que seja
  >= agora + margem_min minutos (compare com `agora` exato, incluindo segundos) e que NÃO esteja em `ocupados`
  (coleção de datetimes já agendados). O retorno tem segundos e microssegundos zerados.
- Procura no máximo 7 dias à frente (hoje + 7); se não achar ou `horarios` vazio, retorna None.
- Horários inválidos (ex.: "25:00", "ab:cd") são ignorados.""",
    "testes": r'''
from datetime import datetime as D
from sol import proximo_horario as p
H = ["21:10","11:40","17:50"]
casos = [
 (p(H, D(2026,10,27,10,0)), D(2026,10,27,11,40)),
 (p(H, D(2026,10,27,11,20)), D(2026,10,27,17,50)),     # 11:40 < 11:20+25
 (p(H, D(2026,10,27,11,15)), D(2026,10,27,11,40)),     # exatamente na margem
 (p(H, D(2026,10,27,21,0)), D(2026,10,28,11,40)),      # vira o dia
 (p(H, D(2026,10,27,10,0), ocupados={D(2026,10,27,11,40)}), D(2026,10,27,17,50)),
 (p([], D(2026,10,27,10,0)), None),
 (p(["23:50"], D(2026,12,31,23,40), margem_min=15), D(2027,1,1,23,50)),
 (p(["00:05"], D(2026,12,31,23,50)), D(2027,1,2,0,5)),           # 00:15 do dia 1 já passou das 00:05
 (p(["00:20"], D(2026,12,31,23,50)), D(2027,1,1,0,20)),
 (p(["25:00","ab:cd","12:00"], D(2026,10,27,8,0)), D(2026,10,27,12,0)),
 (p(["12:00"], D(2026,10,27,8,0), ocupados={D(2026,10,27,12,0)+__import__("datetime").timedelta(days=i) for i in range(8)}), None),
 (p(["12:00"], D(2026,10,27,11,35,30,500)), D(2026,10,28,12,0)),   # 11:35:30 + 25 > 12:00
 (p(["12:00"], D(2026,10,27,11,35,0)), D(2026,10,27,12,0)),
 (p(H, D(2026,10,27,10,0), margem_min=0), D(2026,10,27,11,40)),
 (p(["09:00"], D(2026,10,27,9,0), margem_min=0), D(2026,10,27,9,0)),
]
''',
}

T_PAUSA = {
    "nome": "conserto_pausa_ytdlp",
    "pedido": '''Esta classe controla a pausa do yt-dlp quando o YouTube bloqueia o IP. Ela tem bugs. Conserte e devolva a
classe inteira corrigida.
Regras que ela DEVE seguir:
- `bloqueio(agora)` registra um bloqueio e devolve a pausa em minutos. 1º bloqueio: 20 min.
- Se um novo bloqueio acontece em até 60 min depois do FIM da pausa anterior (ou durante ela), a pausa dobra
  em relação à anterior: 20 -> 40 -> 80 -> 120 (teto de 120, nunca passa).
- Se o novo bloqueio acontece mais de 60 min depois do fim da pausa anterior, volta para 20.
- `pode_rodar(agora)` é True quando não há pausa ou quando agora >= fim da pausa.
- `fim` é o datetime em que a pausa atual acaba (None antes do 1º bloqueio).

```python
from datetime import timedelta

class Pausa:
    def __init__(self):
        self.minutos = 0
        self.fim = None

    def bloqueio(self, agora):
        if self.fim and agora - self.fim < timedelta(minutes=60):
            self.minutos = self.minutos * 2
        else:
            self.minutos = 20
        self.fim = agora + timedelta(minutes=self.minutos)
        return self.minutos

    def pode_rodar(self, agora):
        return self.fim is None or agora > self.fim
```''',
    "testes": r'''
from datetime import datetime as D, timedelta as T
from sol import Pausa
t0 = D(2026,10,27,10,0)
def seq(*deltas):
    p = Pausa(); r = []
    for d in deltas: r.append(p.bloqueio(t0 + T(minutes=d)))
    return r
p = Pausa()
casos = [
 (p.pode_rodar(t0), True),
 (p.fim, None),
 (seq(0), [20]),
 (seq(0, 30), [20, 40]),            # 10 min depois do fim
 (seq(0, 80), [20, 40]),            # exatamente 60 min depois do fim
 (seq(0, 81), [20, 20]),            # passou de 60
 (seq(0, 10), [20, 40]),            # durante a pausa
 (seq(0, 30, 80, 170, 300), [20, 40, 80, 120, 120]),
 (seq(0, 30, 80, 400), [20, 40, 80, 20]),
 (seq(0, 30, 80, 170, 300, 600), [20, 40, 80, 120, 120, 20]),
]
q = Pausa(); q.bloqueio(t0)
casos += [(q.pode_rodar(t0 + T(minutes=19)), False), (q.pode_rodar(t0 + T(minutes=20)), True),
          (q.fim, t0 + T(minutes=20))]
''',
}

T_PARSER = {
    "nome": "parser_gemini",
    "pedido": r"""Escreva em Python a função `extrair_texto(body)` que lê a resposta em streaming do endpoint interno do Gemini.
Formato do `body` (str):
- Pode começar com o prefixo anti-JSON `)]}'` seguido de quebra(s) de linha.
- Depois vem uma sequência de blocos: uma linha só com um número (tamanho do bloco, IGNORE o valor, pode estar
  errado) e na(s) linha(s) seguinte(s) um array JSON (o array é sempre uma única linha).
- Cada array JSON é uma lista de entradas; interessam as entradas que são listas começando com "wrb.fr".
  Nessas, o índice 2 é uma STRING com outro JSON (o "interno"), ou null.
- No JSON interno, o texto da resposta fica em interno[4][0][1][0].
- Os blocos são CUMULATIVOS: cada um traz o texto inteiro até ali. Devolva o texto MAIS LONGO encontrado.
- Ignore em silêncio linhas que não são JSON válido, entradas sem o caminho, interno null, índices faltando ou
  tipos errados. Se nada servir, devolva "".""",
    "testes": r'''
import json
from sol import extrair_texto as x
def frame(txt):
    interno = [None, ["c_1","r_1"], None, None, [["rc_1", [txt], [None]]]]
    return json.dumps([["wrb.fr", None, json.dumps(interno)]])
def body(*frames, prefixo=True):
    s = ")]}'\n\n" if prefixo else ""
    for f in frames: s += f"{len(f)}\n{f}\n"
    return s
def cru(*entradas):
    return json.dumps(list(entradas))
def wrb(interno):
    return ["wrb.fr", None, None if interno is None else json.dumps(interno)]
def com_texto(t):
    return [None, None, None, None, [["rc", [t]]]]
casos = [
 (x(body(frame("Olá"))), "Olá"),
 (x(body(frame("Ol"), frame("Olá, mu"), frame("Olá, mundo!"))), "Olá, mundo!"),
 (x(body(frame("abc"), prefixo=False)), "abc"),
 (x(""), ""),
 (x(")]}'\n"), ""),
 (x(body(cru(wrb(None)))), ""),
 (x(body(cru(["di", 123], ["af.httprm", 5]), frame("ok"))), "ok"),
 (x(body("isso nao e json", frame("certo"))), "certo"),
 (x(body(cru(wrb([None, None])), frame("x2"))), "x2"),
 (x(body(frame("linha1\nlinha2"))), "linha1\nlinha2"),
 (x(body(frame("longo texto final"), frame("curto"))), "longo texto final"),
 (x("999\n" + frame("tamanho errado") + "\n"), "tamanho errado"),
 (x(body(cru(wrb(com_texto(42))))), ""),
 (x(body(cru(wrb(com_texto("")), wrb(com_texto("dois"))))), "dois"),
 (x(body(cru("solto", wrb(com_texto("tres"))))), "tres"),
]
''',
}

T_CRON = {
    "nome": "cron_proxima",
    "pedido": """Escreva em Python `proxima_execucao(expr, agora)` para expressões cron de 5 campos
(minuto hora dia_do_mes mes dia_da_semana). Só biblioteca padrão.
- Cada campo aceita: `*`, número, faixa `a-b`, passo `*/n` e `a-b/n`, e listas com vírgula combinando tudo isso
  (ex.: `1,5,10-20/5`).
- Mês aceita nomes jan..dec; dia da semana aceita nomes sun..sat (sem diferenciar maiúsculas). Dia da semana:
  0 e 7 = domingo, 1 = segunda ... 6 = sábado.
- Regra do cron clássico: se dia_do_mes E dia_da_semana forem ambos restritos (nenhum dos dois é `*`), a data
  vale se QUALQUER um dos dois bater (OU). Se um deles for `*`, vale só o outro.
- Retorna o primeiro datetime ESTRITAMENTE depois de `agora` (segundos e microssegundos zerados) que bate.
  Procura até 5 anos à frente; se não existir (ex.: 30 de fevereiro), retorna None.
- Expressão inválida (número de campos errado, valor fora da faixa, passo 0, texto estranho) -> ValueError.
- Tem que ser rápido: cada chamada em bem menos de 1 segundo, mesmo quando a resposta está anos à frente.""",
    "testes": r'''
from datetime import datetime as D
from sol import proxima_execucao as c
def erro(e):
    try:
        c(e, D(2026,1,1)); return "sem erro"
    except ValueError:
        return "ValueError"
casos = [
 (c("*/15 9-17 * * 1-5", D(2026,10,26,8,50)), D(2026,10,26,9,0)),        # segunda
 (c("*/15 9-17 * * 1-5", D(2026,10,26,17,45)), D(2026,10,27,9,0)),
 (c("*/15 9-17 * * 1-5", D(2026,10,30,17,50)), D(2026,11,2,9,0)),        # sexta -> segunda
 (c("0 0 * * *", D(2026,10,27,0,0)), D(2026,10,28,0,0)),                  # estritamente depois
 (c("30 8 * * *", D(2026,10,27,8,29,59,999)), D(2026,10,27,8,30)),
 (c("0 12 29 feb *", D(2026,3,1)), D(2028,2,29,12,0)),
 (c("0 0 30 2 *", D(2026,1,1)), None),
 (c("0 0 13 * fri", D(2026,10,27)), D(2026,10,30,0,0)),                   # OU: sexta vem antes do dia 13
 (c("0 0 13 * 5", D(2026,11,1)), D(2026,11,6,0,0)),
 (c("0 0 1 * *", D(2026,12,15)), D(2027,1,1,0,0)),
 (c("5 4 * * 0", D(2026,10,27)), D(2026,11,1,4,5)),                       # domingo
 (c("5 4 * * 7", D(2026,10,27)), D(2026,11,1,4,5)),
 (c("5 4 * * SUN", D(2026,10,27)), D(2026,11,1,4,5)),
 (c("0 22 * * 1-5/2", D(2026,10,27,23,0)), D(2026,10,28,22,0)),           # seg, qua, sex
 (c("1,5,10-20/5 * * * *", D(2026,10,27,10,6)), D(2026,10,27,10,10)),
 (c("1,5,10-20/5 * * * *", D(2026,10,27,10,20)), D(2026,10,27,11,1)),
 (c("0 0 * JAN,jul *", D(2026,7,31,23,59)), D(2027,1,1,0,0)),
 (c("59 23 31 12 *", D(2026,12,31,23,59)), D(2027,12,31,23,59)),
 (erro("* * * *"), "ValueError"),
 (erro("60 * * * *"), "ValueError"),
 (erro("*/0 * * * *"), "ValueError"),
 (erro("0 0 32 * *"), "ValueError"),
 (erro("0 0 * foo *"), "ValueError"),
 (erro("0 24 * * *"), "ValueError"),
]
''',
}

T_PATCH = {
    "nome": "aplicar_diff",
    "pedido": """Escreva em Python `aplicar_patch(texto, diff)` que aplica um diff unificado (de UM arquivo) a `texto`
e devolve o texto novo. Só biblioteca padrão (não use difflib para aplicar nem chame programas externos).
- O diff pode ter cabeçalhos `--- ` e `+++ ` (ignore) e um ou mais hunks `@@ -a,b +c,d @@ ...`; quando a
  contagem é omitida (`@@ -3 +3 @@`) ela vale 1. `-0,0` significa inserir no começo do arquivo.
- Linhas do hunk: ' ' contexto, '-' removida, '+' adicionada. Uma linha `\\ No newline at end of file` logo depois
  de uma linha indica que AQUELA linha não termina com \\n (no lado antigo se veio após ' '/'-', no novo se veio
  após '+' ou ' ').
- Se o contexto+removidas não bater exatamente na linha indicada, procure o mesmo bloco em outro lugar do arquivo
  (o mais perto da posição esperada, considerando o deslocamento acumulado dos hunks anteriores). Se não achar
  em lugar nenhum, levante ValueError.
- Hunks são aplicados em ordem; os números de linha do diff se referem ao arquivo ORIGINAL.
- Preserve os finais de linha: o texto tem só \\n; o resultado termina ou não com \\n conforme o diff indicar.""",
    "testes": r'''
from sol import aplicar_patch as ap
A = "a\nb\nc\nd\ne\nf\ng\nh\ni\nj\n"
def erro(t, d):
    try:
        ap(t, d); return "sem erro"
    except ValueError:
        return "ValueError"
casos = [
 (ap(A, "--- a/x\n+++ b/x\n@@ -2,3 +2,3 @@\n b\n-c\n+C\n d\n"), A.replace("c\n", "C\n")),
 (ap(A, "@@ -1,2 +1,3 @@\n a\n+a2\n b\n"), "a\na2\n" + A[2:]),
 (ap(A, "@@ -0,0 +1 @@\n+topo\n"), "topo\n" + A),
 (ap(A, "@@ -9,2 +9,3 @@\n i\n j\n+k\n"), A + "k\n"),
 (ap(A, "@@ -2,2 +2,1 @@\n b\n-c\n@@ -8,2 +7,3 @@\n h\n+H\n i\n"), "a\nb\nd\ne\nf\ng\nh\nH\ni\nj\n"),
 (ap(A, "@@ -5,3 +5,3 @@\n c\n-d\n+D\n e\n"), A.replace("d\n", "D\n")),              # deslocado: contexto real está antes
 (ap("x\n" * 3 + A, "@@ -2,3 +2,3 @@\n b\n-c\n+C\n d\n"), "x\n" * 3 + A.replace("c\n", "C\n")),
 (ap("um\ndois", "@@ -2 +2 @@\n-dois\n\\ No newline at end of file\n+dois\n"), "um\ndois\n"),
 (ap("um\ndois\n", "@@ -2 +2 @@\n-dois\n+DOIS\n\\ No newline at end of file\n"), "um\nDOIS"),
 (ap("um\ndois", "@@ -1,2 +1,2 @@\n-um\n+UM\n dois\n\\ No newline at end of file\n"), "UM\ndois"),
 (ap(A, "@@ -3,1 +3,0 @@\n-c\n"), A.replace("c\n", "")),
 (ap("", "@@ -0,0 +1,2 @@\n+novo\n+arquivo\n"), "novo\narquivo\n"),
 (ap("p\nq\np\nq\n", "@@ -3,2 +3,2 @@\n p\n-q\n+Q\n"), "p\nq\np\nQ\n"),
 (erro(A, "@@ -2,2 +2,2 @@\n b\n-zz\n+y\n"), "ValueError"),
 (ap("l1\nl2\nalvo\nl4\nl5\nalvo\nl7\n", "@@ -5,3 +5,3 @@\n l5\n-alvo\n+ALVO\n l7\n"), "l1\nl2\nalvo\nl4\nl5\nALVO\nl7\n"),
]
''',
}

T_CALC = {
    "nome": "calculadora_python",
    "pedido": """Escreva em Python `calcular(expr)` que avalia uma expressão aritmética com EXATAMENTE a mesma semântica do
Python, SEM usar eval, exec, compile, o módulo ast nem bibliotecas de parsing (escreva o tokenizador e o parser).
- Números: inteiros (`42`, `007` é inválido como no Python 3? -> trate `0` sozinho e números sem zero à esquerda;
  `007` deve dar ValueError) e floats (`1.5`, `.5`, `5.`, `2e3`, `1.5E-2`).
- Operadores: + - * / // % ** e parênteses; unários + e - (podem repetir: `--3`).
- Precedência e associatividade iguais às do Python: ** é associativo à direita e liga mais forte que o unário à
  esquerda (-2**2 == -4) mas o expoente pode ter unário (2**-1 == 0.5); * / // % à esquerda.
- Espaços em qualquer lugar entre tokens são ignorados.
- Resultado com o mesmo tipo e valor que o Python daria (int ou float). ZeroDivisionError deve acontecer igual ao
  Python. Expressão malformada (vazia, parêntese sobrando, operador solto, caractere estranho) -> ValueError.""",
    "testes": r'''
from sol import calcular as k
import inspect, sol
def erro(e):
    try:
        k(e); return "sem erro"
    except ValueError:
        return "ValueError"
    except ZeroDivisionError:
        return "ZeroDivisionError"
fonte = inspect.getsource(sol)
casos = [
 (bool(__import__("re").search(r"(?<![\w.])(eval|exec|compile)\s*\(|\bimport ast\b|\bfrom ast\b", fonte)), False),
 (k("1 + 2 * 3"), 7), (k("(1 + 2) * 3"), 9), (k("-2**2"), -4), (k("2**-1"), 0.5), (k("2**3**2"), 512),
 (k("7 // -2"), -4), (k("-7 % 3"), 2), (k("7 % -3"), -2), (k("7 / 2"), 3.5), (k("6 / 3"), 2.0),
 (k("--3"), 3), (k("-+-3"), 3), (k(".5 + 5."), 5.5), (k("2e3"), 2000.0), (k("1.5E-2 * 100"), 1.5),
 (k("2 ** 0.5 ** 2"), 2 ** 0.25),
 (k("  ( ( 4 ) )  "), 4), (k("10 - 4 - 3"), 3), (k("2 * -3 ** 2"), -18), (k("-3 ** -2"), -3 ** -2),
 (k("7.5 // 2"), 3.0), (k("-(2 + 3) * 2"), -10), (k("0"), 0), (k("0.0"), 0.0),
 (erro("1 / 0"), "ZeroDivisionError"), (erro("5 // 0"), "ZeroDivisionError"), (erro("2 % 0"), "ZeroDivisionError"),
 (erro(""), "ValueError"), (erro("(1 + 2"), "ValueError"), (erro("1 + 2)"), "ValueError"), (erro("1 +"), "ValueError"),
 (erro("* 3"), "ValueError"), (erro("3 $ 4"), "ValueError"), (erro("007"), "ValueError"), (erro("1 2"), "ValueError"),
 (erro("2 *** 3"), "ValueError"), (erro("()"), "ValueError"),
]
''',
}

TAREFAS = [T_NUMERO, T_HORARIO, T_PAUSA, T_PARSER, T_CRON, T_PATCH, T_CALC]
if "--dificeis" in sys.argv:
    TAREFAS = [T_CRON, T_PATCH, T_CALC]
    sys.argv.remove("--dificeis")

# Cada elemento de `casos` é avaliado sozinho (via ast): uma exceção num caso não zera os outros.
RODAR = r'''
import ast, json, sys, traceback
sys.path.insert(0, sys.argv[1])
arvore = ast.parse(open(sys.argv[2], encoding="utf-8").read())
listas = [n for n in arvore.body if isinstance(n, (ast.Assign, ast.AugAssign)) and
          getattr(n.targets[0] if isinstance(n, ast.Assign) else n.target, "id", "") == "casos"]
total = sum(len(n.value.elts) for n in listas)
ns, ok, falhas, i = {}, 0, [], 0
for no in arvore.body:
    if no in listas:
        for elt in no.value.elts:
            try:
                obtido, esperado = eval(compile(ast.Expression(elt), "t", "eval"), ns)
                if obtido == esperado and type(obtido) == type(esperado):
                    ok += 1
                else:
                    falhas.append(f"caso {i}: {ast.unparse(elt)[:120]} -> obtido {obtido!r}")
            except Exception as e:
                falhas.append(f"caso {i}: {ast.unparse(elt)[:120]} -> {type(e).__name__}: {e}")
            i += 1
    else:
        try:
            exec(compile(ast.Module([no], []), "t", "exec"), ns)
        except Exception:
            print(json.dumps({"ok": 0, "total": total, "falhas": [traceback.format_exc()[-600:]]})); sys.exit()
print(json.dumps({"ok": ok, "total": total, "falhas": falhas[:8]}, ensure_ascii=False))
'''


def rodar_testes(codigo, tarefa):
    with tempfile.TemporaryDirectory() as d:
        Path(d, "sol.py").write_text(codigo, "utf-8")
        Path(d, "t.py").write_text(tarefa["testes"], "utf-8")
        Path(d, "rodar.py").write_text(RODAR, "utf-8")
        try:
            r = subprocess.run([sys.executable, "-I", "-X", "utf8", "rodar.py", d, "t.py"], cwd=d,
                               capture_output=True, text=True, timeout=30, encoding="utf-8", errors="replace")
            return json.loads(r.stdout.strip().splitlines()[-1])
        except Exception as e:
            return {"ok": 0, "total": -1, "falhas": [f"execução: {e}"]}


def extrair_codigo(txt):
    blocos = re.findall(r"```(?:python|py)?\s*\n(.*?)```", txt or "", re.S)
    return max(blocos, key=len) if blocos else (txt or "")


def chamar(url, modelo, mensagens):
    t0 = time.time()
    try:
        r = requests.post(url, json={"model": modelo, "messages": mensagens, "max_tokens": 8000}, timeout=600,
                          headers={"Authorization": f"Bearer {TOKEN}"})
        if r.status_code != 200:
            return time.time() - t0, f"ERRO HTTP {r.status_code}: {r.text[:200]}"
        return time.time() - t0, r.json()["choices"][0]["message"]["content"] or ""
    except Exception as e:
        return time.time() - t0, f"ERRO: {e}"


SISTEMA = ("Você é um engenheiro Python. Responda SÓ com um bloco ```python``` contendo o módulo completo "
           "(imports + função/classe pedida), sem testes e sem explicação fora do bloco.")


def main():
    filtro = sys.argv[1].lower() if len(sys.argv) > 1 else ""
    res = json.loads(SAIDA.read_text("utf-8")) if SAIDA.exists() else {}
    for nome, url, mid in MODELOS:
        if filtro and filtro not in nome.lower():
            continue
        print(f"\n===== {nome} =====")
        res[nome] = []
        for t in TAREFAS:
            msgs = [{"role": "system", "content": SISTEMA}, {"role": "user", "content": t["pedido"]}]
            hist = []
            for rodada in range(1, RODADAS + 1):
                dt, txt = chamar(url, mid, msgs)
                if txt.startswith("ERRO"):
                    hist.append({"rodada": rodada, "tempo": round(dt, 1), "ok": 0, "total": -1, "falhas": [txt]})
                    print(f"  [{t['nome']:22}] r{rodada} {dt:5.1f}s {txt[:90]}")
                    break
                cod = extrair_codigo(txt)
                tr = rodar_testes(cod, t)
                hist.append({"rodada": rodada, "tempo": round(dt, 1), **tr, "codigo": cod})
                print(f"  [{t['nome']:22}] r{rodada} {dt:5.1f}s  {tr['ok']}/{tr['total']}")
                if tr["ok"] == tr["total"]:
                    break
                msgs += [{"role": "assistant", "content": txt},
                         {"role": "user", "content": "Rodei os testes e falharam:\n" + "\n".join(tr["falhas"])
                          + "\nCorrija e devolva o módulo completo."}]
            res[nome].append({"tarefa": t["nome"], "rodadas": hist})
        SAIDA.write_text(json.dumps(res, ensure_ascii=False, indent=1), "utf-8")
    placar(res)


def placar(res):
    print("\n===== PLACAR (testes passados) =====")
    print(f"  {'modelo':18} {'1ª tentativa':>13} {'com correção':>13} {'tempo total':>12}")
    for nome, tarefas in res.items():
        p1 = sum(max(t["rodadas"][0]["ok"], 0) for t in tarefas)
        pf = sum(max(t["rodadas"][-1]["ok"], 0) for t in tarefas)
        tot = sum(max(t["rodadas"][-1]["total"], 0) or 0 for t in tarefas) or 1
        tt = sum(r["tempo"] for t in tarefas for r in t["rodadas"])
        print(f"  {nome:18} {p1:>6}/{tot:<6} {pf:>6}/{tot:<6} {tt:>10.0f}s")


if __name__ == "__main__":
    main()
