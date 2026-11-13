#!/usr/bin/env python3
"""gerar_dossies.py — Le os JSON de _analise/ e gera:
  - _analise/dossies/<handle>.md  (1 dossie por canal)
  - _analise/TABELA_MESTRE.md     (roteamento canal->nicho->formato->publico->receita)

Publico real (idade/sexo/pais/trafego) vem cru do Analytics (sem IA).
Gemini so classifica TEMA e escreve a RECEITA DE PRODUCAO por canal.
"""
import json
import sys
import re
from pathlib import Path

if sys.stdout:  # pythonw (tarefa agendada) não tem stdout

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BIN = Path(__file__).resolve().parent
sys.path.insert(0, str(BIN))

ANALISE = Path(r"D:\postador-de-videos\_analise")
DOSSIES = ANALISE / "dossies"
DOSSIES.mkdir(parents=True, exist_ok=True)


def pct_sexo(idade_sexo):
    m = sum(r[2] for r in idade_sexo if r[1] == "male")
    f = sum(r[2] for r in idade_sexo if r[1] == "female")
    return round(m, 1), round(f, 1)


def top_faixa(idade_sexo):
    agg = {}
    for faixa, _, v in idade_sexo:
        agg[faixa] = agg.get(faixa, 0) + v
    return sorted(agg.items(), key=lambda x: -x[1])[:3]


def resumo_publico(a):
    if not a or not a.get("idade_sexo"):
        return "sem dados de audiencia"
    m, f = pct_sexo(a["idade_sexo"])
    faixas = ", ".join(f"{k}={v:.0f}%" for k, v in top_faixa(a["idade_sexo"]))
    paises = ", ".join(f"{p[0]}" for p in a.get("paises", [])[:3])
    trafego = a.get("trafego", [[None]])[0][0] if a.get("trafego") else "?"
    disp = a.get("dispositivo", [[None]])[0][0] if a.get("dispositivo") else "?"
    return f"{m:.0f}% masc / {f:.0f}% fem | faixas: {faixas} | paises: {paises} | trafego#1: {trafego} | {disp}"


import collections

USE_GEMINI = "--no-gemini" not in sys.argv


def heuristica(nome, info):
    """Classificacao sem IA: tags mais comuns + duracao + idioma pelo pais."""
    d = info["derivadas"]
    a = info.get("analytics", {})
    # tags/palavras mais comuns nos titulos+tags
    cont = collections.Counter()
    for v in info.get("videos", []):
        for t in v.get("tags", []):
            cont[t.lower().strip()] += 1
    # palavras dos titulos dos top10
    for t in d.get("top10", []):
        for w in re.findall(r"[a-zA-Zà-úÀ-Ú]{4,}", t["t"].lower()):
            if w not in ("shorts", "short", "video", "para", "como", "https"):
                cont[w] += 1
    top_tags = [k for k, _ in cont.most_common(6)]
    # idioma pelo pais dominante
    pais = a.get("paises", [["BR"]])[0][0] if a.get("paises") else "BR"
    idioma = {"BR": "pt-BR", "US": "en", "ES": "es", "MX": "es",
              "IN": "hi", "RU": "ru", "IT": "it", "FR": "fr"}.get(pais, "pt-BR")
    dur = d.get("dur_mediana_seg", 0)
    fmt = f"short ~{dur}s" if dur <= 65 else f"longo ~{dur}s"
    return {
        "nicho": ", ".join(top_tags[:3]) or "(indefinido)",
        "sub_temas": top_tags[:5],
        "o_que_rende": f"Top videos giram em torno de: {', '.join(top_tags[:4])}. "
                       f"Media {d['views_media']}v; melhores passam de {d['views_max']}v.",
        "formato_ideal": fmt,
        "idioma": idioma,
        "receita_vo3_historias": f"Fabricar {('shorts' if dur<=65 else 'videos')} de tema "
                                 f"[{', '.join(top_tags[:3])}] em {idioma}, ~{dur}s, "
                                 f"mirando publico {('masc' if _masc(a)>50 else 'fem')} {pais}.",
        "frequencia_sugerida": f"~{max(1, round(30/(d.get('cadencia_dias_mediana') or 1)))}/mes"
                               if d.get("cadencia_dias_mediana") else "?",
        "_fonte": "heuristica",
    }


def _masc(a):
    if not a.get("idade_sexo"):
        return 50
    m = sum(r[2] for r in a["idade_sexo"] if r[1] == "male")
    f = sum(r[2] for r in a["idade_sexo"] if r[1] == "female")
    return round(m/(m+f)*100) if (m+f) else 50


def classificar_gemini(nome, info):
    """Gemini se disponivel; senao heuristica sobre dados reais."""
    if not USE_GEMINI:
        return heuristica(nome, info)
    d = info["derivadas"]
    tops = "\n".join(f"  {t['views']}v: {t['t']}" for t in d.get("top10", [])[:8])
    pub = resumo_publico(info.get("analytics", {}))
    prompt = (
        f"Voce e estrategista de canais YouTube. Analise ESTE canal e responda em JSON.\n\n"
        f"Canal: {nome}\n"
        f"Inscritos: {info['inscritos']} | media views: {d['views_media']} | "
        f"shorts/longos: {d['n_shorts']}/{d['n_longos']} | dur mediana: {d['dur_mediana_seg']}s\n"
        f"Publico real: {pub}\n"
        f"TOP videos (views):\n{tops}\n\n"
        f'Responda SO um JSON: {{"nicho": "", "sub_temas": [], "o_que_rende": "", '
        f'"formato_ideal": "", "idioma": "", "receita_vo3_historias": "", "frequencia_sugerida": ""}}'
    )
    try:
        import gemini_llm
        resp = gemini_llm.generate_text(prompt, max_tokens=600)
        js = re.search(r"\{.*\}", resp, re.DOTALL)
        r = json.loads(js.group(0))
        r["_fonte"] = "gemini"
        return r
    except Exception:  # noqa
        h = heuristica(nome, info)
        h["_fonte"] = "heuristica(gemini-falhou)"
        return h


