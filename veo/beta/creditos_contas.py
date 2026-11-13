# -*- coding: utf-8 -*-
"""creditos_contas.py — GERENCIAMENTO DE CREDITOS por conta do Flow (dona, 23/10/2026: "tem que ter um controle de
creditos das contas, um gerenciamento; se a conta esta com menos de 20 creditos, ja nao faz mais naquele dia, passa
pra outra").

Estado em logs\\creditos_contas.json, por conta:
  saldo       ultimo saldo conhecido (lido no Flow pelo worker, ou estimado: lido - custo de cada video que saiu)
  lido_em     quando o saldo foi LIDO no Flow (a estimativa nao mexe nisto)
  renova_em   quando volta (abaixo do minimo / sem credito: proxima meia-noite + 5 min, mesma regra do cron)
  gasto_hoje / videos_hoje / dia   o que a conta gastou no dia
De onde vem o saldo: o gera_auto ja le o menu da conta toda vez que abre o Flow (creditos.ler_saldo_creditos) e
imprime "[CREDITOS] saldo lido no menu de conta: N" — o cron le essa linha da saida (nao abre nada a mais, nao gasta).

Regras:
  - saldo < VEO_CREDITO_MINIMO (20) = fora ate renova_em; o cron passa pra proxima conta (na mesma maquina);
  - escolha dentro da maquina: mais credito primeiro; empate -> a que renova antes; saldo desconhecido vem depois das
    que tem credito conhecido (na 1a vez que for usada o saldo e lido);
  - custo de 1 video: VEO_CUSTO_VIDEO (20 = "Veo 3.1 - Fast", visto em 24/08).
"""
import datetime
import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
ARQ = os.path.join(BASE, "logs", "creditos_contas.json")
MINIMO = int(os.environ.get("VEO_CREDITO_MINIMO", "20"))
CUSTO = int(os.environ.get("VEO_CUSTO_VIDEO", "20"))
_RE_LIDO = re.compile(r"saldo lido no menu de conta:\s*(\d+)")
_RE_INSUF = re.compile(r"saldo insuficiente \((?:creditos=)?(\d+)")


def _agora():
    return datetime.datetime.now()


