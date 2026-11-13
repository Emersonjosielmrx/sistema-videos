"""analise_shorts_foco.py — onde cada TIPO de Short dá certo e onde dá errado (05/11/2026).

Dona 05/11: "analise os de shorts também, retenção e CTR e tudo mais, pra ver quais devemos produzir mais e quais menos
e focar nos que estão dando certo, e em quais canais determinado vídeo está dando certo e em qual está dando errado,
assim podemos focar os vídeos certos nos canais certos em vez de distribuir".

Cruza:
  D:\\postador-de-videos\\_analise\\metricas_studio.json  (Studio: views, continuaram %, % assistida, CTR — metricas_rede.py)
  D:\\postador-de-videos\\logs\\uploads_ledger.jsonl       (vídeo -> pasta)
  <pasta>\\postar.json                                     (midia = tipo do Short, parceiro = canal de origem)
Saída: relatorios\\shorts_foco_<data>.csv (1 linha por vídeo) + resumo na tela (canal x tipo, tipo, origem).

    python analise_shorts_foco.py [--min 3]
"""
import csv
import json
import statistics as st
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
else:  # pythonw (tarefa FocoShorts): sem console
    import os as _os
    sys.stdout = sys.stderr = open(Path(__file__).resolve().parent / "logs" / "foco_shorts.log", "a", encoding="utf-8")
BASE = Path(__file__).resolve().parent
METR = Path(r"D:\postador-de-videos\_analise\metricas_studio.json")
LEDGER = Path(r"D:\postador-de-videos\logs\uploads_ledger.jsonl")
SAIDA = BASE / "relatorios"


def _postar(caminho):
    if not caminho:
        return {}
    p = Path(caminho).parent / "postar.json"
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def carregar():
    metr = json.loads(METR.read_text(encoding="utf-8"))
    led = {}
    for l in LEDGER.read_text(encoding="utf-8").splitlines():
        try:
            x = json.loads(l)
        except ValueError:
            continue
        if x.get("video_id"):
            led[x["video_id"]] = x
    linhas = []
    for vid, m in metr.items():
        if m.get("erro") and not m.get("views"):
            continue
        if (m.get("idade_h") or 0) < 48:  # Short ainda subindo
            continue
        fonte = (m.get("fonte") or "")
        if "completo" in fonte:
            continue
        x = led.get(vid, {})
        pj = _postar(x.get("caminho"))
        tipo = pj.get("midia") or ("corte_longo" if "_cortes" in (x.get("caminho") or "") else
                                   (fonte.split()[0] if fonte else "?"))
        rl = m.get("ret_lista") or {}
        linhas.append({
            "video": vid, "canal": m.get("canal_slug") or x.get("canal") or "?", "tipo": tipo,
            "origem": pj.get("parceiro") or "", "fonte_url": pj.get("fonte") or "",
            "views": float(m.get("views") or rl.get("views") or 0),
            "continuaram": m.get("continuaram") if m.get("continuaram") is not None else rl.get("continuaram"),
            "pct_assistida": m.get("pct_media") if m.get("pct_media") is not None else rl.get("pct_media"),
            "dur_media": m.get("dur_media"), "titulo": (m.get("titulo") or pj.get("titulo") or "")[:90],
            "idade_h": m.get("idade_h"), "projeto": fonte})
    return linhas


def _med(v):
    v = [float(x) for x in v if x is not None]
    return round(st.median(v), 1) if v else None


def resumo(linhas, chave, minimo):
    g = defaultdict(list)
    for l in linhas:
        g[chave(l)].append(l)
    out = []
    for k, ls in g.items():
        if len(ls) < minimo:
            continue
        vs = [l["views"] for l in ls]
        out.append({"grupo": k, "n": len(ls), "views_med": _med(vs), "views_media": round(sum(vs) / len(vs)),
                    "acima_1000": sum(v >= 1000 for v in vs), "zerados": sum(v < 10 for v in vs),
                    "continuaram_med": _med([l["continuaram"] for l in ls]),
                    "pct_assistida_med": _med([l["pct_assistida"] for l in ls])})
    return sorted(out, key=lambda r: -(r["views_med"] or 0))


def imprimir(titulo, rs, n=40):
    print(f"\n=== {titulo}")
    print(f"{'grupo':44} {'n':>3} {'med':>6} {'média':>6} {'≥1k':>4} {'<10':>4} {'contin%':>7} {'assist%':>7}")
    for r in rs[:n]:
        g = r["grupo"] if isinstance(r["grupo"], str) else " | ".join(r["grupo"])
        print(f"{g[:44]:44} {r['n']:3} {r['views_med'] or 0:6.0f} {r['views_media']:6} {r['acima_1000']:4} "
              f"{r['zerados']:4} {r['continuaram_med'] or 0:7} {r['pct_assistida_med'] or 0:7}")


