# -*- coding: utf-8 -*-
"""tetos.py — teto de produção EM VIGOR por serviço/conta (config\\tetos.json), com a rampa automática do monitor de
banimento (D33, dona 29/10: "pode subir mas adicione um monitor pra ver se o que colocou a mais leva a banimento").

Só leitura aqui (quem escreve é D:\\projeto-navegador-sem-navegador\\tools\\monitor_banimento.py). Biblioteca padrão.

    import tetos
    tetos.teto("instagram", "jornalcomia", padrao=5)        # Reels/dia desta conta hoje
    tetos.teto("imagens", "seebotsia")                      # imagens/dia desta conta (padrão do serviço se não há linha)
    tetos.teto("imagens", None, chave="<SEGREDO_REMOVIDO>")
    tetos.teto("veo", None, chave="<SEGREDO_REMOVIDO>") / tetos.teto("veo", None, chave="<SEGREDO_REMOVIDO>")
    tetos.imagens_hoje("seebotsia")                         # quantas imagens a conta já gerou hoje (geracoes.jsonl)

Falhou a leitura (arquivo ausente/quebrado) = devolve o `padrao` pedido: a produção nunca para por causa do teto.
"""
import json
import os
import time
from datetime import date
from pathlib import Path

ARQ = Path(__file__).resolve().parents[1] / "config" / "tetos.json"
GERACOES = Path(r"D:\flow-imagens\logs\geracoes.jsonl")
_cache = {"em": 0, "d": None}


def ler(cache_s=30):
    """Conteúdo do tetos.json (cache curto: os pontos que leem rodam em laço)."""
    if _cache["d"] is not None and time.time() - _cache["em"] < cache_s:
        return _cache["d"]
    try:
        d = json.loads(ARQ.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        d = {}
    _cache.update(em=time.time(), d=d)
    return d


def ligado():
    return os.environ.get("TETOS", "1") != "0" and bool(ler())


def linha(servico, conta=None):
    """A linha da rampa desta conta (ou a global do serviço), ou {}."""
    d = ler()
    if conta:
        return ((d.get("contas") or {}).get(servico) or {}).get(str(conta).lower()) or {}
    return (d.get("global") or {}).get(servico) or {}


def teto(servico, conta=None, padrao=None, chave="teto"):
    """Teto em vigor. Linha da conta/global com a chave → esse valor; senão o padrão do serviço no tetos.json; senão
    `padrao`. Para chaves aninhadas (veo.teto_dia, imagens.max_contas_por_pedido) o padrão vem de servicos[..][chave]."""
    if not ligado():
        return padrao
    d = ler()
    v = linha(servico, conta).get(chave)
    if v is not None:
        return v
    s = (d.get("servicos") or {}).get(servico) or {}
    if chave == "teto":
        p = s.get("padrao")
    else:
        sub = s.get(chave)
        p = sub.get("padrao") if isinstance(sub, dict) else sub
    return p if p is not None else padrao


def imagens_hoje(conta, arq=GERACOES):
    """Quantas imagens esta conta gerou hoje (linhas de geracoes.jsonl com arquivo salvo ou via http)."""
    hoje = date.today().isoformat()
    n = 0
    try:
        with open(arq, "rb") as f:  # só a cauda: o arquivo cresce o dia inteiro
            f.seek(0, 2)
            tam = f.tell()
            f.seek(max(0, tam - 400_000))
            cauda = f.read().decode("utf-8", "replace")
    except OSError:
        return 0
    c = str(conta).lower()
    for l in cauda.splitlines():
        if not l.startswith("{") or hoje not in l:
            continue
        try:
            r = json.loads(l)
        except ValueError:
            continue
        if str(r.get("conta", "")).lower() == c and str(r.get("quando", "")).startswith(hoje) \
                and (r.get("arquivos") or r.get("saida") or r.get("via")):
            n += 1
    return n


if __name__ == "__main__":
    import sys
    sv = sys.argv[1] if len(sys.argv) > 1 else "imagens"
    ct = sys.argv[2] if len(sys.argv) > 2 else None
    print(sv, ct, "->", teto(sv, ct), linha(sv, ct))
