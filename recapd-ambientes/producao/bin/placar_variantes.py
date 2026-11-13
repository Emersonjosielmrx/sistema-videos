"""placar_variantes.py — placar dos testes A/B/C/D… dos Shorts (Cortes). 30/10/2026. SÓ LÊ e escreve o placar.

Junta o ledger de uploads (D:\\postador-de-videos\\logs\\uploads_ledger.jsonl) com o postar.json/_testes_usados.json de
cada vídeo (braço de cada teste; bin\\variantes.py) e as views medidas (tabela do Studio
D:\\postador-de-videos\\_analise\\metricas_studio.json e medidas de 48 h do telegram_estado.json). Aplica a régua do
FABLE_DECISOES.md:
  D1  só vídeos ELEGÍVEIS (views_periodo >= 20; sem Studio, views de 48 h); métricas: pct_media e
      log(views / mediana do canal); também % que chega a 500 e a 1.500 views.
  D3  pronto para decidir quando há >= 6 elegíveis por braço NO MESMO CANAL (estratificado por canal).
  D16 n >= 12 elegíveis por braço e P(braço > A) >= 0,95.
  D6  nunca por nota do júri (este placar nem lê o júri).
Não muda nada sozinho: escreve D:\\video-fila\\linhas\\CORTES\\placar_cortes_testes.json e .md para a dona/Fable decidir
em bin\\cortes_ajustes.json.

Uso: python placar_variantes.py [--idade-min 48]
"""
import argparse
import json
import math
import random
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import variantes  # noqa: E402

POST = Path(r"D:\postador-de-videos")
LEDGER = POST / "logs" / "uploads_ledger.jsonl"
STUDIO = POST / "_analise" / "metricas_studio.json"
TELEGRAM = POST / "config" / "telegram_estado.json"
PARCEIRO_CFG = Path(__file__).resolve().parent.parent / "config" / "parceiro.json"
SAIDA = Path(r"D:\video-fila\linhas\CORTES")
BR = timezone(timedelta(hours=-3))
ELEGIVEL = 20          # D1
MIN_CANAL = 6          # D3
MIN_TOTAL = 12         # D16
P_DECIDE = 0.95        # D16
# T12 (horário) é por canal e vale para o que foi AGENDADO a partir daqui (antes disso todo canal seguia uma regra só)
INICIO_POR_CANAL = {"horario_fraco": datetime(2026, 10, 30, 15, 12, tzinfo=BR)}
# campos antigos do postar.json (antes do dicionário "variantes"); os do render vêm do _testes_usados.json
CAMPO_RENDER = {"gancho_remotion", "fx_choque", "mascote"}
# teste fechado (valor fixo) sem o dicionário "variantes": pastas a partir deste dia têm o campo com o valor fixo
FECHADO = {"legenda_impacto": "20261030"}  # melhorador fixou "lateral" em 30/10 04:44


def _dia_pasta(nome):
    import re
    m = re.search(r"_(20\d{6})(?:_|$)", nome)
    return m.group(1) if m else "00000000"
NOTAS = {
    "gancho_remotion": "braço 'A_falhou' = sorteado B mas o render caiu no ASS (falha de RAM/PC2): não é sorteio, "
                       "compare só os braços sorteados.",
    "mascote": "braço 'A_falhou' = sorteado B mas falhou: não é sorteio, compare só os braços sorteados.",
    "legenda_impacto": "fechado em 'lateral' pelo melhorador em 30/10 04:44 (sem views); só vídeos de antes têm braço.",
    "horario_fraco": "sorteio por CANAL (cada canal fica num braço só): não dá pra estratificar por canal; a "
                     "comparação é entre canais diferentes e vale só como indício.",
}


def _ler_json(p, padrao):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return padrao


def _dt(s):
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00")).astimezone(BR)
    except (ValueError, TypeError):
        return None


