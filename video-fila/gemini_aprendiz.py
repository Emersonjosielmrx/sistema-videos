# -*- coding: utf-8 -*-
r"""gemini_aprendiz.py — o Gemini aprende a consertar (dono 26/10/2026: "sistema de aprendizado pro Gemini com base no
que o Kiro já passou e conforme o tempo também dele, pra que logo ele possa resolver problemas também").

Desde 26/10 os vigias rodam com Gemini e SÓ AVISAM (o Kiro gastava 37% do crédito do mês nos vigias). Este módulo:

1. LIÇÕES DO KIRO: destila os casos RESOLVIDO/NADA A FAZER da base_consertos (diários dos vigias + IA do painel, quase
   tudo feito pelo Kiro) e as lições do dono (config\melhoria_licoes.md) em regras curtas, gravadas em
   config\gemini_licoes.md (refeito 1x/dia; quem destila é o Gemini 3.8 high, sem ferramentas). Também entram os erros
   do próprio Gemini já avaliados — é assim que ele aprende "com o tempo".
2. PROPOSTA: em modo aviso o Gemini escreve "CONSERTO PROPOSTO:" (o que faria). Cada rodada vira um caso em
   estado\gemini_aprendiz.json, com a categoria do problema (texto do problema sem números).
3. NOTA, sozinha ou pelo dono:
   - proposta (REVISAR): quando aparece depois um conserto de verdade parecido (painel/diário), o Gemini 3.8 compara a
     proposta com o que foi feito -> CERTO/ERRADO. Sem conserto em 72 h = sem nota.
   - "nada a fazer" (OK): depois de 24 h, se o mesmo problema não voltou nem foi consertado por outro = CERTO; se foi
     consertado = ERRADO (deixou passar).
   - conserto do próprio Gemini (CONSERTEI, só em categoria liberada): o problema voltou em menos de 6 h = ERRADO e a
     categoria volta para só aviso; não voltou = CERTO.
   - dono no Telegram (bot de produção): "gemini certo 12" / "gemini errado 12" (vale mais que a nota automática).
4. PROMOÇÃO por categoria: >= min_certos notas CERTO nas últimas `janela`, taxa >= taxa_min e a última não ERRADO ->
   o Gemini pode consertar ESSA categoria (pequeno, com backup). Qualquer ERRADO depois rebaixa. Chave geral em
   config\gemini_aprendiz.json ("promover": false = nunca conserta).

    python gemini_aprendiz.py status | destilar | avaliar | certo N | errado N | licoes
"""
import json
import re
import sys
import time
import unicodedata
import urllib.request
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
ESTADO = BASE / "estado" / "gemini_aprendiz.json"
CONFIG = BASE / "config" / "gemini_aprendiz.json"
LICOES = BASE / "config" / "gemini_licoes.md"
LICOES_DONO = BASE / "config" / "melhoria_licoes.md"
PROXY = Path(r"D:\hipercool-videos\secrets\claude_proxy.json")
PADRAO = {"promover": True, "min_certos": 3, "janela": 5, "taxa_min": 0.8, "recaida_h": 6, "ok_h": 24, "expira_h": 72,
          "juiz": "agy/gemini-3.8-flash-high", "juizes_por_rodada": 3, "destilar_h": 24}
INICIO_GEMINI = "2026-10-26 10:00"  # antes disso os diários são do Kiro (lições); depois, do Gemini (casos)


def log(msg):
    linha = f"[{datetime.now():%d/%m %H:%M:%S}] {msg}"
    print(linha)
    try:
        with open(BASE / "logs" / "gemini_aprendiz.log", "a", encoding="utf-8") as f:
            f.write(linha + "\n")
    except OSError:
        pass


def cfg():
    try:
        return {**PADRAO, **json.loads(CONFIG.read_text(encoding="utf-8"))}
    except (OSError, ValueError):
        CONFIG.write_text(json.dumps(PADRAO, ensure_ascii=False, indent=1), encoding="utf-8")
        return dict(PADRAO)