def dossie_md(info, cls):
    d = info["derivadas"]
    a = info.get("analytics", {})
    nome = info["nome"]
    h = info.get("handle", "")
    L = []
    L.append(f"# {info.get('titulo_canal', nome)}  ({h})")
    L.append(f"\n**Canal (credencial):** {nome}")
    L.append(f"**Link:** https://youtube.com/{h}" if h else "")
    L.append(f"\n## Numeros")
    L.append(f"- Inscritos: **{info['inscritos']}** | Views totais: {info['views_totais']} | Videos: {info['n_videos']}")
    L.append(f"- Media views/video: **{d['views_media']}** | mediana: {d['views_mediana']} | max: {d['views_max']}")
    L.append(f"- Shorts/Longos: {d['n_shorts']}/{d['n_longos']} | dur mediana: {d['dur_mediana_seg']}s")
    L.append(f"- Engajamento medio: {d['engajamento_medio_pct']}% | cadencia: {d.get('cadencia_dias_mediana')} dias entre posts")
    L.append(f"\n## Publico real (Analytics 365d)")
    if a.get("idade_sexo"):
        m, f = pct_sexo(a["idade_sexo"])
        L.append(f"- Sexo: **{m:.0f}% masc / {f:.0f}% fem**")
        L.append(f"- Faixas etarias: " + ", ".join(f"{k}={v:.0f}%" for k, v in top_faixa(a["idade_sexo"])))
        L.append(f"- Paises: " + ", ".join(f"{p[0]}({p[1]})" for p in a.get("paises", [])[:5]))
        L.append(f"- Trafego: " + ", ".join(f"{t[0]}({t[1]})" for t in a.get("trafego", [])[:4]))
        L.append(f"- Dispositivo: " + ", ".join(f"{x[0]}({x[1]})" for x in a.get("dispositivo", [])[:4]))
    else:
        L.append("- (sem dados de audiencia)")
    L.append(f"\n## Top 5 videos")
    for t in d.get("top10", [])[:5]:
        L.append(f"- **{t['views']}v** ({t['eng%']}% eng, {t['dur']}s) — {t['t']}  `youtu.be/{t['id']}`")
    L.append(f"\n## Estrategia (IA)")
    L.append(f"- **Nicho:** {cls.get('nicho','?')}")
    L.append(f"- **Sub-temas:** {', '.join(cls.get('sub_temas', []))}")
    L.append(f"- **O que rende:** {cls.get('o_que_rende','?')}")
    L.append(f"- **Formato ideal:** {cls.get('formato_ideal','?')}")
    L.append(f"- **Idioma:** {cls.get('idioma','?')}")
    L.append(f"- **Frequencia:** {cls.get('frequencia_sugerida','?')}")
    L.append(f"\n### RECEITA — o que fabricar pra este canal")
    L.append(f"> {cls.get('receita_vo3_historias','?')}")
    return "\n".join(x for x in L if x is not None)


def main():
    jsons = sorted(ANALISE.glob("*.json"))
    linhas_tabela = []
    print(f"Gerando dossies de {len(jsons)} canais...\n")
    for jf in jsons:
        info = json.loads(jf.read_text(encoding="utf-8"))
        nome = info["nome"]
        cls = classificar_gemini(nome, info)
        md = dossie_md(info, cls)
        (DOSSIES / f"{jf.stem}.md").write_text(md, encoding="utf-8")
        a = info.get("analytics", {})
        m, f = pct_sexo(a["idade_sexo"]) if a.get("idade_sexo") else (0, 0)
        pais = a.get("paises", [["?"]])[0][0] if a.get("paises") else "?"
        linhas_tabela.append({
            "handle": info.get("handle", jf.stem),
            "nicho": cls.get("nicho", "?"),
            "formato": cls.get("formato_ideal", "?"),
            "idioma": cls.get("idioma", "?"),
            "publico": f"{m:.0f}M/{f:.0f}F {pais}",
            "media": info["derivadas"]["views_media"],
            "insc": info["inscritos"],
            "freq": cls.get("frequencia_sugerida", "?"),
            "receita": cls.get("receita_vo3_historias", "?"),
        })
        print(f"  [OK] {jf.stem[:28]:<29} nicho={cls.get('nicho','?')[:22]}")

    # tabela mestre
    linhas_tabela.sort(key=lambda x: -x["media"])
    T = ["# TABELA-MESTRE — Roteamento por Canal\n",
         "Ordenado por media de views. Use pra fabricar VO3/historias sob medida.\n",
         "| Canal | Nicho | Formato | Idioma | Publico | Media | Insc | Freq |",
         "|---|---|---|---|---|---|---|---|"]
    for r in linhas_tabela:
        T.append(f"| {r['handle']} | {r['nicho']} | {r['formato']} | {r['idioma']} | "
                 f"{r['publico']} | {r['media']} | {r['insc']} | {r['freq']} |")
    T.append("\n## Receitas de producao (o que fabricar)\n")
    for r in linhas_tabela:
        T.append(f"- **{r['handle']}** ({r['nicho']}): {r['receita']}")
    (ANALISE / "TABELA_MESTRE.md").write_text("\n".join(T), encoding="utf-8")
    print(f"\nDossies em {DOSSIES}")
    print(f"Tabela-mestre: {ANALISE / 'TABELA_MESTRE.md'}")


if __name__ == "__main__":
    main()
