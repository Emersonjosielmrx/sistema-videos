"""Banco de testes das duplas Argon + reserva rodando como agente (Claude Code CLI pelo proxy da VPS).
Cada (modelo, tarefa) roda numa pasta nova; a nota vem de testes ESCONDIDOS rodados fora do agente.
    python hibridos_bench.py                 # tudo que falta no placar
    python hibridos_bench.py hx-plano        # só modelos que contêm o texto
Placar em hibridos_placar.json (gravado a cada rodada; quem já tem nota é pulado)."""
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, r"D:\claude-code-video")
import motor

AQUI = Path(__file__).parent
BASE = AQUI / "hibridos_bench"
PLACAR = AQUI / "hibridos_placar.json"
URL = "http://157.173.207.22:20133"
CFG = Path(r"C:\Users\Haylla\Desktop\Claude VS Code - Trocar Modelo\settings_1_OPUS-4.6_ANTIGRAVITY.json").read_text("utf-8")
CHAVE = re.search(r'"ANTHROPIC_AUTH_TOKEN", "value": "([^"]+)"', CFG).group(1)
PARALELO = int(os.environ.get("PARALELO", "4"))

MODOS = ("socorro", "maos", "plano", "revisor", "erro")
MODELOS = ([f"hx-{m}-kiro" for m in MODOS] + ["gemini-4-argon", "kr/claude-sonnet-4.5"] +
           [f"hx-{m}-gemini" for m in MODOS] + ["agy/gemini-3.8-flash-high", "argon-flash"] +
           [f"hx-{m}-opus" for m in MODOS] + ["antigravity/claude-opus-4-6-thinking"])

# ---------------------------------------------------------------- tarefas
CALC = {
    "calc.py": '''def media_movel(valores, janela):
    """Média móvel simples: uma média para cada posição onde a janela inteira cabe."""
    saida = []
    for i in range(len(valores) - janela):
        saida.append(sum(valores[i:i + janela]) / janela)
    return saida


def mediana(valores):
    v = sorted(valores)
    meio = len(v) // 2
    if len(v) % 2:
        return v[meio]
    return v[meio] + v[meio - 1] / 2
''',
    "test_calc.py": '''from calc import media_movel, mediana

assert media_movel([1, 2, 3, 4], 2) == [1.5, 2.5, 3.5], media_movel([1, 2, 3, 4], 2)
assert mediana([4, 1, 3, 2]) == 2.5, mediana([4, 1, 3, 2])
print("TODOS OS TESTES PASSARAM")
''',
}
CALC_OCULTO = [
    "media_movel([1, 2, 3, 4], 2) == [1.5, 2.5, 3.5]",
    "media_movel([5], 1) == [5.0]",
    "media_movel([1, 2, 3], 3) == [2.0]",
    "media_movel([1, 2], 3) == []",
    "mediana([3, 1, 2]) == 2",
    "mediana([4, 1, 3, 2]) == 2.5",
    "mediana([10, 20]) == 15",
    "mediana([7]) == 7",
]

