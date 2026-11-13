# -*- coding: utf-8 -*-
r"""base_consertos.py — a base dos problemas já vistos e resolvidos (dono 21/10, frente E do painel: "base de conhecimento
dos problemas resolvidos, o vigia aprende; RAG leve").

Sem modelo de embedding: cada caso vira um registro (problema, causa, o que foi feito, estado, onde está a conversa) e a
busca é por palavras em comum (BM25 simples, sem acento). Quem consulta: a IA do painel (pergunta e conserto) e o vigia
geral, que recebem no prompt os casos mais parecidos já vistos — pra não refazer investigação nem repetir conserto.

Fontes, lidas na hora (nada copiado à mão; a base cresce sozinha):
  - IA do painel: estado\painel_ia\<id>.json — conserto aplicado (CONSERTEI, não desfeito) e proposta "nada a fazer" (OK)
  - diários dos vigias: D:\video-fila\VIGIA_DIARIO.md e D:\hipercool-videos\docs\VIGIA_DIARIO.md (blocos "## "),
    só os RESOLVIDO e NADA A FAZER (os "PRECISA REVISÃO" não ensinam: ninguém fechou)

    python base_consertos.py buscar "texto do problema"   os parecidos, com a nota
    python base_consertos.py listar                       tudo o que a base tem
"""
import json
import math
import re
import sys
import unicodedata
from collections import Counter
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
PASTA_IA = BASE / "estado" / "painel_ia"
DIARIOS = (("vigia geral", BASE / "VIGIA_DIARIO.md", BASE / "logs"),
           ("vigia hipercool", Path(r"D:\hipercool-videos\docs\VIGIA_DIARIO.md"), Path(r"D:\hipercool-videos\logs")))
PARAR = set("""a o e de da do das dos em no na nos nas um uma uns umas que se por para pra com sem ao aos as os
    ser esta estao isso esse essa este estes essas esses nao sim mais menos ja ou como quando onde qual quais foi
    era tem ter fica ficou vai pelo pela pelos pelas sobre entre depois antes agora hoje ainda muito pouco nada tudo
    todo toda todos todas cada mesmo outra outro outros outras porque mas tambem the of and to in is for on""".split())
K1, B = 1.2, 0.75


def _sem_acento(t):
    t = unicodedata.normalize("NFKD", str(t or "").lower())
    return "".join(c for c in t if not unicodedata.combining(c))


def _tokens(t):
    return [w for w in re.findall(r"[a-z0-9_]{3,}", _sem_acento(t)) if w not in PARAR]


def _quando(hora):
    """'20261022_0715' -> '22/10 07:15' (o resto fica como veio)."""
    m = re.fullmatch(r"(\d{4})(\d\d)(\d\d)_(\d\d)(\d\d)", hora or "")
    return f"{m[3]}/{m[2]} {m[4]}:{m[5]}" if m else str(hora or "")[:16]


def _trecho(texto, rotulo, ate=("PLANO", "RISCO", "STATUS"), limite=500):
    """O texto depois de 'CAUSA:' (ou outro rótulo) até o próximo rótulo, numa linha só."""
    m = re.search(rf"{rotulo}\**\s*:?\**\s*(.+?)(?=\n\s*\**\s*\d?\.?\s*\**(?:{'|'.join(ate)})\b|\Z)", texto or "", re.S | re.I)
    return " ".join(m.group(1).split())[:limite] if m else ""


def _do_painel():
    jobs = {}
    for p in PASTA_IA.glob("*_*_*.json"):
        try:
            j = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        jobs[j.get("id")] = j
    out = []
    for j in jobs.values():
        st = j.get("status_ia")
        if j.get("tipo") == "aplicar" and st == "CONSERTEI" and not j.get("desfeito_em"):
            pai = jobs.get(j.get("pai")) or {}
            causa = _trecho(pai.get("resposta"), "CAUSA") or (pai.get("detalhe") or "")
            arqs = [Path(a).name for a in (j.get("manifesto") or {})]
            feito = (j.get("detalhe") or "") + (f" (arquivos: {', '.join(arqs)})" if arqs else "")
            estado, problema, contexto = "RESOLVIDO", pai.get("pedido") or j.get("pedido"), pai.get("contexto") or ""
        elif j.get("tipo") == "propor" and st == "OK":
            causa, feito = _trecho(j.get("resposta"), "CAUSA") or (j.get("detalhe") or ""), "nada a mudar: " + (j.get("detalhe") or "")
            estado, problema, contexto = "NADA A FAZER", j.get("pedido"), j.get("contexto") or ""
        else:
            continue
        out.append({"id": j["id"], "fonte": "IA do painel", "quando": (j.get("fim") or j.get("criado") or "")[:16].replace("T", " "),
                    "projeto": j.get("projeto"), "problema": str(problema or "")[:400], "estado": estado,
                    "resumo": " ".join(f"{causa} -> {feito}".split())[:600], "conversa": f"painel:{j['id']}",
                    "busca": f"{problema} {contexto[:1500]} {causa} {feito}"})
    return out


