# -*- coding: utf-8 -*-
r"""flow_saldo_real.py — SALDO REAL de cada conta do Flow, lido por HTTP (sem abrir o Flow, sem gastar).

Dona 01/11/2026: "controle de créditos rígido para todos os projetos que usam Veo, como fazemos no Claude web/Genspark/
1min: não ficar tentando contas sem crédito e saber exatamente quanto cada uma tem".

Fonte: o painel de saúde do navegador-sem-navegador (tools\saude.py, roda sozinho a cada poucos minutos) já lê o
GetCredits de TODA conta em TODA máquina (services\veo_flow\saude_flow.py) e grava em
D:\projeto-navegador-sem-navegador\relatorios\saida\saude.json -> "flow": {"<conta>" ou "<conta>@<maquina>": {vivo,
obs "créditos N", quando}}. Antes ninguém usava isso: o creditos_contas só via o saldo quando a conta abria o Flow
para gerar (e quase todas ficavam com "50" velho), e o cron castigava 6 h por "login caiu" contas que estavam logadas
com 1050 créditos em outra máquina.

    from flow_saldo_real import conta
    conta("aulacomia")  -> {"creditos": 1050, "maquinas": {"x200ma": 1050, "acer": 1050}, "quando": "...", "vivo": True}
"""
import datetime
import json
import re
from pathlib import Path

SAUDE = Path(r"D:\projeto-navegador-sem-navegador\relatorios\saida\saude.json")
FRESCO_MIN = 45  # leitura mais velha que isso não vale como "real"
_RE_CRED = re.compile(r"cr[ée]ditos\s+(\d+)")
_cache = {"mtime": None, "dados": {}}


def _ler():
    try:
        mt = SAUDE.stat().st_mtime
    except OSError:
        return {}
    if _cache["mtime"] == mt:
        return _cache["dados"]
    try:
        flow = json.loads(SAUDE.read_text("utf-8")).get("flow") or {}
    except (OSError, ValueError):
        return _cache["dados"]
    agora = datetime.datetime.now()
    out = {}
    for chave, v in flow.items():
        if not isinstance(v, dict):
            continue
        nome, _, maq = chave.partition("@")
        maq = maq or "pc1"
        try:
            quando = datetime.datetime.fromisoformat(str(v.get("quando") or v.get("ultima") or v.get("em")))
        except ValueError:
            continue
        if (agora - quando).total_seconds() > FRESCO_MIN * 60:
            continue
        m = _RE_CRED.search(str(v.get("obs") or ""))
        reg = out.setdefault(nome, {"creditos": None, "maquinas": {}, "mortas": [], "quando": None, "vivo": False})
        if v.get("vivo") and m:
            n = int(m.group(1))
            reg["maquinas"][maq] = n
            reg["vivo"] = True
            reg["creditos"] = max(reg["creditos"] or 0, n)
            reg["quando"] = max(reg["quando"] or "", quando.isoformat(timespec="seconds"))
        elif v.get("vivo") is False:
            reg["mortas"].append(maq)
    _cache.update(mtime=mt, dados=out)
    return out


def conta(sess):
    """Leitura real (fresca) da conta ou None se o painel não tem leitura recente dela."""
    r = _ler().get(sess)
    return r if r and r["vivo"] else None


def creditos(sess):
    r = conta(sess)
    return r["creditos"] if r else None


def todas():
    return {k: v for k, v in _ler().items() if v["vivo"]}


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    t = todas()
    for k, v in sorted(t.items(), key=lambda kv: -(kv[1]["creditos"] or 0)):
        print(f"{k:32} {v['creditos']:>5}  {v['maquinas']}")
    print(f"{len(t)} contas com leitura real; total {sum(v['creditos'] or 0 for v in t.values())} créditos")