def main():
    minimo = int(sys.argv[sys.argv.index("--min") + 1]) if "--min" in sys.argv else 3
    linhas = carregar()
    SAIDA.mkdir(exist_ok=True)
    arq = SAIDA / f"shorts_foco_{datetime.now():%Y%m%d}.csv"
    with open(arq, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]), delimiter=";")
        w.writeheader()
        w.writerows(linhas)
    print(f"{len(linhas)} Shorts com 48 h+ e métricas do Studio -> {arq}")
    imprimir("POR TIPO", resumo(linhas, lambda l: l["tipo"], minimo))
    imprimir("POR CANAL", resumo(linhas, lambda l: l["canal"], minimo))
    imprimir("CANAL x TIPO", resumo(linhas, lambda l: (l["canal"], l["tipo"]), minimo), 70)
    imprimir("POR CANAL DE ORIGEM (parceiro)", resumo([l for l in linhas if l["origem"]], lambda l: l["origem"], minimo))
    if "--aplicar" in sys.argv:
        fontes_por_canal(linhas)
        aplicar(resumo(linhas, lambda l: (l["canal"], l["tipo"]), minimo),
                {r["grupo"]: r["views_med"] or 0 for r in resumo(linhas, lambda l: l["canal"], 1)})


FONTES_CANAL = Path(r"D:\recapd-ambientes\producao\estado\fontes_por_canal.json")


def fontes_por_canal(linhas):
    """12/11 dona ("usar mais o conteúdo que deu certo NAQUELE canal"): {cred_do_canal: {origem: razão}} — razão =
    mediana de views da origem (fonte do parceiro) NO canal ÷ mediana do canal, com >= 2 vídeos. O parceiro_diario.
    _escolher_fonte multiplica o peso da fonte por essa razão (limitada a 0,3–3)."""
    sys.path.insert(0, r"D:\postador-de-videos\bin")
    import youtube_web_poster as yw
    mapa = yw.ler_mapa()["canais"]
    g, por_canal = defaultdict(list), defaultdict(list)
    for l in linhas:
        if l["origem"]:
            g[(l["canal"], l["origem"])].append(l["views"])
        por_canal[l["canal"]].append(l["views"])
    out = {}
    for (slug, origem), vs in g.items():
        if len(vs) < 2:
            continue
        med_c = st.median(por_canal[slug]) or 1
        razao = round(max(0.3, min(3.0, (st.median(vs) + 1) / (med_c + 1))), 2)
        for cred in (mapa.get(slug) or {}).get("creds") or []:
            out.setdefault(cred, {})[origem] = razao
    FONTES_CANAL.write_text(json.dumps({"_quando": datetime.now().isoformat(timespec="minutes"), "canais": out},
                                       ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"fontes por canal: {sum(len(v) for v in out.values())} pares (canal, fonte) -> {FONTES_CANAL}")


PARCEIRO = Path(r"D:\recapd-ambientes\producao\config\parceiro.json")
FOCO_MIN_MED = 100  # tipo entra no foco do canal com mediana >= 100 views (com --min Shorts medidos)


def aplicar(canal_tipo, med_canal=None):
    """Grava em parceiro.json pt[i]["nichos_foco"] = {tipo: mediana} dos tipos que rendem NO canal (05/11, dona:
    "o tipo vai pro canal em que mais rende, independente do nome"). Canal sem tipo bom = sem foco (funil antigo).
    12/11 dona ("focar nos conteúdos que deram mais views NAQUELE canal"): além do corte fixo (>= 100), entra o tipo
    que rende >= 1,3x a mediana do PRÓPRIO canal (com >= 20 views) — os canais fracos também ganham foco. Roda todo
    dia (tarefa FocoShorts, 05:40)."""
    med_canal = med_canal or {}
    import shutil
    sys.path.insert(0, r"D:\postador-de-videos\bin")
    import youtube_web_poster as yw
    mapa = yw.ler_mapa()["canais"]
    cred_do_slug = {s: set(e.get("creds") or []) for s, e in mapa.items()}
    d = json.loads(PARCEIRO.read_text(encoding="utf-8"))
    nichos = {n for f in d.get("fontes", []) for n in [f["tipo"]] + f.get("nichos", [])}
    foco = defaultdict(dict)
    for r in canal_tipo:
        slug, tipo = r["grupo"]
        v = r["views_med"] or 0
        if tipo in nichos and (v >= FOCO_MIN_MED or (v >= 20 and v >= 1.3 * (med_canal.get(slug) or 0))):
            foco[slug][tipo] = r["views_med"]
    shutil.copy(PARCEIRO, PARCEIRO.with_name(f"parceiro.json.bak_foco_{datetime.now():%Y%m%d_%H%M}"))
    for c in d.get("pt", []):
        slug = next((s for s, creds in cred_do_slug.items() if c["canal"] in creds), None)
        if slug in foco:
            c["nichos_foco"] = foco[slug]
            print(f"foco: {c['nome']} <- {foco[slug]}")
        else:
            c.pop("nichos_foco", None)
    d["_nichos_foco_obs"] = (f"{datetime.now():%d/%m %H:%M} analise_shorts_foco.py --aplicar: tipo com mediana >= "
                             f"{FOCO_MIN_MED} views NO canal (Studio). Recalcular: rodar de novo.")
    PARCEIRO.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
