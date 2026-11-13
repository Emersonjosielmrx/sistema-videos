"""virais_fracos.py — viral num canal -> versão NOVA da mesma fonte nos canais fracos (dona, 30/10/2026).

Dona 30/10: "a ideia seria POSTAR NESSES CANAIS QUE NÃO DÃO VISUALIZAÇÕES OS VÍDEOS QUE VIRALIZAM NOS OUTROS; e se um
tipo de vídeo ou um parceiro não dá visualizações, aí sim nós cortamos."

Como funciona (o mais simples e seguro):
  - VIRAL = Short nosso com >= min_views_48h no placar de 48 h (D:\\postador-de-videos\\config\\telegram_estado.json,
    medidas_48h, o mesmo do notificar_telegram.medir_48h), publicado nos últimos janela_dias, com fonte de parceiro
    conhecida (postar.json "fonte" + "parceiro" que existe em config/parceiro.json "fontes").
  - FRACO = canal ligado do parceiro com >= fracos.min_medidos Shorts medidos em fracos.janela_dias e que NÃO dá views:
    mediana < fracos.mediana_max E fração >= 500 views <= fracos.pct500_max.
  - Para cada viral, os fracos que ainda não receberam essa fonte ganham uma versão NOVA: o anime_auto roda de novo
    sobre o MESMO vídeo da fonte (--fonte <canal do parceiro> --id <vídeo>) com o @ e o destino do canal fraco — novo
    roteiro, nova narração, novo título (o mesmo caminho de quando a fonte vai pra outro canal/língua). NUNCA re-sobe o
    mesmo arquivo (o YouTube trata como conteúdo reutilizado).
  - O postar.json novo ganha "viral_de" (vídeo viral, views, canal): o parceiro_diario.postar deixa essa fonte subir
    mesmo já postada em outro canal (exceção à regra "nunca a mesma fonte em 2 canais") e põe o viral NA FRENTE da fila
    do canal fraco (ele substitui o Short comum do dia, não soma upload — o canal fraco já bate na cota/limite).
  - Nicho: o canal fraco do mesmo nicho da fonte vai primeiro; de outro nicho só com aceitar_outro_nicho=true (a dona
    aceita testar). A narração segue o tipo da FONTE (PARCEIRO_TIPO), nunca o do canal.
  - Canal fraco esperando o "limite diário de envios" do YouTube ou com Short pronto parado há > parado_max_dias não
    recebe (não teria como subir: só aumentaria o estoque parado).

Liga/desliga: config/parceiro.json "virais_fracos": {"modo": "desligado" | "ensaio" | "ligado", ...}.
  ensaio  = a produção só REGISTRA o que faria (logs/virais_fracos.jsonl + log da produção); nada é produzido.
  ligado  = 1 versão por rodada da produção (max_por_dia no total), antes da produção normal.

  python bin/virais_fracos.py --ensaio      mostra virais, canais fracos e o plano (não produz nada)
  python bin/virais_fracos.py --fontes      placar por parceiro (fonte) e por tipo — base dos cortes
"""
import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

BIN = Path(__file__).resolve().parent
if str(BIN) not in sys.path:
    sys.path.insert(0, str(BIN))
import parceiro_diario as pdx  # noqa: E402

POSTADOR = Path(r"D:\postador-de-videos")
ESTADO_TG = POSTADOR / "config" / "telegram_estado.json"
REGISTRO = pdx.WS / "_virais_fracos.json"           # {fonte_id: {canal: ts}} — quem já recebeu cada fonte viral
LOG_JSONL = pdx.PROD / "logs" / "virais_fracos.jsonl"  # o que fez / faria (ensaio), 1 linha por decisão

PADRAO = {"modo": "ensaio", "min_views_48h": 1500, "janela_dias": 12, "max_canais_por_viral": 3,
          "max_por_dia": 4, "max_por_rodada": 1, "aceitar_outro_nicho": True, "parado_max_dias": 4,
          "fracos": {"janela_dias": 21, "min_medidos": 5, "mediana_max": 100, "pct500_max": 10}}


