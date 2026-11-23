"""medico_recuperacao.py — 23/11 dona: "analise tudo, melhore tudo que pode elevar a postagem e os resultados,
principalmente a recuperação, e crie scripts pra ficar analisando e tomando decisões de melhorias".

O que faz (1x por dia, depois que o YouTube fecha as views da véspera — tarefa MedicoRecuperacao 07:10):
  1. MEDE cada canal vivo: views/dia (estado\\canais_views_hist.jsonl, 1ª leitura do dia, corte 06h) x a média de
     ANTES dos banimentos (12-16/11), tendência dos últimos 3 dias e % dos Shorts abertos às 21-22 h (uploads_ledger).
  2. DECIDE por canal, uma alavanca por vez (sempre com o número que justificou):
       - restrito (<30%) e < 50% dos Shorts no nobre       -> "so_nobre": abre só às 21-22 h (21 h = 8,9x a mediana
         em 2160 Shorts, estado\\sinais_shorts.json)
       - restrito há >= DIAS_SEM_REAGIR dias, já no nobre, sem subir -> "descanso": 0 vídeos por DESCANSO_DIAS dias
       - recuperado (>= 70%) por 2 dias seguidos           -> tira "so_nobre"/"punido" (a rampa volta a subir)
  3. AVALIA cada alavanca aplicada há >= DIAS_AVALIAR dias: views/dia depois x antes. Alavanca que NÃO melhorou em
     2+ canais vai pra lista "nao_funciona" e o médico para de usar (aprende).
  4. Escreve estado\\medico_recuperacao.json (histórico de decisões) e MEDICO.md (painel legível pra dona e pro
     relatorio_ronda).

As alavancas vão em D:\\postador-de-videos\\config\\rampa_canais.json (campos "so_nobre", "descanso_ate",
"medico") e o politica.py lê (horario_publicacao / _extra_rampa). Desliga tudo: MEDICO_ALAVANCAS=0 no ambiente do
postador ou arquivo estado\\medico_recuperacao.off. Só aplica com --aplicar (sem isso = ensaio, só escreve o painel).
    python medico_recuperacao.py            # ensaio: mede, decide, mostra
    python medico_recuperacao.py --aplicar  # grava as alavancas
"""
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE = Path(r"D:\video-fila")
HIST = BASE / "estado" / "canais_views_hist.jsonl"
EST = BASE / "estado" / "medico_recuperacao.json"
PAINEL = BASE / "MEDICO.md"
DESLIGA = BASE / "estado" / "medico_recuperacao.off"
RAMPA = Path(r"D:\postador-de-videos\config\rampa_canais.json")
LEDGER = Path(r"D:\postador-de-videos\logs\uploads_ledger.jsonl")
TRAVADAS = Path(r"D:\postador-de-videos\config\contas_travadas.json")
BR = timezone(timedelta(hours=-3))

ANTES = [f"2026-11-{d}" for d in range(12, 17)]
RECUPERADO, RESTRITO = 0.70, 0.30
NOBRE_MIN = 0.50          # abaixo disto o canal "não usa" o nobre
DIAS_SEM_REAGIR = int(os.environ.get("MEDICO_DIAS_SEM_REAGIR", "5"))
DESCANSO_DIAS = int(os.environ.get("MEDICO_DESCANSO_DIAS", "3"))
DIAS_AVALIAR = int(os.environ.get("MEDICO_DIAS_AVALIAR", "3"))
MIN_ANTES = 300           # canal que fazia < 300 views/dia antes não tem base pra medir recuperação


def log(m):
    print(m, flush=True)


def _dia(ts):
    return (datetime.fromisoformat(ts[:16]) - timedelta(hours=6)).date().isoformat()


def series():
    """{slug: {"nome", "ganho": {dia: views}}} — views ganhas por dia fechado."""
    prim = {}
    for ln in HIST.read_text(encoding="utf-8", errors="ignore").splitlines():
        try:
            r = json.loads(ln)
        except ValueError:
            continue
        s, ts, v = r.get("slug"), r.get("ts", ""), r.get("views")
        if not s or v is None or ts < "2026-11-10":
            continue
        k = (s, _dia(ts))
        if k not in prim or ts < prim[k][0]:
            prim[k] = (ts, v, r.get("nome") or s)
    out = {}
    for s in {k[0] for k in prim}:
        dias = sorted(d for (ss, d) in prim if ss == s)
        g = {a: prim[(s, b)][1] - prim[(s, a)][1] for a, b in zip(dias, dias[1:])}
        out[s] = {"nome": prim[(s, dias[-1])][2], "ganho": g}
    return out