def ler():
    try:
        with open(ARQ, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _gravar(d):
    try:
        tmp = ARQ + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
        os.replace(tmp, ARQ)
    except Exception:
        pass


def _proxima_renovacao(agora=None):
    agora = agora or _agora()
    return ((agora + datetime.timedelta(days=1)).replace(hour=0, minute=5, second=0, microsecond=0)
            ).isoformat(timespec="seconds")


def _conta(d, sess, agora):
    c = d.setdefault(sess, {})
    hoje = agora.date().isoformat()
    if c.get("dia") != hoje:
        c.update(dia=hoje, gasto_hoje=0, videos_hoje=0)
    return c


def _renovou(c, agora):
    rv = c.get("renova_em")
    try:
        return bool(rv) and agora >= datetime.datetime.fromisoformat(rv)
    except Exception:
        return True


def anotar_uso(sess, saida, gerou, sem_credito=False, agora=None):
    """Depois de cada chamada do gera_auto: grava o saldo lido, desconta o custo se o video saiu e poe fora quem ficou
    abaixo do minimo. Devolve o registro da conta."""
    agora = agora or _agora()
    d = ler()
    c = _conta(d, sess, agora)
    lidos = _RE_LIDO.findall(saida or "") or _RE_INSUF.findall(saida or "")
    if lidos:
        c["saldo"] = int(lidos[-1])
        c["lido_em"] = agora.isoformat(timespec="seconds")
        c.pop("estimado", None)
    if gerou:
        c["gasto_hoje"] = c.get("gasto_hoje", 0) + CUSTO
        c["videos_hoje"] = c.get("videos_hoje", 0) + 1
        if c.get("saldo") is not None:
            c["saldo"] = max(0, c["saldo"] - CUSTO)
            c["estimado"] = True
    if sem_credito and not lidos:
        c["saldo"] = 0
    if c.get("saldo") is not None and c["saldo"] < MINIMO:
        c["renova_em"] = c.get("renova_em") if (c.get("renova_em") and not _renovou(c, agora)) \
            else _proxima_renovacao(agora)
    else:
        c.pop("renova_em", None)
    d[sess] = c
    _gravar(d)
    return c


def real(sess, maquinas=None):
    """01/11 (dona: "controle de créditos rígido"): saldo REAL lido por HTTP pelo painel de saúde (flow_saldo_real).
    maquinas = só o saldo nessas máquinas (a mesma conta pode ter saldo diferente em cada máquina). None = sem leitura."""
    try:
        import flow_saldo_real
        r = flow_saldo_real.conta(sess)
    except Exception:  # noqa: BLE001
        return None
    if not r:
        return None
    if maquinas:
        vals = [v for m, v in r["maquinas"].items() if m in set(maquinas)]
        return max(vals) if vals else None
    return r["creditos"]


def fora(sess, agora=None, d=None):
    """Motivo se a conta esta abaixo do minimo e ainda nao renovou, senao None. Passou da renovacao: libera (saldo
    vira desconhecido ate o proximo uso ler de novo). 01/11: leitura REAL fresca manda (mais e menos que o minimo)."""
    agora = agora or _agora()
    r = real(sess)
    if r is not None:
        return None if r >= MINIMO else f"{r} creditos reais (< {MINIMO})"
    d = ler() if d is None else d
    c = d.get(sess) or {}
    if c.get("saldo") is None or c["saldo"] >= MINIMO:
        return None
    if _renovou(c, agora):
        return None
    return f"{c['saldo']} creditos (< {MINIMO}) ate {str(c.get('renova_em'))[5:16]}"


def ordenar(sessoes, agora=None, maquinas=None):
    """Mais credito primeiro; empate -> renova antes; desconhecido depois dos conhecidos (ordem de entrada mantida,
    quem chama ja embaralhou).
    01/11 (dona: "priorizamos usar as que têm muito primeiro, com a devida rotação para não estourar nenhuma; quando
    todas tiverem só os 50 do dia, aumentamos a rotação"): saldo REAL (nas máquinas da etapa) em faixas de 100 —
    contas da mesma faixa revezam pela que gerou MENOS hoje; as de 1000+ vêm antes, e quando só sobram as de ~50 do
    dia todas ficam na mesma faixa e o rodízio passa a ser só pelo uso do dia."""
    agora = agora or _agora()
    d = ler()

    def chave(s):
        c = d.get(s["session"]) or {}
        usos = c.get("videos_hoje", 0) if c.get("dia") == agora.date().isoformat() else 0
        r = real(s["session"], maquinas)
        if r is not None:
            return (0, -(r // 100), usos, -r)
        saldo = c.get("saldo")
        if saldo is not None and _renovou(c, agora) and saldo < MINIMO:
            saldo = None  # renovou: nao sabe ainda
        rv = c.get("renova_em") or "9999"
        return (1, -(saldo // 100), usos, rv) if saldo is not None else (2, 0, usos, rv)
    return sorted(sessoes, key=chave)


def linha_resumo(sessoes, agora=None):
    """Uma linha p/ o resumo diario: saldo por conta conhecida e quantas ficaram fora."""
    agora = agora or _agora()
    d = ler()
    partes, n_fora, total = [], 0, 0
    for s in sessoes:
        c = d.get(s["session"]) or {}
        if c.get("saldo") is None:
            continue
        if fora(s["session"], agora, d):
            n_fora += 1
        total += c["saldo"]
        partes.append(f"{s['session']}={c['saldo']}{'~' if c.get('estimado') else ''}")
    desconhecidas = len(sessoes) - len(partes)
    return (f"Creditos Veo: {total} conhecidos em {len(partes)} contas ({n_fora} fora, < {MINIMO}); "
            f"{desconhecidas} sem leitura ainda | " + ", ".join(partes))


def resumo_do_dia(sessoes, enviar, agora=None):
    """Manda a linha 1x por dia (no 1o ciclo do dia) pelo resumo de avisos (nao e importante)."""
    agora = agora or _agora()
    d = ler()
    hoje = agora.date().isoformat()
    if d.get("_resumo_dia") == hoje:
        return None
    if not any((d.get(s["session"]) or {}).get("saldo") is not None for s in sessoes):
        return None  # nada lido ainda: espera o 1o saldo (nao manda linha vazia)
    linha = linha_resumo(sessoes, agora)
    try:
        enviar(linha)
    except Exception:
        return None
    d = ler()
    d["_resumo_dia"] = hoje
    _gravar(d)
    return linha