def conf(c=None):
    c = c or pdx.cfg()
    out = json.loads(json.dumps(PADRAO))
    v = c.get("virais_fracos") or {}
    out.update({k: x for k, x in v.items() if k != "fracos"})
    out["fracos"].update(v.get("fracos") or {})
    return out


def _ler(path, padrao):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return padrao


def _ts(s):
    try:
        d = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


# ─────────────────────────── base: medidas 48 h x ledger x postar.json ───────────────────────────
def base():
    """[{vid, canal (cred), views, pub, pj, fonte_id, parceiro, tipo, idioma}] dos vídeos medidos em 48 h."""
    med = (_ler(ESTADO_TG, {}) or {}).get("medidas_48h") or {}
    por_vid = {}
    try:
        for l in pdx.LEDGER.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(l)
            except ValueError:
                continue
            if r.get("video_id"):
                por_vid.setdefault(r["video_id"], r)
    except OSError:
        pass
    out = []
    for vid, m in med.items():
        r = por_vid.get(vid) or {}
        pj, d = None, {}
        if r.get("caminho"):
            pj = Path(r["caminho"]).parent / "postar.json"
            d = _ler(pj, {})
        out.append({"vid": vid, "canal": r.get("canal_id"), "views": int(m.get("views") or 0), "pub": _ts(m.get("pub")),
                    "projeto": r.get("projeto"), "pj": pj, "fonte": d.get("fonte"), "fonte_id": pdx._id_fonte(d.get("fonte")),
                    "parceiro": d.get("parceiro"), "tipo": d.get("midia"), "idioma": d.get("idioma") or "pt",
                    "titulo": d.get("titulo") or m.get("titulo") or "", "viral_de": d.get("viral_de")})
    return out