LOJA = {
    "loja/__init__.py": "",
    "loja/cupons.py": 'CUPONS = {"DEZ": 10, "VINTE": 20}\n',
    "loja/precos.py": '''FRETE = 15.0
FRETE_GRATIS_A_PARTIR = 100.0


def aplicar_desconto(preco, pct):
    """Preço depois de tirar pct por cento, arredondado em 2 casas."""
    return round(preco * pct / 100, 2)
''',
    "loja/carrinho.py": '''from loja.precos import aplicar_desconto


class Carrinho:
    def __init__(self):
        self.itens = []  # (nome, preco, qtd)

    def adicionar(self, nome, preco, qtd=1):
        self.itens.append((nome, preco, qtd))

    def subtotal(self):
        return round(sum(preco for _, preco, _ in self.itens), 2)

    def total(self):
        return self.subtotal()
''',
    "test_loja.py": '''from loja.precos import aplicar_desconto
from loja.carrinho import Carrinho

assert aplicar_desconto(200, 10) == 180.0, aplicar_desconto(200, 10)
k = Carrinho(); k.adicionar("a", 10, 3)
assert k.subtotal() == 30, k.subtotal()
assert k.total() == 45.0, k.total()
k = Carrinho(); k.adicionar("a", 60, 2); k.aplicar_cupom("DEZ")
assert k.total() == 108.0, k.total()
print("TODOS OS TESTES PASSARAM")
''',
}
LOJA_PREP = '''from loja.precos import aplicar_desconto
from loja.carrinho import Carrinho
def c(*itens, cupom=None):
    k = Carrinho()
    for it in itens: k.adicionar(*it)
    if cupom: k.aplicar_cupom(cupom)
    return k
def erro(f):
    try: f()
    except ValueError: return True
    return False
'''
LOJA_OCULTO = [
    "aplicar_desconto(200, 10) == 180.0",
    "aplicar_desconto(19.99, 0) == 19.99",
    "aplicar_desconto(50, 100) == 0.0",
    "c(('a', 10, 3)).subtotal() == 30",
    "c(('a', 10, 3), ('b', 2.5, 2)).subtotal() == 35.0",
    "c(('a', 10, 3)).total() == 45.0",
    "c(('a', 50, 2)).total() == 100.0",
    "c(('a', 60, 2), cupom='DEZ').total() == 108.0",
    "c(('a', 100, 1), cupom='vinte').total() == 95.0",
    "c().total() == 0",
    "erro(lambda: c(('a', 1, 1), cupom='XYZ'))",
    "c(('a', 33.33, 3), cupom='DEZ').total() == 104.99",
]

REL = {
    "videos.csv": "canal,titulo,segundos\nManhwa,A,3000\n manhwa,B,1200\nMANHWA,C,300\nAnime,D,4000\nanime,E,59\nCuriosidades,F,600\n",
    "app/__init__.py": "",
    "app/leitura.py": '''import csv


def ler(caminho):
    with open(caminho, encoding="utf-8") as f:
        return [{"canal": l["canal"], "titulo": l["titulo"], "segundos": int(l["segundos"])} for l in csv.DictReader(f)]
''',
    "app/agrupar.py": '''def por_canal(videos):
    """{canal: {"videos": n, "segundos": total}}"""
    saida = {}
    for v in videos:
        d = saida.setdefault(v["canal"], {"videos": 0, "segundos": 0})
        d["videos"] += 1
        d["segundos"] += v["segundos"]
    return saida
''',
    "app/tempo.py": '''def formatar(seg):
    """H:MM:SS a partir de 1 hora, senão M:SS."""
    if seg >= 3600:
        horas = seg // 3600
        minutos = seg // 60
        return f"{horas}:{minutos:02d}:{seg % 60:02d}"
    return f"{seg // 60}:{seg % 60:02d}"
''',
    "app/util.py": '''def limpar_titulo(t):
    return " ".join(t.split())


def plural(n, palavra):
    return f"{n} {palavra}" + ("" if n == 1 else "s")
''',
    "relatorio.py": '''import sys

from app.agrupar import por_canal
from app.leitura import ler
from app.tempo import formatar


def main():
    dados = por_canal(ler(sys.argv[1]))
    for canal in sorted(dados):
        d = dados[canal]
        print(f"{canal}: {d['videos']} vídeos, {formatar(d['segundos'])}")


if __name__ == "__main__":
    main()
''',
}
REL_PREP = '''import json, os, subprocess, sys
from app.tempo import formatar
from app.agrupar import por_canal
def rodar(*a):
    return subprocess.run([sys.executable, "relatorio.py", "videos.csv", *a], capture_output=True, text=True, encoding="utf-8",
                          errors="replace", env=dict(os.environ, PYTHONIOENCODING="utf-8")).stdout
ESPERADO = {"anime": {"videos": 2, "segundos": 4059}, "curiosidades": {"videos": 1, "segundos": 600},
            "manhwa": {"videos": 3, "segundos": 4500}}
'''
REL_OCULTO = [
    "formatar(59) == '0:59'",
    "formatar(600) == '10:00'",
    "formatar(3600) == '1:00:00'",
    "formatar(3725) == '1:02:05'",
    "formatar(7322) == '2:02:02'",
    "por_canal([{'canal': 'Manhwa', 'segundos': 10}, {'canal': ' manhwa ', 'segundos': 5}]) == {'manhwa': {'videos': 2, 'segundos': 15}}",
    "json.loads(rodar('--json')) == ESPERADO",
    "'manhwa: 3 vídeos, 1:15:00' in rodar()",
    "'anime: 2 vídeos, 1:07:39' in rodar()",
    "rodar().count('manhwa') == 1",
]