def carregar(idade_min):
    med = (_ler_json(TELEGRAM, {}) or {}).get("medidas_48h") or {}
    ms = _ler_json(STUDIO, {}) or {}
    cfg = _ler_json(PARCEIRO_CFG, {}) or {}
    canais_pt = {d.get("canal") for d in cfg.get("pt", []) if d.get("canal")}
    agora = datetime.now(BR)
    vistos, linhas = set(), []
    try:
        texto = LEDGER.read_text(encoding="utf-8")
    except OSError:
        texto = ""
    for ln in texto.splitlines():
        try:
            r = json.loads(ln)
        except ValueError:
            continue
        vid = r.get("video_id")
        if not vid or vid in vistos or r.get("projeto") != "parceiro" or r.get("tipo") not in (None, "short"):
            continue
        vistos.add(vid)
        pasta = Path(r.get("caminho") or "").parent
        pj = _ler_json(pasta / "postar.json", {})
        tu = _ler_json(pasta / "_testes_usados.json", {})
        pub = _dt(r.get("publish_at") or r.get("ts"))
        agendado = _dt(r.get("ts"))
        s = ms.get(vid) if isinstance(ms.get(vid), dict) else {}
        rl = s.get("ret_lista") or {}
        m = med.get(vid) or {}
        vp = rl.get("views_periodo")
        V = vp if vp is not None else m.get("views")
        pct = s.get("pct_media") if s.get("pct_media") is not None else rl.get("pct_media")
        bracos = {}
        vdict = pj.get("variantes") or {}
        for nome, t in variantes.TESTES.items():
            if t.get("por") == "canal":
                ini = INICIO_POR_CANAL.get(nome)
                cid = r.get("canal_id")
                if cid in canais_pt and agendado and (not ini or agendado >= ini):
                    bracos[nome] = str(variantes.braco(nome, cid))
                continue
            campo = t["campo"]
            if "variantes" in pj:  # vídeo de 30/10 em diante: só conta o que foi SORTEADO (dicionário "variantes")
                if nome not in vdict:
                    continue
                v = vdict[nome]
                if campo in CAMPO_RENDER and tu.get(campo) not in (None, ""):
                    v = tu[campo]  # o que o render usou de fato (A_falhou etc.)
            elif FECHADO.get(nome) and _dia_pasta(pasta.name) >= FECHADO[nome]:
                continue  # campo antigo gravado com o valor fixo depois que o teste fechou: não é sorteio
            elif campo in CAMPO_RENDER and tu.get(campo) not in (None, ""):
                v = tu[campo]
            elif campo in pj:
                v = pj[campo]
            else:
                continue  # vídeo feito antes do teste existir
            v = str(v) if v not in (None, "") else ("centro" if nome == "legenda_impacto" else "A")
            if nome == "fx_choque" and v not in ("A", "A_falhou", "fora"):
                v = "B"  # o render grava o estilo sorteado dentro do B (raio_00d1ff, fogo_ff2a1a…)
            bracos[nome] = v
        for nome, v in vdict.items():  # teste novo que ainda não está no registro
            bracos.setdefault(nome, str(v))
        idade = (agora - pub).total_seconds() / 3600 if pub else None
        linhas.append(dict(vid=vid, canal=r.get("canal") or r.get("canal_id"), canal_id=r.get("canal_id"),
                           pasta=pasta.name, pub=pub.isoformat() if pub else None, idade_h=idade, V=V,
                           medido=V is not None and idade is not None and idade >= idade_min,
                           pct=pct, bracos=bracos))
    # mediana de views por canal (só medidos) para log(V / mediana do canal)
    por_canal = defaultdict(list)
    for x in linhas:
        if x["medido"]:
            por_canal[x["canal"]].append(float(x["V"]))
    mediana = {c: max(statistics.median(v), 1.0) for c, v in por_canal.items()}
    for x in linhas:
        x["elegivel"] = bool(x["medido"] and float(x["V"]) >= ELEGIVEL)
        x["log_rel"] = math.log(max(float(x["V"]), 1.0) / mediana[x["canal"]]) if x["medido"] else None
    return ajustar_por_periodo(linhas)


# ───────── 13/11: views SEM o efeito do horário (pedido do chat do D: em RECADOS_ENTRE_AGENTES.md) ─────────
# Nos Shorts de parceiro o 1º post das 21-23 h rende ~100x o do resto do dia nos canais fracos. "≥ 500 views" e
# "views ÷ mediana do canal" medem em que horário o vídeo caiu, não o braço do teste: braço que caiu mais vezes à
# noite parecia vencedor. Aqui cada vídeo é comparado só com os do MESMO canal no MESMO período (noite x resto), a
# mesma conta do video-fila\inteligencia_ajustada.linhas_ajustadas:
#     rz = (views + 1) ÷ (mediana do grupo + 1), entre 1/8 e 8; grupo com < 4 medidos = mediana do canal inteiro
# e o que o placar compara entre os braços é "ficou ACIMA da mediana do próprio grupo" (rz > 1).
# PLACAR_AJUSTADO=0 volta a decidir pelo ≥ 500 (conta antiga).
NOITE = (21, 22, 23)
MIN_GRUPO = 4
AJUSTADO = __import__("os").environ.get("PLACAR_AJUSTADO", "1") != "0"


