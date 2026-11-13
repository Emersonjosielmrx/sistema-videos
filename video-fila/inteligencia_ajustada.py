"""inteligencia_ajustada.py — notas de FONTE e de NARRADOR sem o efeito do horário (13/11/2026).

Dona 13/11: "faça todas as melhorias possíveis na inteligência de postagens e de criação dos vídeos".
Achado (1.300 Shorts de parceiro com 48 h+): o post das 21-23 h de Brasília rende ~100x o do resto do dia nos canais
fracos. As notas antigas (views ÷ mediana do canal) misturavam isso: fonte/voz que caiu mais vezes à noite parecia
ótima (kkvirjao: "melhor" no ranking geral e 6 views de mediana à noite), e a boa que só saiu de dia parecia ruim.

Aqui cada Short é comparado só com os do MESMO canal no MESMO período (noite 21-23 h x resto):
    razão = (views + 1) ÷ (mediana do grupo + 1)          grupo com < 4 vídeos = mediana do canal inteiro
e a nota de cada fonte/voz é a média geométrica das razões, puxada pra 1 quando há poucos vídeos.

Grava (todo dia, pela tarefa FocoShorts — analise_shorts_foco.py --aplicar):
  recapd\\estado\\fontes_por_canal.json   {"canais": {cred: {fonte: 0,3-3}}, "geral": {fonte: 0,4-2,5}}
        -> parceiro_diario._escolher_fonte (peso da fonte no canal; sem dado do canal usa o geral) e nota_pronto
  recapd\\estado\\narradores_ajustado.json {"vozes": {voz: [nota log2 -1,5..1,5, n]}}
        -> anime_voz_clonada.ranking_geral (escolha e corte de voz); VOZ_RANKING_AJUSTADO=0 volta ao antigo

    python inteligencia_ajustada.py            # grava e mostra o resumo
    python inteligencia_ajustada.py --ver      # só mostra
"""
import json
import math
import statistics as st
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
ESTADO = Path(r"D:\recapd-ambientes\producao\estado")
NOITE = (21, 22, 23)


def linhas_ajustadas():
    import analise_sinais_shorts as a
    ls = [l for l in a.carregar() if l.get("projeto") == "parceiro short" and "hora" in l]
    grupo, canal = defaultdict(list), defaultdict(list)
    for l in ls:
        l["noite"] = l["hora"] in NOITE
        grupo[(l["canal"], l["noite"])].append(l["views"])
        canal[l["canal"]].append(l["views"])
    for l in ls:
        g = grupo[(l["canal"], l["noite"])]
        base = st.median(g) if len(g) >= 4 else st.median(canal[l["canal"]])
        # teto de 8x pra cima e pra baixo: 1 vídeo que explodiu (ou zerou) não decide a nota sozinho
        l["rz"] = max(0.125, min(8.0, (l["views"] + 1) / (base + 1)))
    return ls


def _nota(razoes, neutros, piso, teto):
    """Média geométrica puxada pra 1 por `neutros` vídeos imaginários de razão 1."""
    s = sum(math.log(r) for r in razoes)
    return round(max(piso, min(teto, math.exp(s / (len(razoes) + neutros)))), 2)


def calcular():
    ls = linhas_ajustadas()
    sys.path.insert(0, r"D:\postador-de-videos\bin")
    import youtube_web_poster as yw
    mapa = yw.ler_mapa()["canais"]
    por_cf, por_f, por_v = defaultdict(list), defaultdict(list), defaultdict(list)
    for l in ls:
        if l.get("parceiro"):
            por_cf[(l["canal"], l["parceiro"])].append(l["rz"])
            por_f[l["parceiro"]].append(l["rz"])
        if l.get("narrador"):
            por_v[l["narrador"]].append(l["rz"])
    canais = {}
    for (slug, fonte), rz in por_cf.items():
        if len(rz) < 2:
            continue
        n = _nota(rz, 2, 0.3, 3.0)
        for cred in (mapa.get(slug) or {}).get("creds") or []:
            canais.setdefault(cred, {})[fonte] = n
    geral = {f: _nota(rz, 3, 0.4, 2.5) for f, rz in por_f.items() if len(rz) >= 4}
    vozes = {v: [round(max(-1.5, min(1.5, sum(math.log2(r) for r in rz) / (len(rz) + 3))), 3), len(rz)]
             for v, rz in por_v.items() if len(rz) >= 2}
    return {"n": len(ls), "canais": canais, "geral": geral, "vozes": vozes,
            "_n_fonte": {f: len(rz) for f, rz in por_f.items()}}


