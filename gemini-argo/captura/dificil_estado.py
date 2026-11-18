"""17/11 (dona): tarefa DIFÍCIL e REAL do projeto de vídeo — recapd colab/postar_longos.py, _gravar_estado.
O mesmo defeito (rodada que já estava rodando grava a cópia antiga do estado por cima) voltou 4 vezes (02/11, 13/11,
14/11 15h20, 16/11) e foi remendado em camadas. O modelo recebe a versão de 03/11 + os 4 relatos de incidente e tem
que consertar tudo. Nota = testes escondidos que simulam cada incidente. Opus 5.5 = referência.
    python dificil_estado.py --ref          valida: versão 03/11 falha, versão de produção (17/11) passa
    python dificil_estado.py MODELO [...]   roda os modelos (um por vez)"""
import shutil
import sys
from pathlib import Path

import hibridos_bench as hb

ESTADO_0311 = '''"""Trecho de colab/postar_longos.py (postagem dos longos). Várias rodadas podem rodar ao mesmo tempo (tarefa do
Windows a cada hora + execução manual); cada uma lê o estado no começo, trabalha horas e grava no fim."""
import json
import threading
from pathlib import Path

BASE = Path(__file__).parent
ESTADO = BASE / "longos_postados.json"
FICHAS = BASE / "fichas"  # uma pasta por longo (ficha); o bipar_palavrao.py cria FICHAS/<nome>/SEM_PALAVRAO.txt
_TRAVA_EST = threading.RLock()


def _estado():
    try:
        return json.loads(ESTADO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"postados": [], "reprovados": []}


def _gravar_estado(est):
    """03/11: grava JUNTANDO com o que está no arquivo. Em 02/11 duas rodadas rodaram juntas e a que terminou depois
    gravou a lista que tinha lido de manhã por cima: o post do yKfgs no Fio da Meada sumiu e ele voltou pra fila (quase
    saiu em 3 canais — regra: vídeo único por canal). Postado/reprovado/corte que existir no arquivo nunca se perde."""
    with _TRAVA_EST:
        _gravar_estado_trancado(est)


def _gravar_estado_trancado(est):
    disco = _estado()
    vistos = {(p.get("nome"), p.get("url")) for p in est.get("postados", [])}
    est["postados"] = est.get("postados", []) + [p for p in disco.get("postados", [])
                                                 if (p.get("nome"), p.get("url")) not in vistos]
    est["reprovados"] = sorted(set(est.get("reprovados", [])) | set(disco.get("reprovados", [])))
    est["cortes_postados"] = sorted(set(est.get("cortes_postados", [])) | set(disco.get("cortes_postados", [])))
    ESTADO.write_text(json.dumps(est, ensure_ascii=False, indent=1), encoding="utf-8")
'''

INCIDENTES = '''# Incidentes reais com o estado dos longos (longos_postados.json) — todos depois do conserto de 03/11

Formato do estado: {"postados": [{"nome", "url", "titulo", "canal"}], "reprovados": [nomes],
"cortes_postados": [nomes], "presos": {nome: {"status": "enviando"|"erro", ...}}, "presos_soltar": [nomes]}.
Várias rodadas rodam juntas; cada uma lê no começo e grava (com _gravar_estado) quando termina um envio, horas depois.

1. 13/11 20h45 — Parte 4 do Medieval VOLTOU a "reprovada" sozinha. Ela estava reprovada por palavrão; o
   bipar_palavrao.py bipou o áudio, criou fichas/<nome>/SEM_PALAVRAO.txt e tirou o nome dos "reprovados" no arquivo.
   A rodada que já estava rodando (leu antes, com ela reprovada) gravou no fim e ela voltou pra lista. Regra: ficha
   com SEM_PALAVRAO.txt está liberada e nunca pode ficar em "reprovados".
2. 14/11 — "presos" (longo cujo envio travou/está em andamento) sumiam: a rodada antiga gravava o "presos" que tinha
   lido de manhã por cima do que outra rodada marcou depois. Preso marcado por qualquer rodada não pode sumir por isso.
3. 14/11 15h20 — Título do jardineiro: o título real "Por que a academia inteira tremeu..." foi corrigido à mão no
   arquivo (antes era a nota "(reposto 03/11 do uploads_ledger...)"). A rodada que já estava rodando gravou e o
   título voltou a ser a nota. Título que começa com "(" é NOTA provisória: perde para um título de verdade do
   arquivo para o mesmo url. Título de verdade novo (da rodada) continua valendo.
4. 16/11 — Era preciso SOLTAR um preso de propósito quando o envio dele terminou (marca "enviando" que ficou para
   trás). Como "presos" nunca pode sumir (item 2), a rodada põe o nome em est["presos_soltar"]; ao gravar, cada
   nome de presos_soltar (da rodada ou do arquivo) sai de "presos" SÓ se lá o status for "enviando" (preso com
   "erro" nunca é solto por aqui). "presos_soltar" não fica gravado no arquivo depois de aplicado.

Tudo do conserto de 03/11 continua valendo: postado/reprovado/corte que existe no arquivo nunca se perde, e postado
não duplica (mesmo nome+url).
'''