def _hora_br(pub):
    d = _dt(pub) if isinstance(pub, str) else pub
    return d.astimezone(BR).hour if d else None


def ajustar_por_periodo(linhas):
    """Põe em cada linha MEDIDA: noite (bool), rz (razão ajustada) e acima (rz > 1). Linha sem medida ou sem hora de
    publicação fica com rz=None (não entra na conta ajustada). Só lê "canal", "pub", "V" e "medido"."""
    grupo, canal = defaultdict(list), defaultdict(list)
    for x in linhas:
        x["noite"], x["rz"], x["acima"] = None, None, None
        h = _hora_br(x.get("pub"))
        if not x.get("medido") or x.get("V") is None or h is None:
            continue
        x["noite"] = h in NOITE
        grupo[(x["canal"], x["noite"])].append(float(x["V"]))
        canal[x["canal"]].append(float(x["V"]))
    for x in linhas:
        if x["noite"] is None:
            continue
        g = grupo[(x["canal"], x["noite"])]
        base = statistics.median(g) if len(g) >= MIN_GRUPO else statistics.median(canal[x["canal"]])
        x["rz"] = round(max(0.125, min(8.0, (float(x["V"]) + 1) / (base + 1))), 4)
        x["acima"] = x["rz"] > 1.0
    return linhas


def _p_melhor(k_n_por_braco, ref, sorteios=20000, semente=7):
    """P(taxa do braço > taxa do braço de referência), Beta(1+k, 1+n-k) — para cada braço != ref."""
    rnd = random.Random(semente)
    if ref not in k_n_por_braco:
        return {}
    kr, nr = k_n_por_braco[ref]
    out = {}
    for b, (k, n) in k_n_por_braco.items():
        if b == ref or n == 0 or nr == 0:
            continue
        ganhou = sum(rnd.betavariate(1 + k, 1 + n - k) > rnd.betavariate(1 + kr, 1 + nr - kr) for _ in range(sorteios))
        out[b] = round(ganhou / sorteios, 3)
    return out


def _resumo(xs):
    E = [x for x in xs if x["elegivel"]]
    pcts = [float(x["pct"]) for x in E if x["pct"] is not None]
    rel = [x["log_rel"] for x in E if x["log_rel"] is not None]
    n = len(E)
    return dict(
        n_total=len(xs), n_medidos=sum(x["medido"] for x in xs), n_elegiveis=n,
        pct_elegivel=round(n / max(1, sum(x["medido"] for x in xs)), 3),
        chega_500=round(sum(float(x["V"]) >= 500 for x in E) / n, 3) if n else None,
        chega_1500=round(sum(float(x["V"]) >= 1500 for x in E) / n, 3) if n else None,
        pct_media=round(statistics.mean(pcts), 1) if pcts else None,
        pct_ge65=round(sum(p >= 65 for p in pcts) / len(pcts), 3) if pcts else None,
        log_views_rel=round(statistics.mean(rel), 3) if rel else None,
        # ajustado pelo horário (mesmo canal + mesmo período); conta TODOS os medidos, não só os elegíveis: de dia o
        # canal fraco quase não tem vídeo com 20 views e o corte dos elegíveis deixava só os posts da noite
        **_resumo_ajustado(xs),
    )


def _resumo_ajustado(xs):
    A = [x for x in xs if x.get("rz") is not None]
    n = len(A)
    return dict(
        n_ajustados=n, n_noite=sum(bool(x["noite"]) for x in A),
        acima_grupo=round(sum(bool(x["acima"]) for x in A) / n, 3) if n else None,
        log_rz=round(statistics.mean(math.log(x["rz"]) for x in A), 3) if n else None,
    )