def _dos_diarios():
    out = []
    for nome, arq, logs in DIARIOS:
        try:
            texto = arq.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for bloco in re.split(r"\n(?=## )", texto):
            m = re.match(r"## (\S+)\s+[—-]\s+(.+)", bloco.strip())
            if not m:
                continue
            est = re.search(r"Estado\**\s*:?\**\s*([^\n]+)", bloco)
            e = _sem_acento(est.group(1) if est else "").upper()
            if "NADA" in e:
                estado = "NADA A FAZER"
            elif "RESOLVID" in e:
                estado = "RESOLVIDO"
            else:
                continue
            hora = m.group(1)
            linhas = [" ".join(l.replace("**", "").strip("-* ").split()) for l in bloco.splitlines()[1:]
                      if l.strip().startswith(("-", "*")) and not re.match(r"[-*\s]*\**Estado", l.strip())]
            linhas = [l for l in linhas if not l.endswith(":")]  # cabeçalho vazio ("O que achei:") sem o conteúdo
            log = logs / f"vigia_agente_{hora}.log"
            out.append({"id": f"{nome}:{hora}", "fonte": nome, "quando": _quando(hora), "projeto": None,
                        "problema": m.group(2).strip()[:400], "estado": estado, "resumo": " | ".join(linhas)[:600],
                        "conversa": str(log) if log.exists() else None, "busca": bloco[:4000]})
    return out


def registros():
    return _do_painel() + _dos_diarios()


def buscar(texto, n=3, regs=None):
    """Os n casos mais parecidos com o texto: [(nota, registro)], só com pelo menos 2 palavras importantes em comum."""
    regs = registros() if regs is None else regs
    if not regs:
        return []
    docs = [Counter(_tokens(r["busca"])) for r in regs]
    media = sum(sum(d.values()) for d in docs) / len(docs) or 1
    df = Counter(w for d in docs for w in d)
    q = set(_tokens(texto))
    notas = []
    for r, d in zip(regs, docs):
        comuns = [w for w in q if w in d]
        if len(comuns) < 2:
            continue
        tam = sum(d.values()) or 1
        nota = sum(math.log(1 + (len(docs) - df[w] + 0.5) / (df[w] + 0.5))
                   * d[w] * (K1 + 1) / (d[w] + K1 * (1 - B + B * tam / media)) for w in comuns)
        notas.append((round(nota, 2), r))
    notas.sort(key=lambda x: -x[0])
    return notas[:n]


def bloco_prompt(texto, n=3, nota_min=5.0):  # 22/10: casos certos davam 19-21; parecidos só de palavra, 2-3
    """Texto pronto pro prompt dos agentes ("" se nada parecido)."""
    try:
        achados = [(s, r) for s, r in buscar(texto, n) if s >= nota_min]
    except Exception:  # noqa: BLE001 — a base nunca pode derrubar o agente
        return ""
    if not achados:
        return ""
    linhas = [f"- [{r['quando']} · {r['fonte']} · {r['estado']}] {r['problema'][:200]} => {r['resumo'][:420]}"
              + (f" (conversa: {r['conversa']})" if r.get("conversa") else "") for _s, r in achados]
    return ("CASOS PARECIDOS JÁ VISTOS (base de consertos; confira se ainda vale, o código pode ter mudado depois; "
            "não repita conserto que o dono desfez):\n" + "\n".join(linhas))


if __name__ == "__main__":
    if sys.stdout:
        if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "buscar" and len(sys.argv) > 2:
        for s, r in buscar(" ".join(sys.argv[2:]), 5):
            print(f"{s:6.2f}  [{r['quando']} · {r['fonte']} · {r['estado']}] {r['problema'][:120]}\n        {r['resumo'][:200]}")
        print("\n" + (bloco_prompt(" ".join(sys.argv[2:])) or "(nada parecido o bastante pro prompt)"))
    elif cmd == "listar":
        regs = registros()
        for r in regs:
            print(f"[{r['quando']} · {r['fonte']} · {r['estado']}] {r['problema'][:140]}")
        print(f"\n{len(regs)} casos ({datetime.now():%d/%m %H:%M})")
    else:
        print(__doc__)