def gravar():
    r = calcular()
    quando = datetime.now().isoformat(timespec="minutes")
    ESTADO.mkdir(parents=True, exist_ok=True)
    (ESTADO / "fontes_por_canal.json").write_text(json.dumps(
        {"_quando": quando, "_como": "razão no mesmo canal e mesmo período (noite 21-23 h x resto); inteligencia_ajustada.py",
         "canais": r["canais"], "geral": r["geral"]}, ensure_ascii=False, indent=1), encoding="utf-8")
    (ESTADO / "narradores_ajustado.json").write_text(json.dumps(
        {"_quando": quando, "_como": "média de log2(razão ajustada), 3 neutros; inteligencia_ajustada.py",
         "vozes": r["vozes"]}, ensure_ascii=False, indent=1), encoding="utf-8")
    # cópia em config\ (vai junto pro PC2/PC3 no scp do ocioso: lá não há métricas pra calcular)
    (ESTADO.parent / "config" / "narradores_ajustado.json").write_text(
        (ESTADO / "narradores_ajustado.json").read_text(encoding="utf-8"), encoding="utf-8")
    return r


def relatorio():
    """INTELIGENCIA_SHORTS.md (todo dia): a prova do horário nobre por canal + melhores/piores fontes e vozes já
    ajustadas. É o que a dona e os chats leem pra conferir se as regras continuam valendo."""
    ls = linhas_ajustadas()
    canais = defaultdict(lambda: {"n": [], "r": []})
    for l in ls:
        canais[l["canal"]]["n" if l["noite"] else "r"].append(l["views"])
    r = calcular()
    out = [f"# Inteligência dos Shorts — {datetime.now():%d/%m/%Y %H:%M}", "",
           f"{len(ls)} Shorts de parceiro com 48 h+ (Studio). Gerado por `video-fila/inteligencia_ajustada.py` "
           "(tarefa FocoShorts, 05:40).", "",
           "## Horário nobre (21-23 h de Brasília) x resto do dia — mediana de views no MESMO canal", "",
           "| Canal | Noite | n | Resto | n | Noite ÷ resto |", "|---|---|---|---|---|---|"]
    ganha = perde = 0
    for c, d in sorted(canais.items(), key=lambda x: -len(x[1]["n"])):
        if len(d["n"]) >= 4 and len(d["r"]) >= 4:
            mn, mr = st.median(d["n"]), st.median(d["r"])
            ganha += mn > mr
            perde += mn < mr
            out.append(f"| {c} | {mn:.0f} | {len(d['n'])} | {mr:.0f} | {len(d['r'])} | {(mn + 1) / (mr + 1):.1f}x |")
    out += ["", f"**A noite ganha em {ganha} canais e perde em {perde}.** Se isso inverter, rever HORARIO_NOBRE_BR "
            "(parceiro_diario._ordem_horarios).", "",
            "## Fontes (nota sem o efeito do horário; 1,00 = normal do canal)", "",
            "Melhores: " + ", ".join(f"{f} {n} ({r['_n_fonte'][f]})" for f, n in
                                     sorted(r["geral"].items(), key=lambda x: -x[1])[:12]), "",
            "Piores: " + ", ".join(f"{f} {n} ({r['_n_fonte'][f]})" for f, n in
                                   sorted(r["geral"].items(), key=lambda x: x[1])[:12]), "",
            "## Narradores (log2 da razão ajustada; 0 = normal, +1 = dobro, -1 = metade; entre parênteses, vídeos)", "",
            "Melhores: " + ", ".join(f"{v} {x[0]:+.2f} ({x[1]})" for v, x in
                                     sorted(r["vozes"].items(), key=lambda x: -x[1][0])[:12] if x[1] >= 5), "",
            "Piores: " + ", ".join(f"{v} {x[0]:+.2f} ({x[1]})" for v, x in
                                   sorted(r["vozes"].items(), key=lambda x: x[1][0])[:12] if x[1] >= 5), ""]
    (BASE / "INTELIGENCIA_SHORTS.md").write_text(chr(10).join(out) + chr(10), encoding="utf-8")


def main():
    if sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    r = calcular() if "--ver" in sys.argv else gravar()
    print(f"{r['n']} Shorts | {sum(len(v) for v in r['canais'].values())} pares canal x fonte | "
          f"{len(r['geral'])} fontes no geral | {len(r['vozes'])} vozes")
    g = sorted(r["geral"].items(), key=lambda x: -x[1])
    print("fontes melhores:", [(f, n, r["_n_fonte"][f]) for f, n in g[:8]])
    print("fontes piores:  ", [(f, n, r["_n_fonte"][f]) for f, n in g[-8:]])
    v = sorted(r["vozes"].items(), key=lambda x: -x[1][0])
    print("vozes melhores:", [(k, *x) for k, x in v[:8]])
    print("vozes piores:  ", [(k, *x) for k, x in v[-8:]])


if __name__ == "__main__":
    main()