def canais_fracos(c, b, k):
    """{cred: estatística} dos canais ligados do parceiro que não dão views (todos os projetos medidos no canal)."""
    f = k["fracos"]
    corte = datetime.now(timezone.utc) - timedelta(days=f["janela_dias"])
    por = defaultdict(list)
    for x in b:
        if x["canal"] and x["pub"] and x["pub"] >= corte:
            por[x["canal"]].append(x["views"])
    out, todos = {}, {}
    for cid, dst in pdx.destinos(c).items():
        vs = sorted(por.get(cid, []))
        if not vs:
            continue
        st = {"nome": dst["nome"], "idioma": dst["idioma"], "nicho": dst.get("nicho"), "n": len(vs),
              "mediana": vs[len(vs) // 2], "pct500": round(100 * sum(v >= 500 for v in vs) / len(vs)), "soma": sum(vs)}
        todos[cid] = st
        if st["n"] >= f["min_medidos"] and st["mediana"] < f["mediana_max"] and st["pct500"] <= f["pct500_max"]:
            out[cid] = st
    return out, todos


def virais(c, b, k):
    """Shorts nossos que viralizaram (mais views primeiro), com a fonte do parceiro que dá pra refazer."""
    fontes = {f["nome"]: f for f in c.get("fontes", [])}
    corte = datetime.now(timezone.utc) - timedelta(days=k["janela_dias"])
    out, vistos = [], set()
    for x in sorted(b, key=lambda x: -x["views"]):
        if x["views"] < k["min_views_48h"] or not x["pub"] or x["pub"] < corte or not x["fonte_id"]:
            continue
        if x["fonte_id"] in vistos or x["parceiro"] not in fontes:
            continue
        vistos.add(x["fonte_id"])
        out.append({**x, "fonte_cfg": fontes[x["parceiro"]]})
    return out


# ─────────────────────────── plano ───────────────────────────
def _ja_tem(its, reg, fonte_id):
    """Canais que já têm (ou já receberam) esta fonte: fichas na fila/postadas + registro."""
    tem = {x["canal"] for x in its if pdx._id_fonte(x["fonte"]) == fonte_id}
    return tem | set((reg.get(fonte_id) or {}).keys())


def _pode_receber(cid, its, k):
    if pdx._em_cooldown_limite(cid):
        return False, "esperando o limite diário de envios do YouTube"
    agora = datetime.now().timestamp()
    parados = [x for x in its if x["canal"] == cid and x["estado"] == "pronto"
               and agora - x["pj"].parent.stat().st_ctime > k["parado_max_dias"] * 86400]
    if parados:
        return False, f"{len(parados)} Short(s) pronto(s) parado(s) há > {k['parado_max_dias']} dias (canal não está subindo)"
    return True, ""


def plano(c=None, its=None, b=None, k=None, verbose=False):
    """Lista de tarefas [{viral, alvo (pt) ou None, linguas, motivo...}] e os pulados (com motivo)."""
    c = c or pdx.cfg()
    k = k or conf(c)
    its = its if its is not None else pdx.itens(c)
    b = b if b is not None else base()
    fracos, _ = canais_fracos(c, b, k)
    reg = _ler(REGISTRO, {})
    dst = pdx.destinos(c)
    tarefas, pulados = [], []
    # carga: quantas versões virais cada canal recebeu em 7 dias (+ as deste plano) — reparte entre os fracos em vez de
    # mandar tudo pro mais fraco
    semana = datetime.now().timestamp() - 7 * 86400
    carga = defaultdict(int)
    for por in reg.values():
        for cid, ts in por.items():
            if isinstance(ts, (int, float)) and ts > semana:
                carga[cid] += 1
    for v in virais(c, b, k):
        fc = v["fonte_cfg"]
        serve = [fc["tipo"]] + fc.get("nichos", [])
        ja = _ja_tem(its, reg, v["fonte_id"]) | {v["canal"]}
        cand_pt, cand_ling = [], []
        for cid, st in fracos.items():
            if cid in ja:
                continue
            ok, mot = _pode_receber(cid, its, k)
            if not ok:
                pulados.append((v["vid"], st["nome"], mot))
                continue
            if st["idioma"] == "pt":
                mesmo = st["nicho"] in serve
                if not mesmo and not k["aceitar_outro_nicho"]:
                    pulados.append((v["vid"], st["nome"], f"nicho '{st['nicho']}' x fonte {serve}"))
                    continue
                fila = sum(1 for x in its if x["canal"] == cid and x["estado"] in ("pronto", "esperando"))
                cand_pt.append((not mesmo, carga[cid], st["mediana"], fila, cid))
            elif fc["tipo"] not in pdx.LINGUA_SEM_NICHO:
                lang = next(l for l, d in c["idiomas"].items() if d["canal"] == cid)
                cand_ling.append((carga[cid], st["mediana"], lang, cid))
        cand_pt.sort()
        n = k["max_canais_por_viral"]
        # 1 produção = 1 versão pt (canal fraco pt) + as línguas fracas que cabem (a tradução sai do mesmo roteiro)
        alvo = cand_pt[0][-1] if cand_pt else None
        esc_l = sorted(cand_ling)[:max(0, n - (1 if alvo else 0))]
        linguas = [x[2] for x in esc_l]
        if not alvo and not linguas:
            continue
        for cid in [alvo] + [x[3] for x in esc_l]:
            if cid:
                carga[cid] += 1
        tarefas.append({"viral_vid": v["vid"], "views": v["views"], "canal_viral": dst.get(v["canal"], {}).get("nome", v["canal"]),
                        "fonte_id": v["fonte_id"], "fonte": v["fonte"], "parceiro": v["parceiro"], "tipo": fc["tipo"],
                        "fonte_url": fc["url"], "titulo": v["titulo"][:80], "alvo": alvo,
                        "alvo_nome": dst[alvo]["nome"] if alvo else None,
                        "nicho_alvo": fracos[alvo]["nicho"] if alvo else None,
                        "mesmo_nicho": (not cand_pt[0][0]) if alvo else None, "linguas": linguas})
    return tarefas, pulados, fracos


def _hoje(reg):
    corte = datetime.now().timestamp() - 24 * 3600
    return sum(1 for por in reg.values() for ts in por.values() if isinstance(ts, (int, float)) and ts > corte)


def _jsonl(obj):
    try:
        LOG_JSONL.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_JSONL, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(obj, ensure_ascii=False) + "\n")
    except OSError:
        pass


def rodada(c=None):
    """Chamado pela produção (parceiro_diario.producao) antes da produção normal. Devolve quantas versões produziu."""
    c = c or pdx.cfg()
    k = conf(c)
    if k["modo"] not in ("ensaio", "ligado"):
        return 0
    tarefas, _, fracos = plano(c, k=k)
    if not tarefas:
        pdx.log(f"virais->fracos [{k['modo']}]: nada a fazer ({len(fracos)} canais fracos)")
        return 0
    reg = _ler(REGISTRO, {})
    feitos = 0
    for t in tarefas:
        if feitos >= k["max_por_rodada"] or _hoje(reg) >= k["max_por_dia"]:
            break
        resumo = (f"viral {t['viral_vid']} ({t['views']} views em 48 h no {t['canal_viral']}, fonte {t['parceiro']} "
                  f"{t['fonte_id']} [{t['tipo']}]) -> {t['alvo_nome'] or '-'}"
                  + (f" (nicho {t['nicho_alvo']}{'' if t['mesmo_nicho'] else ', TESTE de outro nicho'})" if t["alvo"] else "")
                  + f" + línguas {t['linguas'] or '-'}")
        if k["modo"] == "ensaio":
            pdx.log(f"virais->fracos [ensaio]: FARIA {resumo}")
            _jsonl({"ts": datetime.now().isoformat(timespec="seconds"), "modo": "ensaio", **t})
            feitos += 1
            continue
        alvo = pdx.destinos(c)[t["alvo"]] if t["alvo"] else None
        if not alvo:  # só línguas: o pt sai no 1º canal fraco pt... sem nenhum, a versão pt iria pra um canal forte
            pdx.log(f"virais->fracos: {t['viral_vid']} só teria línguas e nenhum canal pt fraco livre — pulado")
            continue
        pdx.log(f"virais->fracos: PRODUZINDO {resumo}")
        antes = {str(x["pj"]) for x in pdx.itens(c)}
        rc = pdx._rodar_auto(c, alvo, t["linguas"], t["fonte_url"], t["tipo"], video_id=t["fonte_id"])
        novos = [x for x in pdx.itens(c) if str(x["pj"]) not in antes]
        marca = {"video": t["viral_vid"], "views_48h": t["views"], "canal": t["canal_viral"], "fonte_id": t["fonte_id"],
                 "mesmo_nicho": t["mesmo_nicho"], "em": datetime.now().isoformat(timespec="seconds")}
        for x in novos:
            try:
                pdx._gravar(x["pj"], viral_de=marca)
            except (OSError, ValueError) as e:
                pdx.log(f"virais->fracos: não marquei {x['pj']} ({e})")
        agora = datetime.now().timestamp()
        por = reg.setdefault(t["fonte_id"], {})
        for x in novos:
            por[x["canal"]] = agora
        if not novos:  # falhou: marca o alvo mesmo assim pra não insistir na mesma fonte a cada rodada
            por[t["alvo"]] = agora
        pdx._json_atomico(REGISTRO, reg)
        pdx.log(f"virais->fracos: rc={rc} | novos: " + (", ".join(f"{x['pj'].parent.name} -> {x['canal']}" for x in novos)
                                                          or "nenhum"))
        _jsonl({"ts": datetime.now().isoformat(timespec="seconds"), "modo": "ligado", "rc": str(rc),
                "novos": [str(x["pj"].parent.name) for x in novos], **t})
        feitos += 1
    return feitos


# ─────────────────────────── relatórios (CLI) ───────────────────────────
def relatorio_fontes(c=None, b=None, dias=21):
    """Placar por parceiro (fonte) e por tipo: Shorts do parceiro medidos em 48 h nos últimos `dias`."""
    c = c or pdx.cfg()
    b = b if b is not None else base()
    corte = datetime.now(timezone.utc) - timedelta(days=dias)
    tipo_de = {f["nome"]: f["tipo"] for f in c.get("fontes", [])}
    por_f, por_t = defaultdict(list), defaultdict(list)
    for x in b:
        if x["projeto"] != "parceiro" or not x["pub"] or x["pub"] < corte or not x["parceiro"]:
            continue
        por_f[x["parceiro"]].append(x["views"])
        por_t[x["tipo"] or tipo_de.get(x["parceiro"], "?")].append(x["views"])

    def st(vs):
        vs = sorted(vs)
        return {"n": len(vs), "mediana": vs[len(vs) // 2], "pct500": round(100 * sum(v >= 500 for v in vs) / len(vs)),
                "max": vs[-1], "soma": sum(vs)}
    return ({k: st(v) for k, v in por_f.items()}, {k: st(v) for k, v in por_t.items()})


def main():
    import argparse
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ensaio", action="store_true", help="mostra virais, canais fracos e o plano (não produz)")
    ap.add_argument("--fontes", action="store_true", help="placar por parceiro e por tipo")
    a = ap.parse_args()
    c = pdx.cfg()
    k = conf(c)
    b = base()
    if a.fontes:
        pf, pt = relatorio_fontes(c, b)
        print("TIPO               n  mediana  %>=500   max   soma")
        for t, s in sorted(pt.items(), key=lambda kv: kv[1]["pct500"]):
            print(f"{t:16} {s['n']:4} {s['mediana']:7} {s['pct500']:6}% {s['max']:6} {s['soma']:6}")
        print("\nPARCEIRO (fonte)    n  mediana  %>=500   max   soma   peso_atual")
        pesos = {f["nome"]: f.get("peso", 1) for f in c.get("fontes", [])}
        for f, s in sorted(pf.items(), key=lambda kv: (kv[1]["pct500"], -kv[1]["n"])):
            print(f"{f:18} {s['n']:4} {s['mediana']:7} {s['pct500']:6}% {s['max']:6} {s['soma']:6}   {pesos.get(f, '-')}")
        return
    print(f"modo no config: {k['modo']} | viral >= {k['min_views_48h']} views em 48 h nos últimos {k['janela_dias']} dias")
    vs = virais(c, b, k)
    print(f"\nVIRAIS com fonte refazível: {len(vs)}")
    for v in vs:
        print(f"  {v['views']:6} {v['vid']} canal={v['canal']} fonte={v['parceiro']}:{v['fonte_id']} [{v['fonte_cfg']['tipo']}] {v['titulo'][:60]}")
    tarefas, pulados, fracos = plano(c, b=b, k=k)
    _, todos = canais_fracos(c, b, k)
    print(f"\nCANAIS (últimos {k['fracos']['janela_dias']} dias; FRACO = n>={k['fracos']['min_medidos']}, mediana<"
          f"{k['fracos']['mediana_max']}, %>=500<={k['fracos']['pct500_max']}):")
    for cid, s in sorted(todos.items(), key=lambda kv: (kv[1]["pct500"], kv[1]["mediana"])):
        print(f"  {'FRACO' if cid in fracos else '     '} {s['nome'][:28]:28} [{s['idioma']}] nicho={s['nicho'] or '-':18} "
              f"n={s['n']:3} mediana={s['mediana']:5} %>=500={s['pct500']:3}% soma={s['soma']}")
    print(f"\nPLANO ({len(tarefas)} produções possíveis; por rodada {k['max_por_rodada']}, por dia {k['max_por_dia']}):")
    for t in tarefas:
        print(f"  {t['viral_vid']} ({t['views']} no {t['canal_viral']}) fonte {t['parceiro']}:{t['fonte_id']} [{t['tipo']}] -> "
              f"{t['alvo_nome'] or '-'}{'' if t['mesmo_nicho'] in (None, True) else ' (TESTE outro nicho: ' + str(t['nicho_alvo']) + ')'}"
              f" + línguas {t['linguas'] or '-'}")
    med = {x["vid"]: x["views"] for x in b}
    feitas = [x for x in pdx.itens(c) if x["d"].get("viral_de")]
    print(f"\nVERSÕES VIRAIS já produzidas: {len(feitas)}")
    for x in feitas:
        vid = str(x["d"].get("posted_url") or "").rsplit("/", 1)[-1]
        vd = x["d"]["viral_de"]
        print(f"  {x['pj'].parent.name} -> {x['canal']} [{x['estado']}] viral {vd.get('video')} ({vd.get('views_48h')}) | "
              f"views 48 h: {med.get(vid, 'ainda sem medida')}")
    if pulados:
        print("\nPULADOS (canal fraco que não pode receber agora):")
        for nome, mot in sorted({(p[1], p[2]) for p in pulados}):
            print(f"  {nome}: {mot}")


if __name__ == "__main__":
    main()