def placar(linhas, aj):
    testes = list(variantes.TESTES) + sorted({n for x in linhas for n in x["bracos"]} - set(variantes.TESTES))
    out = {}
    for nome in testes:
        t = variantes.TESTES.get(nome, {})
        xs = [x for x in linhas if nome in x["bracos"]]
        valor = aj.get(nome, t.get("padrao", "ab"))
        ops = variantes.opcoes(valor, t.get("nomes"))
        bracos = sorted({x["bracos"][nome] for x in xs})
        ref = (t.get("nomes") or ["A"])[0]
        por_braco = {b: _resumo([x for x in xs if x["bracos"][nome] == b]) for b in bracos}
        # D3: por canal, elegíveis por braço; canais onde TODOS os braços sorteados têm >= MIN_CANAL
        sorteados = ops or bracos
        canal = defaultdict(lambda: defaultdict(int))
        for x in xs:
            if x["elegivel"]:
                canal[x["canal"]][x["bracos"][nome]] += 1
        canais_ok = sorted(c for c, d in canal.items() if len(sorteados) >= 2 and all(d.get(b, 0) >= MIN_CANAL
                                                                                       for b in sorteados))
        kn500 = {b: (round((r["chega_500"] or 0) * r["n_elegiveis"]), r["n_elegiveis"]) for b, r in por_braco.items()}
        kn65 = {}
        for b in bracos:
            E = [x for x in xs if x["bracos"][nome] == b and x["elegivel"] and x["pct"] is not None]
            kn65[b] = (sum(float(x["pct"]) >= 65 for x in E), len(E))
        p500 = _p_melhor(kn500, ref)
        p65 = _p_melhor(kn65, ref)
        n_ok = all(por_braco.get(b, {}).get("n_elegiveis", 0) >= MIN_TOTAL for b in sorteados) if len(sorteados) >= 2 \
            else False
        # 13/11: views ajustadas pelo horário — "acima da mediana do próprio grupo" por braço, com TODOS os medidos
        kn_aj = {b: (sum(bool(x["acima"]) for x in xs if x["bracos"][nome] == b and x.get("rz") is not None),
                     sum(1 for x in xs if x["bracos"][nome] == b and x.get("rz") is not None)) for b in bracos}
        p_aj = _p_melhor(kn_aj, ref)
        canal_aj = defaultdict(lambda: defaultdict(int))
        for x in xs:
            if x.get("rz") is not None:
                canal_aj[x["canal"]][x["bracos"][nome]] += 1
        if AJUSTADO:  # decide pela conta ajustada (e pela retenção, que não depende do horário)
            p_views = p_aj
            n_ok = len(sorteados) >= 2 and all(kn_aj.get(b, (0, 0))[1] >= MIN_TOTAL for b in sorteados)
            canais_ok = sorted(c for c, d in canal_aj.items() if len(sorteados) >= 2
                               and all(d.get(b, 0) >= MIN_CANAL for b in sorteados))
        else:
            p_views = p500
        vencedor = [b for b in sorteados if b != ref and max(p_views.get(b, 0), p65.get(b, 0)) >= P_DECIDE]
        perdedor = [b for b in sorteados if b != ref and min(p_views.get(b, 1), p65.get(b, 1)) <= 1 - P_DECIDE]
        if not ops:
            estado = f"sem teste agora (valor fixo {valor!r})"
        elif nome == "horario_fraco":
            estado = ("dá pra olhar (só indício: braço por canal)" if n_ok else "esperando dados")
        elif canais_ok and n_ok and (vencedor or perdedor):
            estado = "PRONTO PARA DECIDIR (D3+D16)"
        elif canais_ok and n_ok:
            estado = "dados suficientes, sem diferença clara ainda"
        else:
            estado = "esperando dados"
        out[nome] = dict(
            valor_atual=valor, bracos_sorteados=sorteados, referencia=ref, estado=estado,
            por_braco=por_braco, elegiveis_por_canal={c: dict(d) for c, d in sorted(canal.items())},
            canais_com_6_por_braco=canais_ok, n12_por_braco=n_ok,
            p_melhor_que_ref_500=p500, p_melhor_que_ref_pct65=p65,
            p_melhor_que_ref_ajustado=p_aj, decide_por=("ajustado+pct65" if AJUSTADO else "500+pct65"),
            medidos_por_canal_ajustado={c: dict(d) for c, d in sorted(canal_aj.items())},
            sugestao=(f"{vencedor} melhor que {ref}" if vencedor else "") + (f"; {perdedor} pior que {ref}"
                                                                           if perdedor else ""),
            nota=NOTAS.get(nome, ""),
        )
    return out


