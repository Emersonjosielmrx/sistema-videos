# -*- coding: utf-8 -*-
"""limitador.py — pausa e retorno INTELIGENTE quando um serviço bate no limite (429/cota/erro).

Por serviço ("tts", "gemini", "youtube", ...): falhas seguidas >= LIMIAR abrem uma pausa.
A pausa é dinâmica: começa em BASE, DOBRA a cada nova rodada de falhas (até MAXIMO) e cai
pela METADE a cada sucesso — então se o limite for curto ela encolhe, se for longo ela cresce.
Estado em workspace/limitador.json (vale entre execuções: a fila respeita a pausa do render).

    limitador.falhou("tts")        # registra falha; devolve segundos de pausa (0 = ainda não)
    limitador.ok("tts")            # registra sucesso (zera falhas, encolhe a pausa)
    limitador.restante("tts")      # segundos que faltam da pausa atual (0 = liberado)
    limitador.esperar("tts")       # dorme o que faltar da pausa
"""
import json
import time
from datetime import datetime
from pathlib import Path

from hp_common import PROJECT_DIR, log

ESTADO = PROJECT_DIR / "workspace" / "limitador.json"
LIMIAR = 3            # falhas seguidas antes de pausar
BASE = 5 * 60         # 1ª pausa: 5 min
MAXIMO = 2 * 60 * 60  # pausa máxima: 2 h


def _ler():
    try:
        return json.loads(ESTADO.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _gravar(d):
    ESTADO.parent.mkdir(parents=True, exist_ok=True)
    ESTADO.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


def _s(d, servico):
    return d.setdefault(servico, {"falhas": 0, "pausa_s": 0, "pausa_ate": 0})


def falhou(servico, motivo=""):
    d = _ler()
    s = _s(d, servico)
    s["falhas"] += 1
    pausa = 0
    if s["falhas"] >= LIMIAR:
        s["pausa_s"] = min(MAXIMO, max(BASE, s["pausa_s"] * 2))
        s["pausa_ate"] = time.time() + s["pausa_s"]
        s["falhas"] = 0
        pausa = s["pausa_s"]
        log(f"  [limitador] {servico}: limite batido ({motivo[:80]}) -> pausa de {pausa // 60} min "
            f"(até {datetime.fromtimestamp(s['pausa_ate']):%H:%M})")
    _gravar(d)
    return pausa


def ok(servico):
    d = _ler()
    s = _s(d, servico)
    if s["falhas"] or s["pausa_s"]:
        s["falhas"] = 0
        s["pausa_s"] = s["pausa_s"] // 2 if s["pausa_s"] > BASE else 0
        _gravar(d)


def restante(servico):
    return max(0, int(_s(_ler(), servico)["pausa_ate"] - time.time()))


def esperar(servico):
    r = restante(servico)
    if r:
        log(f"  [limitador] {servico}: em pausa, aguardando {r // 60} min {r % 60} s...")
        time.sleep(r)
    return r


def resumo():
    agora = time.time()
    return {k: {"pausa_min": round(max(0, v["pausa_ate"] - agora) / 60, 1), "proxima_pausa_min": v["pausa_s"] // 60,
                "falhas_seguidas": v["falhas"]} for k, v in _ler().items()}