TAREFAS = {
    "calc": (CALC, "", CALC_OCULTO,
             "os testes de test_calc.py falham. Rode `python test_calc.py`, leia calc.py, ache e conserte os bugs em calc.py "
             "(não mexa no teste) e rode o teste de novo até imprimir TODOS OS TESTES PASSARAM."),
    "loja": (LOJA, LOJA_PREP, LOJA_OCULTO,
             "fica a loja (pacote loja/). Corrija: o desconto de loja/precos.py está errado e o subtotal ignora a quantidade. "
             "Implemente Carrinho.aplicar_cupom(codigo) usando loja/cupons.py (código sem diferenciar maiúsculas/minúsculas; "
             "código desconhecido levanta ValueError). total() = subtotal com o desconto do cupom (use aplicar_desconto) mais "
             "o FRETE de loja/precos.py quando o valor com desconto for menor que FRETE_GRATIS_A_PARTIR; carrinho vazio tem "
             "total 0. Rode `python test_loja.py` até passar (não mexa no teste)."),
    "relatorio": (REL, REL_PREP, REL_OCULTO,
                  "o `python relatorio.py videos.csv` mostra durações erradas acima de 1 hora e separa o mesmo canal escrito "
                  "com maiúsculas/espaços diferentes (ex.: 'Manhwa' e ' manhwa'). Ache as causas no código (pasta app/) e "
                  "conserte, com os canais em minúsculas e sem espaços nas pontas. Depois acrescente a opção `--json` "
                  "(`python relatorio.py videos.csv --json`) que imprime só o JSON {canal: {\"videos\": n, \"segundos\": s}}. "
                  "Confira rodando os dois comandos."),
}

CONFERIR = '''import ast, json, sys, traceback
sys.path.insert(0, ".")
ns = {}
try:
    exec(compile(PREP, "prep", "exec"), ns)
except Exception:
    print(json.dumps({"ok": 0, "falhas": ["prep: " + traceback.format_exc()[-300:]]})); sys.exit()
ok, falhas = 0, []
for c in CASOS:
    try:
        if eval(c, ns): ok += 1
        else: falhas.append(c)
    except Exception as e:
        falhas.append(c + " -> " + type(e).__name__ + ": " + str(e)[:100])
print(json.dumps({"ok": ok, "falhas": falhas}, ensure_ascii=False))
'''

trava = threading.Lock()


def nota(pasta, prep, casos):
    pre = (f"from calc import *\n" if "calc.py" in os.listdir(pasta) else "") + prep
    cod = f"PREP = {pre!r}\nCASOS = {casos!r}\n" + CONFERIR
    (pasta / "_conferir.py").write_text(cod, "utf-8")
    try:
        p = subprocess.run([sys.executable, "-X", "utf8", "_conferir.py"], cwd=pasta, capture_output=True, text=True,
                           encoding="utf-8", timeout=120)
        r = json.loads(p.stdout.strip().splitlines()[-1])
    except Exception as e:
        r = {"ok": 0, "falhas": [f"conferência quebrou: {e}"]}
    (pasta / "_conferir.py").unlink(missing_ok=True)
    return r