def relatorio_md(res, linhas, gerado):
    med = sum(x["medido"] for x in linhas)
    ele = sum(x["elegivel"] for x in linhas)
    L = [f"# Placar dos testes dos Shorts (Cortes) — {gerado}", "",
         "Gerado por `D:\\recapd-ambientes\\producao\\bin\\placar_variantes.py` (só lê; não muda nada). Régua do "
         "FABLE_DECISOES.md: D1 só **elegíveis** (views >= 20), D3 >= 6 elegíveis por braço no mesmo canal, "
         "D16 >= 12 por braço e P >= 0,95; nunca pela nota do júri (D6). Decidir = mudar a chave em "
         "`bin\\cortes_ajustes.json` para o braço vencedor (com linha no histórico).", "",
         f"Shorts de parceiro no ledger: {len(linhas)} | medidos (>= 48 h): {med} | elegíveis: {ele}", ""]
    for nome, r in res.items():
        L.append(f"## {nome} — {r['estado']}")
        L.append(f"Valor em cortes_ajustes: `{r['valor_atual']}` | braços: {', '.join(map(str, r['bracos_sorteados']))}"
                 f" | referência: {r['referencia']}")
        if r["nota"]:
            L.append(f"> {r['nota']}")
        L.append("")
        L.append("| braço | vídeos | medidos | elegíveis | % eleg. | ≥500 | ≥1.500 | pct_media | pct≥65 | log(v/med) | "
                 "à noite | acima do grupo | log(rz) |")
        L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
        f = lambda v, pc=False: "—" if v is None else (f"{v:.0%}" if pc else f"{v}")
        for b, s in r["por_braco"].items():
            L.append(f"| {b} | {s['n_total']} | {s['n_medidos']} | {s['n_elegiveis']} | {f(s['pct_elegivel'], 1)} | "
                     f"{f(s['chega_500'], 1)} | {f(s['chega_1500'], 1)} | {f(s['pct_media'])} | {f(s['pct_ge65'], 1)} | "
                     f"{f(s['log_views_rel'])} | {s.get('n_noite', 0)}/{s.get('n_ajustados', 0)} | "
                     f"{f(s.get('acima_grupo'), 1)} | {f(s.get('log_rz'))} |")
        if r.get("p_melhor_que_ref_ajustado"):
            L.append(f"\nP(melhor que {r['referencia']}) AJUSTADO pelo horário (acima da mediana do mesmo canal e "
                     f"período): {r['p_melhor_que_ref_ajustado']} — decide por: {r.get('decide_por')}")
        if r["p_melhor_que_ref_500"] or r["p_melhor_que_ref_pct65"]:
            L.append(f"\nP(melhor que {r['referencia']}): ≥500 {r['p_melhor_que_ref_500']} | pct≥65 "
                     f"{r['p_melhor_que_ref_pct65']}")
        L.append(f"\nCanais com ≥ {MIN_CANAL} elegíveis em cada braço: {', '.join(r['canais_com_6_por_braco']) or 'nenhum'}"
                 f" | ≥ {MIN_TOTAL} por braço no total: {'sim' if r['n12_por_braco'] else 'não'}")
        if r["sugestao"]:
            L.append(f"\n**Sugestão (a dona decide):** {r['sugestao']}")
        L.append("")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--idade-min", type=float, default=48, help="horas desde a publicação para contar a medida")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    linhas = carregar(a.idade_min)
    res = placar(linhas, variantes.ajustes())
    gerado = datetime.now(BR).strftime("%Y-%m-%d %H:%M")
    SAIDA.mkdir(parents=True, exist_ok=True)
    (SAIDA / "placar_cortes_testes.json").write_text(json.dumps(
        {"gerado": gerado, "regua": {"elegivel_views": ELEGIVEL, "min_por_braco_canal": MIN_CANAL,
                                     "min_por_braco": MIN_TOTAL, "p_decide": P_DECIDE, "idade_min_h": a.idade_min},
         "testes": res}, ensure_ascii=False, indent=1), encoding="utf-8")
    md = relatorio_md(res, linhas, gerado)
    (SAIDA / "placar_cortes_testes.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
