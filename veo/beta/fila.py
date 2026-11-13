# -*- coding: utf-8 -*-
"""
========================================================================
fila.py  —  Buffer de prompts prontos (nao desperdicar trabalho do Gemini)
========================================================================

PROBLEMA que resolve: antes, cada ciclo chamava o Gemini pra criar o prompt
(tema+fala+cenario), e SE a geracao do video falhava (timeout/crash), esse
prompt era JOGADO FORA — no ciclo seguinte o Gemini era chamado do zero.
Retrabalho de token e tempo.

SOLUCAO: uma fila persistente (logs/prompt_queue.json) de prompts JA PRONTOS.
- Quando um video falha, o prompt volta pra fila (re-enfileira) em vez de sumir.
- Quando a maquina esta livre, o bot enche a fila em lote (so a fase LLM,
  barata, sem abrir navegador). Assim quando a producao volta, ja tem trabalho
  pronto sem esperar o Gemini.

Cada item da fila = o dict de montar_prompt (prompt/fala/cenario/fonte/score/
iteracoes) + a foto ja escolhida + o canal. A sessao NAO entra: e re-escolhida
no consumo (nunca reusar a conta que falhou).
"""
import os, json, datetime

BASE = os.path.dirname(os.path.abspath(__file__))
QUEUE_FILE = os.path.join(BASE, "logs", "prompt_queue.json")

try:
    import config as _cfg
    FILA_MIN = getattr(_cfg, "FILA_MIN", 5)    # abaixo disso, encher em lote
    FILA_ALVO = getattr(_cfg, "FILA_ALVO", 10) # ate quanto encher
    FILA_MAX = getattr(_cfg, "FILA_MAX", 30)   # teto duro (nao inflar infinito)
except Exception:
    FILA_MIN, FILA_ALVO, FILA_MAX = 5, 10, 30


def _load():
    if not os.path.exists(QUEUE_FILE):
        return []
    try:
        with open(QUEUE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save(items):
    os.makedirs(os.path.dirname(QUEUE_FILE), exist_ok=True)
    tmp = QUEUE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    os.replace(tmp, QUEUE_FILE)  # escrita atomica (nao corrompe se cair no meio)


def tamanho():
    return len(_load())


def precisa_encher():
    """True se a fila esta abaixo do minimo (vale gerar prompts em lote)."""
    return tamanho() < FILA_MIN


def quanto_encher():
    """Quantos prompts faltam pra chegar no alvo (0 se ja cheia)."""
    return max(0, FILA_ALVO - tamanho())


def enfileirar(formula, foto, canal, prioridade=False):
    """Adiciona um prompt pronto na fila. prioridade=True poe na frente
    (usado quando um video falhou e queremos reaproveitar logo)."""
    items = _load()
    if len(items) >= FILA_MAX:
        return False
    item = {
        "formula": formula,   # dict de montar_prompt (prompt/fala/cenario/fonte/score/iteracoes)
        "foto": foto,
        "canal": canal,
        "enfileirado_em": datetime.datetime.now().isoformat(timespec="seconds"),
        "tentativas": formula.get("_tentativas_fila", 0) if isinstance(formula, dict) else 0,
    }
    if prioridade:
        items.insert(0, item)
    else:
        items.append(item)
    _save(items)
    return True


def desenfileirar():
    """Tira o proximo prompt da fila (FIFO). Retorna o item ou None se vazia."""
    items = _load()
    if not items:
        return None
    item = items.pop(0)
    _save(items)
    return item


def reenfileirar_no_erro(item, max_retentativas=3):
    """Um item consumido cuja geracao de video FALHOU volta pra fila (frente),
    ate um teto de retentativas (pra nao ficar preso num prompt ruim eterno)."""
    if not item:
        return False
    t = item.get("tentativas", 0) + 1
    if t > max_retentativas:
        return False  # descarta: ja tentou demais
    item["tentativas"] = t
    items = _load()
    items.insert(0, item)
    _save(items)
    return True


if __name__ == "__main__":
    print(f"fila: {tamanho()} item(s) | min={FILA_MIN} alvo={FILA_ALVO} max={FILA_MAX}")
    print(f"precisa encher? {precisa_encher()} | faltam {quanto_encher()} pro alvo")