def rodar(modelo, tarefa):
    arquivos, prep, casos, pedido = TAREFAS[tarefa]
    pasta = BASE / tarefa / re.sub(r"[^\w.-]", "_", modelo)
    shutil.rmtree(pasta, ignore_errors=True)
    for nome, txt in arquivos.items():
        (pasta / nome).parent.mkdir(parents=True, exist_ok=True)
        (pasta / nome).write_text(txt, "utf-8")
    env = dict(os.environ, ANTHROPIC_BASE_URL=URL, ANTHROPIC_AUTH_TOKEN=CHAVE, ANTHROPIC_MODEL=modelo,
               ANTHROPIC_DEFAULT_OPUS_MODEL=modelo, ANTHROPIC_DEFAULT_SONNET_MODEL=modelo,
               ANTHROPIC_DEFAULT_HAIKU_MODEL="kr/claude-haiku-4.5", ANTHROPIC_SMALL_FAST_MODEL="kr/claude-haiku-4.5",
               CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1", PYTHONIOENCODING="utf-8")
    env.pop("ANTHROPIC_API_KEY", None)
    cmd = [motor._exe(), "-p", "--output-format", "json", "--max-turns", "30", "--setting-sources", "project",
           "--allowedTools", "Read,Edit,Write,Bash,Glob,Grep", "--disallowedTools", "WebFetch,WebSearch,Agent,Task"]
    t0 = time.time()
    turnos, erro = None, ""
    try:
        p = subprocess.run(cmd, cwd=pasta, env=env, input=f"Na pasta {pasta} {pedido}".encode("utf-8"),
                           capture_output=True, timeout=1200)
        saida = (p.stdout + p.stderr).decode("utf-8", "replace")
        for linha in reversed(saida.strip().splitlines()):
            if linha.startswith("{"):
                j = json.loads(linha)
                turnos = j.get("num_turns")
                if j.get("is_error"):
                    erro = str(j.get("result") or j.get("subtype"))[:200]
                break
        else:
            erro = saida[-200:]
    except subprocess.TimeoutExpired:
        erro = "timeout 20 min"
    tempo = round(time.time() - t0)
    r = nota(pasta, prep, casos)
    linha = {"ok": r["ok"], "total": len(casos), "tempo": tempo, "turnos": turnos, "erro": erro, "falhas": r["falhas"][:5]}
    with trava:
        placar = json.loads(PLACAR.read_text("utf-8")) if PLACAR.exists() else {}
        placar.setdefault(modelo, {})[tarefa] = linha
        PLACAR.write_text(json.dumps(placar, ensure_ascii=False, indent=1), "utf-8")
    print(f"{modelo:38} {tarefa:10} {r['ok']:>2}/{len(casos):<2} {tempo:>5}s turnos={turnos} {erro[:60]}", flush=True)


def resumo():
    placar = json.loads(PLACAR.read_text("utf-8")) if PLACAR.exists() else {}
    linhas = []
    for m, ts in placar.items():
        ok = sum(t["ok"] for t in ts.values())
        tot = sum(t["total"] for t in ts.values())
        tempo = sum(t["tempo"] for t in ts.values())
        linhas.append((-ok, tempo, m, ok, tot, len(ts)))
    print(f"\n{'modelo':38} {'nota':>7} {'tempo':>7} tarefas")
    for _, tempo, m, ok, tot, n in sorted(linhas):
        print(f"{m:38} {ok:>3}/{tot:<3} {tempo:>6}s {n}/{len(TAREFAS)}")


if __name__ == "__main__":
    filtro = sys.argv[1] if len(sys.argv) > 1 else ""
    feito = json.loads(PLACAR.read_text("utf-8")) if PLACAR.exists() else {}
    fila = [(m, t) for m in MODELOS if filtro in m for t in TAREFAS if t not in feito.get(m, {})]
    print(len(fila), "rodadas na fila", flush=True)
    with ThreadPoolExecutor(PARALELO) as ex:
        list(ex.map(lambda a: rodar(*a), fila))
    resumo()