PEDIDO = ("o postar.py tem a gravação do estado dos longos (_gravar_estado / _gravar_estado_trancado) e o arquivo "
          "INCIDENTES.md descreve 4 defeitos REAIS que aconteceram em produção depois do último conserto. Conserte "
          "postar.py para que nenhum dos 4 aconteça mais, sem perder o que o conserto de 03/11 já garante. Mantenha os "
          "nomes das funções e das constantes (BASE, ESTADO, FICHAS). Escreva testes que simulem duas rodadas "
          "concorrentes para cada incidente e rode-os até passar. Não use internet.")

PREP = r'''import json, os, tempfile, shutil
from pathlib import Path
import postar as P
_tmp = Path(tempfile.mkdtemp())
P.ESTADO = _tmp / "longos_postados.json"
P.FICHAS = _tmp / "fichas"
P.FICHAS.mkdir()
def disco(d=None):
    if d is not None: P.ESTADO.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    return json.loads(P.ESTADO.read_text(encoding="utf-8"))
def liberar(n):
    (P.FICHAS / n).mkdir(exist_ok=True); (P.FICHAS / n / "SEM_PALAVRAO.txt").write_text("ok")
def grava(est):
    P._gravar_estado(json.loads(json.dumps(est))); return disco()
def cenario_postado():
    disco({"postados": [{"nome": "a", "url": "u1"}, {"nome": "b", "url": "u2"}], "reprovados": ["r1"], "cortes_postados": ["c1"]})
    return grava({"postados": [{"nome": "a", "url": "u1"}, {"nome": "c", "url": "u3"}], "reprovados": ["r2"], "cortes_postados": []})
def cenario_palavrao():
    disco({"postados": [], "reprovados": ["med4", "x"]})
    liberar("med4"); disco({"postados": [], "reprovados": ["x"]})
    return grava({"postados": [], "reprovados": ["med4", "x", "novo"]})
def cenario_presos():
    disco({"postados": [], "reprovados": [], "presos": {"p1": {"status": "erro"}, "p2": {"status": "enviando"}}})
    return grava({"postados": [], "reprovados": [], "presos": {"p3": {"status": "enviando"}}})
def cenario_titulo():
    disco({"postados": [{"nome": "jard", "url": "lzt", "titulo": "Por que a academia inteira tremeu"},
                        {"nome": "o", "url": "u9", "titulo": "(nota velha)"}], "reprovados": []})
    return grava({"postados": [{"nome": "jard", "url": "lzt", "titulo": "(reposto 03/11 do uploads_ledger)"},
                               {"nome": "o", "url": "u9", "titulo": "Titulo novo da rodada"},
                               {"nome": "z", "url": "u7", "titulo": "(so nota)"}], "reprovados": []})
def cenario_soltar():
    disco({"postados": [], "reprovados": [], "presos": {"e1": {"status": "enviando"}, "e2": {"status": "erro"},
                                                         "e3": {"status": "enviando"}}, "presos_soltar": ["e3"]})
    return grava({"postados": [], "reprovados": [], "presos": {"e1": {"status": "enviando"}, "e2": {"status": "erro"}},
                  "presos_soltar": ["e1", "e2"]})
def tit(d, url): return next(p.get("titulo") for p in d["postados"] if p["url"] == url)
'''

