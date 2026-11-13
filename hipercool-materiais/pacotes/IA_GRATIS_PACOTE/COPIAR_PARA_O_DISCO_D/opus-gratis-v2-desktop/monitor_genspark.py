# -*- coding: utf-8 -*-
r"""monitor_genspark.py — zelador/painel do pool do Genspark (molde do monitor_sonnet / argon).

Não abre navegador: só lê contas_genspark.json e resume o estado — quantas contas logadas, quantas
com crédito agora, capacidade estimada do dia e quando a cota renova. Pensado para rodar de tempos
em tempos (tarefa agendada) e para o "bom dia".

    python monitor_genspark.py            # resumo legível
    python monitor_genspark.py --status   # JSON (para o Telegram/automção)
    python monitor_genspark.py --faltando  # só lista as contas que ainda precisam de login
"""
import json
import sys
from datetime import datetime
from pathlib import Path

CONTAS = Path(r"D:\opus-gratis\contas_genspark.json")
CREDITOS_DIA = 100
CUSTO_MSG = 3


def ler():
    try:
        return json.loads(CONTAS.read_text(encoding="utf-8"))["contas"]
    except (OSError, ValueError, KeyError):
        return []


def resumo():
    cs = ler()
    hoje = datetime.now().date().isoformat()
    logadas = [c for c in cs if c.get("logado")]
    sem_login = [c for c in cs if not c.get("logado")]
    com_cota = []
    for c in logadas:
        cred = CREDITOS_DIA if c.get("data_cota") != hoje else c.get("creditos", CREDITOS_DIA)
        if cred >= CUSTO_MSG and not c.get("bloqueada"):
            com_cota.append((c["apelido"], cred))
    gasto = sum(c.get("stats", {}).get("creditos_gastos", 0) for c in cs)
    ok = sum(c.get("stats", {}).get("ok", 0) for c in cs)
    err = sum(c.get("stats", {}).get("erros", 0) for c in cs)
    voltas = sorted(c["sem_cota_ate"][:16] for c in cs if c.get("sem_cota_ate"))
    return {
        "agora": datetime.now().isoformat(timespec="minutes"),
        "total": len(cs),
        "logadas": len(logadas),
        "sem_login": len(sem_login),
        "com_cota_agora": len(com_cota),
        "capacidade_restante_hoje": sum(cred // CUSTO_MSG for _, cred in com_cota),
        "mensagens_ok": ok, "erros": err, "creditos_gastos_total": gasto,
        "proxima_renovacao": voltas[0] if voltas else None,
        "precisam_login": [c["apelido"] for c in sem_login],
    }


def main(a):
    if "--faltando" in a:
        for ap in resumo()["precisam_login"]:
            print(ap)
        return
    r = resumo()
    if "--status" in a:
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return
    print(f"Genspark pool — {r['agora']}")
    print(f"  contas: {r['total']} (logadas {r['logadas']}, sem login {r['sem_login']})")
    print(f"  com crédito agora: {r['com_cota_agora']}  →  ~{r['capacidade_restante_hoje']} mensagens ainda hoje")
    print(f"  uso acumulado: {r['mensagens_ok']} ok, {r['erros']} erros, {r['creditos_gastos_total']} créditos gastos")
    if r["proxima_renovacao"]:
        print(f"  próxima renovação de cota: {r['proxima_renovacao']}")
    if r["sem_login"]:
        print(f"  ⚠ {r['sem_login']} contas ainda sem login no Genspark → python genspark.py login")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main(sys.argv[1:])