def nobre_por_canal(dias=7):
    """{nome do canal: (Shorts que abriram, quantos às 21-22 h)} nos últimos N dias."""
    lim = (datetime.now(BR) - timedelta(days=dias)).date().isoformat()
    hoje = datetime.now(BR).date().isoformat()
    tot, nob = Counter(), Counter()
    for ln in LEDGER.read_text(encoding="utf-8", errors="ignore").splitlines():
        try:
            r = json.loads(ln)
        except ValueError:
            continue
        if r.get("tipo") == "completo":
            continue
        pa = r.get("publish_at")
        try:
            d = datetime.fromisoformat(pa.replace("Z", "+00:00")).astimezone(BR) if pa else \
                datetime.fromisoformat(r["ts"]).astimezone(BR)
        except (ValueError, KeyError, AttributeError):
            continue
        if not (lim <= d.date().isoformat() <= hoje):
            continue
        c = r.get("canal_id")
        tot[c] += 1
        nob[c] += d.hour in (21, 22)
    return tot, nob


def _norm(x):
    import unicodedata
    x = unicodedata.normalize("NFKD", str(x or "")).encode("ascii", "ignore").decode().lower()
    return "".join(ch for ch in x if ch.isalnum())


def _slug_para_id():
    """nome/slug do histórico de views -> canal_id do postador. O uploads_ledger tem os dois (canal + canal_id);
    também vale o canal_id sem "novo_" e sem "_" (novo_imovelemfoco -> imovelemfoco = slug do histórico)."""
    m = {}
    for ln in LEDGER.read_text(encoding="utf-8", errors="ignore").splitlines()[-20000:]:
        try:
            r = json.loads(ln)
        except ValueError:
            continue
        cid = r.get("canal_id")
        if not cid:
            continue
        m[_norm(r.get("canal"))] = cid
        m[_norm(cid.replace("novo_", ""))] = cid
    m[_norm("Fio da Meada")] = m.get(_norm("Fio da Meada")) or "novo_codigo_inteligente_n7j"  # @CodigoInteligente-n7j
    m[_norm("fiodameada")] = "novo_codigo_inteligente_n7j"
    return m