CASOS = [
    # conserto de 03/11 (continua valendo)
    "sorted(p['nome'] for p in cenario_postado()['postados']) == ['a', 'b', 'c']",
    "sorted(cenario_postado()['reprovados']) == ['r1', 'r2']",
    "cenario_postado()['cortes_postados'] == ['c1']",
    "len([p for p in cenario_postado()['postados'] if p['nome'] == 'a']) == 1",
    # incidente 1: palavrão liberado não volta
    "'med4' not in cenario_palavrao()['reprovados']",
    "sorted(cenario_palavrao()['reprovados']) == ['novo', 'x']",
    # incidente 2: presos não somem
    "sorted(cenario_presos()['presos']) == ['p1', 'p2', 'p3']",
    "cenario_presos()['presos']['p1'] == {'status': 'erro'}",
    # incidente 3: título de nota perde pro título real
    "tit(cenario_titulo(), 'lzt') == 'Por que a academia inteira tremeu'",
    "tit(cenario_titulo(), 'u9') == 'Titulo novo da rodada'",
    "tit(cenario_titulo(), 'u7') == '(so nota)'",
    # incidente 4: soltar preso só se 'enviando'
    "'e1' not in cenario_soltar()['presos']",
    "'e3' not in cenario_soltar()['presos']",
    "cenario_soltar()['presos'].get('e2') == {'status': 'erro'}",
    "'presos_soltar' not in cenario_soltar() or cenario_soltar()['presos_soltar'] == []",
    # tudo junto, 2 gravações seguidas (a 2ª rodada é a mais antiga)
    "(disco({'postados': [], 'reprovados': ['m'], 'presos': {'k': {'status': 'enviando'}}}), liberar('m'), "
    "grava({'postados': [{'nome': 'n', 'url': 'un', 'titulo': 'T'}], 'reprovados': [], 'presos': {}, 'presos_soltar': ['k']}), "
    "grava({'postados': [{'nome': 'n', 'url': 'un', 'titulo': '(nota)'}], 'reprovados': ['m'], 'presos': {'k': {'status': 'enviando'}}}))[-1] "
    "and (lambda d: d['reprovados'] == [] and tit(d, 'un') == 'T' and len(d['postados']) == 1)(disco())",
]

# referência = o código de PRODUÇÃO de hoje (17/11), que passou pelos 4 incidentes
REF = ESTADO_0311.replace('''    est["cortes_postados"] = sorted(set(est.get("cortes_postados", [])) | set(disco.get("cortes_postados", [])))
    ESTADO.write_text''', '''    est["reprovados"] = [n for n in est["reprovados"] if not (FICHAS / n / "SEM_PALAVRAO.txt").exists()]
    est["cortes_postados"] = sorted(set(est.get("cortes_postados", [])) | set(disco.get("cortes_postados", [])))
    est["presos"] = {**disco.get("presos", {}), **est.get("presos", {})}
    for n in set(est.pop("presos_soltar", []) + disco.get("presos_soltar", [])):
        if est["presos"].get(n, {}).get("status") == "enviando":
            est["presos"].pop(n, None)
    tit_disco = {p.get("url"): p.get("titulo") for p in disco.get("postados", [])
                 if p.get("titulo") and not str(p["titulo"]).startswith("(")}
    for p in est["postados"]:
        if str(p.get("titulo") or "").startswith("(") and tit_disco.get(p.get("url")):
            p["titulo"] = tit_disco[p["url"]]
    ESTADO.write_text''')

TAREFA = {"estado_longos": ({"postar.py": ESTADO_0311, "INCIDENTES.md": INCIDENTES}, PREP, CASOS, PEDIDO)}


def conferir_ref():
    for nome, txt in (("03/11", ESTADO_0311), ("producao", REF)):
        p = Path("_val_est") / nome.replace("/", "")
        shutil.rmtree(p, ignore_errors=True)
        p.mkdir(parents=True)
        (p / "postar.py").write_text(txt, "utf-8")
        r = hb.nota(p, PREP, CASOS)
        print(nome, f"{r['ok']}/{len(CASOS)}", *[f[:160] for f in r["falhas"][:8]], sep="\n  ")
    shutil.rmtree("_val_est", ignore_errors=True)


if __name__ == "__main__":
    hb.TAREFAS = TAREFA
    hb.PLACAR = Path(__file__).with_name("dificil_placar.json")
    hb.BASE = Path(__file__).with_name("dificil")
    if sys.argv[1:] == ["--ref"]:
        conferir_ref()
    else:
        for m in sys.argv[1:]:
            hb.rodar(m, "estado_longos")