def _ler():
    try:
        e = json.loads(ESTADO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        e = {}
    e.setdefault("casos", []); e.setdefault("vistos", {}); e.setdefault("prox_id", 1)
    return e


def _gravar(e):
    ESTADO.parent.mkdir(parents=True, exist_ok=True)
    tmp = ESTADO.with_suffix(".tmp")
    tmp.write_text(json.dumps(e, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(ESTADO)


def _sem_acento(t):
    t = unicodedata.normalize("NFKD", str(t or "").lower())
    return "".join(c for c in t if not unicodedata.combining(c))


def categoria(linha):
    """'recap longo: alimentador travado (46 min sem dar a volta) — reiniciado' -> 'recap longo: alimentador travado'.
    Sem números (mudam a cada rodada) e só o começo: é a 'família' do problema."""
    t = re.sub(r"^\s*-\s*", "", _sem_acento(linha))
    if t.startswith("ronda de rotina"):
        return "ronda de rotina"
    t = re.sub(r"\(.*?\)|\d+([.,]\d+)?", "#", t)
    t = re.sub(r"[^a-z#_:./ -]", " ", t)
    cab, _, resto = t.partition(":")
    pal = (cab + (": " + " ".join(resto.split()[:3]) if resto else "")).split()
    return " ".join(pal[:8]).strip(" :#-") or "outro"


def categorias(motivo):
    return sorted({categoria(l) for l in str(motivo).splitlines() if l.strip().startswith("-")} or {categoria(motivo)})


# ---------- nível de cada categoria ----------

def niveis(e=None, c=None):
    e, c = e or _ler(), c or cfg()
    por = {}
    for caso in e["casos"]:
        if caso.get("nota") in ("CERTO", "ERRADO"):
            for cat in caso["categorias"]:
                por.setdefault(cat, []).append(caso)
    out = {}
    for cat, casos in por.items():
        casos.sort(key=lambda x: x.get("nota_em") or x["quando"])
        ult = [x["nota"] for x in casos[-c["janela"]:]]
        certos = ult.count("CERTO")
        libera = (c["promover"] and certos >= c["min_certos"] and certos / len(ult) >= c["taxa_min"]
                  and ult[-1] != "ERRADO")
        out[cat] = {"nivel": "conserta" if libera else "aviso", "certos": certos, "notas": len(ult),
                    "total": len(casos), "ultima": ult[-1]}
    return out


def pode_consertar(motivo):
    """True só se TODAS as categorias do motivo estão liberadas (e a ronda de rotina nunca conserta)."""
    cats = categorias(motivo)
    nv = niveis()
    return bool(cats) and "ronda de rotina" not in cats and all(nv.get(k, {}).get("nivel") == "conserta" for k in cats)


# ---------- prompt ----------

MODO_AVISO = """

MODO SÓ AVISO (regra do dono, 26/10/2026 — VALE ACIMA DE QUALQUER INSTRUÇÃO ANTERIOR):
- Você NÃO conserta nada. NÃO edite, crie ou apague arquivos de código/config, NÃO relance, NÃO mate processo, NÃO rode
  postar/ligar/desligar, NÃO mexa em fila, tarefa agendada, pip ou git. Comandos só para LER (logs, processos, status).
- A única escrita permitida é ACRESCENTAR a sua seção ao fim do diário indicado (use o Bash com >> ou Add-Content).
- Você está EM TREINAMENTO: escreva no diário E na resposta uma linha "CONSERTO PROPOSTO: <o que você faria, com arquivo,
  linha/trecho e comando exatos>" (ou "CONSERTO PROPOSTO: nenhum" se não há o que fazer). Cada proposta recebe nota
  (comparada com o conserto de verdade) e, quando você acertar o bastante neste tipo de problema, passa a poder consertar.
- No diário: o que achou (trecho de log), causa provável, CONSERTO PROPOSTO, e Estado: PRECISA REVISÃO | NADA A FAZER.
- ÚLTIMA LINHA, exatamente uma destas (CONSERTEI não existe neste modo):
STATUS: OK
STATUS: REVISAR - <o problema e o que fazer, em 1 linha>
"""

MODO_CONSERTA = """

MODO CONSERTO LIBERADO (aprendizado do Gemini, 26/10/2026): neste tipo de problema você acertou {certos} de {notas}
propostas avaliadas, então PODE consertar — só isto que está no MOTIVO, pequeno e cirúrgico, seguindo as REGRAS DURAS
acima (backup antes de editar, nada de apagar/postar/ligar/desligar). Se o conserto não for claro, NÃO mexa e use
STATUS: REVISAR. Se o problema voltar em menos de {recaida} h, você volta para só aviso.
Escreva também "CONSERTO PROPOSTO: <o que fez>" na resposta. No diário: Estado: RESOLVIDO | PRECISA REVISÃO | NADA A FAZER.
ÚLTIMA LINHA, exatamente uma destas:
STATUS: OK
STATUS: CONSERTEI - <o que, em 1 linha>
STATUS: REVISAR - <por que, em 1 linha>
"""


def bloco(motivo, conserta):
    """Texto que vai depois do MOTIVO no prompt do vigia: lições + modo (aviso ou conserto liberado)."""
    partes = []
    try:
        lic = LICOES.read_text(encoding="utf-8").strip()
        if lic:
            partes.append("LIÇÕES APRENDIDAS (do Kiro, que consertava antes, e das suas notas):\n" + lic[:6000])
    except OSError:
        pass
    if conserta:
        nv = niveis()
        cats = categorias(motivo)
        certos = min(nv[k]["certos"] for k in cats)
        notas = max(nv[k]["notas"] for k in cats)
        partes.append(MODO_CONSERTA.format(certos=certos, notas=notas, recaida=cfg()["recaida_h"]))
    else:
        partes.append(MODO_AVISO)
    return "\n\n" + "\n".join(partes)


# ---------- casos ----------

def ver_problemas(problemas):
    """Toda checagem (com ou sem agente): marca quando cada categoria apareceu por último (pra saber se voltou)."""
    if not problemas:
        return
    e = _ler()
    agora = time.time()
    for p in problemas:
        e["vistos"][categoria(p)] = agora
    _gravar(e)


def _proposta(texto):
    m = re.findall(r"CONSERTO PROPOSTO\**\s*:?\**\s*(.+)", texto or "")
    return " ".join(m[-1].split())[:800] if m else ""


def registrar(lado, motivo, status, texto, conserta):
    e = _ler()
    caso = {"id": e["prox_id"], "quando": datetime.now().strftime("%Y-%m-%d %H:%M"), "t": time.time(), "lado": lado,
            "motivo": str(motivo)[:600], "categorias": categorias(motivo), "status": status,
            "modo": "conserta" if conserta else "aviso", "proposta": _proposta(texto), "nota": None}
    e["prox_id"] += 1
    e["casos"].append(caso)
    e["casos"] = e["casos"][-800:]
    _gravar(e)
    log(f"caso {caso['id']} ({lado}, {caso['modo']}, {status}): {caso['categorias']} | proposta: {caso['proposta'][:150]}")
    return caso["id"]


def _dar_nota(caso, nota, por, motivo=""):
    caso.update(nota=nota, nota_por=por, nota_em=datetime.now().strftime("%Y-%m-%d %H:%M"), nota_motivo=motivo[:300])
    log(f"nota caso {caso['id']}: {nota} ({por}) {motivo[:150]}")


def _consertos_depois(caso, regs):
    """Consertos de verdade (não do Gemini) que vieram depois do caso, parecidos com ele."""
    import base_consertos
    # conserto "de verdade" = IA do painel (botão do dono) ou diário de antes do Gemini; diário depois disso é do
    # próprio Gemini e não serve de gabarito pra ele
    depois = [r for r in regs if r["estado"] == "RESOLVIDO" and _quando_iso(r["quando"]) > caso["quando"]
              and (r["fonte"] == "IA do painel" or _quando_iso(r["quando"]) < INICIO_GEMINI)]
    if not depois:
        return []
    return [r for s, r in base_consertos.buscar(caso["motivo"], 2, regs=depois) if s >= 5.0]


def _quando_iso(q):
    """'22/10 07:15' ou '2026-10-22 07:15' -> '2026-10-22 07:15' (ano atual)."""
    m = re.fullmatch(r"(\d\d)/(\d\d) (\d\d:\d\d)", q or "")
    return f"{datetime.now().year}-{m[2]}-{m[1]} {m[3]}" if m else str(q or "")[:16]


def _juiz(caso, conserto):
    """Gemini 3.8 (sem ferramentas) compara a proposta com o conserto de verdade. CERTO/ERRADO ou None."""
    c = cfg()
    p = json.loads(PROXY.read_text(encoding="utf-8"))
    pergunta = ("Compare a PROPOSTA de um vigia em treinamento com o CONSERTO que foi feito de verdade no mesmo "
                "problema. CERTO = a proposta acha a mesma causa e o conserto dela resolveria (mesmo com outras "
                "palavras). ERRADO = causa errada, ou o conserto não resolveria, ou propôs algo perigoso.\n\n"
                f"PROBLEMA: {caso['motivo'][:500]}\n\nPROPOSTA: {caso['proposta'] or '(não propôs nada)'}\n\n"
                f"CONSERTO DE VERDADE: {conserto['problema'][:300]} => {conserto['resumo'][:600]}\n\n"
                "Responda em 1 linha: CERTO - <por quê> ou ERRADO - <por quê>.")
    req = urllib.request.Request(p["base_url"].rstrip("/") + "/v1/messages", method="POST",
                                 data=json.dumps({"model": c["juiz"], "max_tokens": 300,
                                                  "messages": [{"role": "user", "content": pergunta}]}).encode(),
                                 headers={"x-api-key": p["auth_token"], "anthropic-version": "2023-06-01",
                                          "content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            d = json.loads(r.read().decode("utf-8"))
        txt = " ".join(b.get("text", "") for b in d.get("content", []) if b.get("type") == "text").strip()
    except Exception as ex:  # noqa: BLE001
        log(f"juiz falhou: {type(ex).__name__}: {ex}")
        return None
    m = re.search(r"\b(CERTO|ERRADO)\b\s*[-—:]?\s*(.*)", txt)
    return (m[1], m[2]) if m else None


def avaliar():
    """Dá as notas que já dá pra dar (barato: só chama o juiz quando há conserto de verdade pra comparar)."""
    c, e = cfg(), _ler()
    agora = time.time()
    try:
        import base_consertos
        regs = base_consertos.registros()
    except Exception as ex:  # noqa: BLE001
        log(f"base_consertos falhou: {ex}")
        regs = []
    juizes = 0
    for caso in e["casos"]:
        if caso.get("nota"):
            continue
        idade_h = (agora - caso["t"]) / 3600
        voltou = any(e["vistos"].get(k, 0) > caso["t"] + 600 for k in caso["categorias"])  # 10 min: a mesma rodada
        if caso["status"] == "CONSERTEI":
            if voltou and idade_h <= c["recaida_h"]:
                _dar_nota(caso, "ERRADO", "auto", "o problema voltou depois do conserto")
            elif idade_h > c["recaida_h"]:
                _dar_nota(caso, "CERTO", "auto", f"não voltou em {c['recaida_h']} h")
            continue
        if "ronda de rotina" in caso["categorias"]:
            caso["nota"] = "SEM"  # ronda não ensina conserto
            continue
        feitos = _consertos_depois(caso, regs) if regs else []
        if caso["status"] == "OK":
            if feitos:
                _dar_nota(caso, "ERRADO", "auto", f"disse nada a fazer, mas depois consertaram: {feitos[0]['problema'][:120]}")
            elif idade_h > c["ok_h"]:
                if voltou:
                    caso["nota"] = "SEM"  # voltou sem conserto: não dá pra saber
                else:
                    _dar_nota(caso, "CERTO", "auto", f"nada a fazer e não voltou em {c['ok_h']} h")
            continue
        # REVISAR = proposta
        if feitos and juizes < c["juizes_por_rodada"]:
            juizes += 1
            v = _juiz(caso, feitos[0])
            if v:
                _dar_nota(caso, v[0], "juiz", f"{v[1]} | conserto: {feitos[0]['problema'][:120]}")
        elif idade_h > c["expira_h"]:
            caso["nota"] = "SEM"
    _gravar(e)


def nota_dono(cid, nota):
    e = _ler()
    for caso in e["casos"]:
        if caso["id"] == cid:
            _dar_nota(caso, nota, "dono")
            _gravar(e)
            nv = niveis(e)
            return f"Caso {cid} = {nota}. " + "; ".join(f"{k}: {nv.get(k, {}).get('nivel', 'aviso')}" for k in caso["categorias"])
    return f"Não achei o caso {cid}."


# ---------- lições ----------

def destilar(forcar=False):
    """Refaz config\\gemini_licoes.md a partir do que o Kiro resolveu + lições do dono + erros do Gemini já avaliados."""
    c = cfg()
    if not forcar and LICOES.exists() and time.time() - LICOES.stat().st_mtime < c["destilar_h"] * 3600:
        return False
    import base_consertos
    regs = [r for r in base_consertos.registros() if _quando_iso(r["quando"]) < INICIO_GEMINI]
    resolvidos = [r for r in regs if r["estado"] == "RESOLVIDO"][-90:]
    nada = [r for r in regs if r["estado"] == "NADA A FAZER"][-40:]
    e = _ler()
    erros = [x for x in e["casos"] if x.get("nota") == "ERRADO"][-25:]
    try:
        dono = LICOES_DONO.read_text(encoding="utf-8")[:4000]
    except OSError:
        dono = ""
    texto = ("CONSERTOS QUE FUNCIONARAM (feitos pelo Kiro):\n"
             + "\n".join(f"- {r['problema'][:160]} => {r['resumo'][:320]}" for r in resolvidos)
             + "\n\nFALSOS ALARMES (nada a fazer):\n" + "\n".join(f"- {r['problema'][:160]} => {r['resumo'][:200]}" for r in nada)
             + "\n\nERROS DO VIGIA EM TREINAMENTO (não repetir):\n"
             + "\n".join(f"- {x['motivo'][:160]} | propôs: {x['proposta'][:200]} | errado porque: {x.get('nota_motivo', '')}" for x in erros)
             + "\n\nREGRAS DO DONO:\n" + dono)
    pergunta = ("Você vai treinar um vigia de produção de vídeos (Windows, Python, projetos em D:\\). Abaixo está o "
                "histórico real. Escreva de 25 a 45 LIÇÕES curtas em português, uma por linha começando com '- ', no "
                "formato 'Quando <sinal no log/problema>: a causa costuma ser <...>; o certo é <...>' ou 'Nunca <...>'. "
                "Prefira o que se repete e o que evita estrago. Cite arquivos/comandos exatos quando o histórico citar. "
                "Inclua as lições dos ERROS. Responda só com as linhas.\n\n" + texto[:60000])
    p = json.loads(PROXY.read_text(encoding="utf-8"))
    req = urllib.request.Request(p["base_url"].rstrip("/") + "/v1/messages", method="POST",
                                 data=json.dumps({"model": c["juiz"], "max_tokens": 4000,
                                                  "messages": [{"role": "user", "content": pergunta}]}).encode(),
                                 headers={"x-api-key": p["auth_token"], "anthropic-version": "2023-06-01",
                                          "content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            d = json.loads(r.read().decode("utf-8"))
        txt = "\n".join(b.get("text", "") for b in d.get("content", []) if b.get("type") == "text")
    except Exception as ex:  # noqa: BLE001
        log(f"destilar falhou: {type(ex).__name__}: {ex}")
        return False
    linhas = [l.strip() for l in txt.splitlines() if l.strip().startswith("- ")]
    if len(linhas) < 10:
        log(f"destilar: resposta curta demais ({len(linhas)} linhas) — mantive as lições antigas")
        return False
    LICOES.write_text(f"<!-- gerado por gemini_aprendiz.py destilar em {datetime.now():%d/%m %H:%M} de "
                      f"{len(resolvidos)} consertos, {len(nada)} falsos alarmes e {len(erros)} erros do Gemini -->\n"
                      + "\n".join(linhas) + "\n", encoding="utf-8")
    log(f"lições refeitas: {len(linhas)} linhas")
    return True


# ---------- status / Telegram ----------

def status_texto():
    e, c = _ler(), cfg()
    nv = niveis(e, c)
    casos = e["casos"]
    notas = [x for x in casos if x.get("nota") in ("CERTO", "ERRADO")]
    lin = [f"Aprendizado do Gemini: {len(casos)} rodadas, {len(notas)} com nota "
           f"({sum(x['nota'] == 'CERTO' for x in notas)} certas). Promoção {'LIGADA' if c['promover'] else 'DESLIGADA'}"
           f" (precisa {c['min_certos']} certas nas últimas {c['janela']})."]
    liberadas = [k for k, v in nv.items() if v["nivel"] == "conserta"]
    lin.append("Pode consertar: " + (", ".join(liberadas) if liberadas else "nada ainda (só avisa)"))
    for k, v in sorted(nv.items(), key=lambda kv: -kv[1]["certos"])[:8]:
        lin.append(f"- {k}: {v['certos']}/{v['notas']} certas -> {v['nivel']}")
    pend = [x for x in casos if not x.get("nota") and x["status"] == "REVISAR"][-5:]
    if pend:
        lin.append("Esperando nota (responda 'gemini certo N' ou 'gemini errado N'):")
        lin += [f"#{x['id']} {x['quando'][5:]} {x['motivo'][:90]} | propôs: {x['proposta'][:120]}" for x in pend]
    return "\n".join(lin)


def comando(texto):
    t = re.sub(r"^\s*gemini\s*", "", texto or "", flags=re.I).strip()
    m = re.match(r"(certo|errado)\s*#?(\d+)", t, re.I)
    if m:
        return nota_dono(int(m[2]), m[1].upper())
    if re.match(r"promover\s+(sim|on|ligar)", t, re.I) or re.match(r"promover\s+(n[aã]o|off|desligar)", t, re.I):
        c = cfg()
        c["promover"] = bool(re.match(r"promover\s+(sim|on|ligar)", t, re.I))
        CONFIG.write_text(json.dumps(c, ensure_ascii=False, indent=1), encoding="utf-8")
        return f"Promoção do Gemini {'LIGADA' if c['promover'] else 'DESLIGADA (só avisa sempre)'}."
    if re.match(r"li[cç][oõ]es", t, re.I):
        try:
            return LICOES.read_text(encoding="utf-8")[:3500]
        except OSError:
            return "Ainda sem lições (rode 'gemini destilar')."
    if re.match(r"destilar", t, re.I):
        return "Lições refeitas." if destilar(forcar=True) else "Não consegui refazer as lições (ver logs\\gemini_aprendiz.log)."
    return status_texto() + "\n\nComandos: gemini status | certo N | errado N | lições | destilar | promover sim/não"


if __name__ == "__main__":
    if sys.stdout:
        if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    a = sys.argv[1:] or ["status"]
    if a[0] == "destilar":
        print("ok" if destilar(forcar=True) else "falhou")
    elif a[0] == "avaliar":
        avaliar(); print(status_texto())
    elif a[0] == "licoes":
        print(LICOES.read_text(encoding="utf-8") if LICOES.exists() else "(sem lições)")
    else:
        print(comando(" ".join(a)))