def main():
    aplicar = "--aplicar" in sys.argv and not DESLIGA.exists()
    agora = datetime.now(BR)
    ontem = (agora - timedelta(days=1)).date().isoformat()
    est = json.loads(EST.read_text("utf-8")) if EST.exists() else {"decisoes": [], "nao_funciona": []}
    rampa = json.loads(RAMPA.read_text("utf-8"))
    canais_r = rampa.setdefault("canais", {})
    try:
        trav = set(json.loads(TRAVADAS.read_text("utf-8")).keys())
    except (OSError, ValueError, AttributeError):
        trav = set()
    ser = series()
    tot, nob = nobre_por_canal()
    s2id = _slug_para_id()
    linhas, novas = [], []

    for s, d in sorted(ser.items(), key=lambda x: -sum(x[1]["ganho"].get(a, 0) for a in ANTES)):
        if s in trav:
            continue
        base = [d["ganho"][a] for a in ANTES if a in d["ganho"]]
        if not base:
            continue
        media = sum(base) / len(base)
        if media < MIN_ANTES:
            continue
        ult = [d["ganho"].get((agora - timedelta(days=i)).date().isoformat()) for i in (3, 2, 1)]
        ult = [x for x in ult if x is not None]
        if not ult:
            continue
        v_ontem = d["ganho"].get(ontem, ult[-1])
        pct = v_ontem / media
        tend = "↗" if len(ult) >= 2 and ult[-1] > ult[0] * 1.3 else ("↘" if len(ult) >= 2 and ult[-1] < ult[0] * 0.7 else "→")
        cid = s2id.get(_norm(s)) or s2id.get(_norm(d["nome"]))
        n_tot, n_nob = tot.get(cid, 0), nob.get(cid, 0)
        frac_nobre = n_nob / n_tot if n_tot else 0
        cr = canais_r.get(cid) or {} if cid else {}
        sit = "✅ recuperado" if pct >= RECUPERADO else ("🔴 restrito" if pct < RESTRITO else "🟡 parcial")
        dias_restrito = 0
        for i in range(1, 15):
            g = d["ganho"].get((agora - timedelta(days=i)).date().isoformat())
            if g is None or g / media >= RESTRITO:
                break
            dias_restrito += 1
        dec = None
        if not cid:
            acao = "sem canal_id no cadastro (não mexo)"
        elif cr.get("descanso_ate") and cr["descanso_ate"] > agora.isoformat():
            acao = f"em descanso até {cr['descanso_ate'][:10]}"
        elif pct >= RECUPERADO and d["ganho"].get((agora - timedelta(days=2)).date().isoformat(), 0) / media >= RECUPERADO:
            if cr.get("so_nobre") or cr.get("punido"):
                dec = {"alavanca": "liberar", "motivo": f"{pct:.0%} da média 2 dias seguidos"}
            acao = "recuperado — " + ("liberar (tira so_nobre/punido)" if dec else "nada")
        elif sit == "🔴 restrito" and frac_nobre < NOBRE_MIN and not cr.get("so_nobre") \
                and "so_nobre" not in est["nao_funciona"]:
            dec = {"alavanca": "so_nobre", "motivo": f"{pct:.0%} da média e só {n_nob}/{n_tot} Shorts às 21-22 h"}
            acao = "SÓ NOBRE (21-22 h)"
        elif sit == "🔴 restrito" and dias_restrito >= DIAS_SEM_REAGIR and tend != "↗" \
                and "descanso" not in est["nao_funciona"] and not cr.get("descanso_feito"):
            dec = {"alavanca": "descanso", "motivo": f"restrito há {dias_restrito} dias sem reagir ({pct:.0%})"}
            acao = f"DESCANSO {DESCANSO_DIAS} dias"
        else:
            acao = "observar"
        if dec:
            dec.update({"canal_id": cid, "canal": d["nome"], "slug": s, "quando": agora.isoformat(timespec="seconds"),
                        "views_antes": round(sum(ult) / len(ult)), "media_pre_ban": round(media),
                        "aplicado": aplicar})
            novas.append(dec)
        linhas.append(f"| {d['nome'][:24]} | {media:,.0f} | {' / '.join(f'{x:,}' for x in ult)} | {pct:.0%} {tend} | "
                      f"{sit} | {n_nob}/{n_tot} | {acao} |".replace(",", "."))

    # 23/11: alavanca NOVA (sem placar ainda) vai só em METADE dos canais elegíveis; a outra metade fica de CONTROLE
    # (mesma medição, sem mexer) — senão "melhorou" pode ser só o tempo passando. Alterna pela ordem de tamanho.
    # Com 2+ resultados bons no placar a alavanca passa a valer pra todos. MEDICO_SEM_CONTROLE=1 aplica em todos.
    placar_bom = Counter(x["alavanca"] for x in est["decisoes"] if (x.get("resultado") or {}).get("melhorou"))
    for alav in ("so_nobre", "descanso"):
        grupo = [x for x in novas if x["alavanca"] == alav]
        if placar_bom[alav] >= 2 or os.environ.get("MEDICO_SEM_CONTROLE") == "1":
            continue
        for i, x in enumerate(grupo):
            if i % 2 == 1:
                x["alavanca"] = f"controle_{alav}"
                x["motivo"] += " — CONTROLE (não mexo, comparo)"
    for x in novas:
        if x["alavanca"].startswith("controle_"):
            x["aplicado"] = aplicar  # o controle também é "medido" depois

    # aplica
    if aplicar:
        for dec in novas:
            c = canais_r.setdefault(dec["canal_id"], {})
            if dec["alavanca"] == "so_nobre":
                c["so_nobre"] = "21-23"
            elif dec["alavanca"] == "descanso":
                c["descanso_ate"] = (agora + timedelta(days=DESCANSO_DIAS)).isoformat(timespec="seconds")
                c["descanso_feito"] = agora.date().isoformat()
            elif dec["alavanca"] == "liberar":
                c.pop("so_nobre", None)
                c.pop("punido", None)
            c["medico"] = f"{dec['alavanca']} {dec['quando'][:16]}: {dec['motivo']}"
        if novas:
            tmp = RAMPA.with_suffix(".tmp")
            tmp.write_text(json.dumps(rampa, ensure_ascii=False, indent=1), "utf-8")
            os.replace(tmp, RAMPA)
        est["decisoes"].extend(novas)

    # avalia alavancas antigas (aprende)
    aval = []
    por_alav = defaultdict(lambda: [0, 0])  # alavanca -> [melhorou, não]
    for dec in est["decisoes"]:
        if not dec.get("aplicado") or dec.get("resultado") or dec["alavanca"] == "liberar":
            continue
        t0 = datetime.fromisoformat(dec["quando"])
        if (agora - t0).days < DIAS_AVALIAR:
            continue
        g = ser.get(dec["slug"], {}).get("ganho", {})
        # descanso: mede os DIAS_AVALIAR dias DEPOIS do fim do descanso
        ini = t0 + timedelta(days=DESCANSO_DIAS if dec["alavanca"] == "descanso" else 0)
        dep = [g.get((ini + timedelta(days=i)).date().isoformat()) for i in range(1, DIAS_AVALIAR + 1)]
        dep = [x for x in dep if x is not None]
        if len(dep) < 2:
            continue
        m = sum(dep) / len(dep)
        melhorou = m >= dec["views_antes"] * 1.5 and m - dec["views_antes"] >= 50
        dec["resultado"] = {"views_depois": round(m), "melhorou": melhorou, "medido": agora.isoformat(timespec="seconds")}
        aval.append(f"- {dec['canal']}: **{dec['alavanca']}** {dec['views_antes']} -> {round(m)} views/dia "
                    f"({'✅ melhorou' if melhorou else '❌ não mudou'})")
    # efeito = melhora da alavanca ACIMA da melhora do controle (razão depois/antes)
    def _razao(x):
        r = x.get("resultado") or {}
        return (r.get("views_depois", 0) + 1) / (x.get("views_antes", 0) + 1)
    for alav in ("so_nobre", "descanso"):
        ctl = [_razao(x) for x in est["decisoes"] if x["alavanca"] == f"controle_{alav}" and x.get("resultado")]
        if not ctl:
            continue
        base_ctl = sorted(ctl)[len(ctl) // 2]
        for x in est["decisoes"]:
            if x["alavanca"] == alav and x.get("resultado") and "vs_controle" not in x["resultado"]:
                x["resultado"]["vs_controle"] = round(_razao(x) / base_ctl, 2)
                x["resultado"]["melhorou"] = x["resultado"]["vs_controle"] >= 1.3
                aval.append(f"- {x['canal']}: {alav} vs controle = {x['resultado']['vs_controle']}x")
    for dec in est["decisoes"]:
        r = dec.get("resultado")
        if r and not dec["alavanca"].startswith("controle_"):
            por_alav[dec["alavanca"]][0 if r["melhorou"] else 1] += 1
    for alav, (bom, ruim) in por_alav.items():
        if ruim >= 2 and bom == 0 and alav not in est["nao_funciona"]:
            est["nao_funciona"].append(alav)
            aval.append(f"- ⛔ **{alav}** não ajudou em {ruim} canais — o médico para de usar")
    if aplicar or aval:
        EST.write_text(json.dumps(est, ensure_ascii=False, indent=1), "utf-8")

    out = [f"# 🩺 Médico da recuperação — {agora:%d/%m %H:%M}" + ("" if aplicar else " (ensaio)"), "",
           "| Canal | Antes (média/dia) | Últimos 3 dias | Ontem x antes | Situação | Nobre 7 d | Decisão |",
           "|---|---:|---|---:|---|---:|---|", *linhas, ""]
    out += ["## Decisões desta rodada", *(f"- {x['canal']}: **{x['alavanca']}** — {x['motivo']}" +
                                       ("" if aplicar else " _(ensaio, não aplicado)_") for x in novas)] \
        if novas else ["## Decisões desta rodada", "- nenhuma"]
    out += ["", "## Resultado das alavancas", *(aval or ["- nada pra medir ainda (precisa de "
                                                          f"{DIAS_AVALIAR} dias depois de aplicar)"])]
    placar = [f"- {a}: {b} melhorou / {r} não" for a, (b, r) in por_alav.items()]
    out += ["", "## Placar das alavancas (aprendizado)", *(placar or ["- ainda sem medição"]),
            f"- não funcionam (o médico não usa mais): {', '.join(est['nao_funciona']) or 'nenhuma'}"]
    PAINEL.write_text("\n".join(out) + "\n", "utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
