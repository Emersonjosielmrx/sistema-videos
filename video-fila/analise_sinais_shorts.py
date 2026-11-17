"""analise_sinais_shorts.py — quais ESCOLHAS de cada Short mexem nas views (13/11/2026).

Dona 13/11: "faça todas as melhorias possíveis na inteligência de postagens e de criação dos vídeos".
Para cada Short com 48 h+ (Studio): razão = views ÷ mediana do canal dele (tira o efeito "canal grande"). Agrupa a
razão por cada escolha gravada no postar.json (hora da postagem, dia da semana, duração, estilo de título, legenda,
gancho, formato, narrador...) e mostra a mediana da razão e a taxa de "acerto" (razão >= 2). Só leitura.

    python analise_sinais_shorts.py [--min 15] [--json]
Saída --json: estado\\sinais_shorts.json (usado por quem decide: horários, duração, estilos).
"""
import json
import statistics as st
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
else:
    sys.stdout = sys.stderr = open(Path(__file__).resolve().parent / "logs" / "sinais_shorts.log", "a", encoding="utf-8")
BASE = Path(__file__).resolve().parent
METR = Path(r"D:\postador-de-videos\_analise\metricas_studio.json")
LEDGER = Path(r"D:\postador-de-videos\logs\uploads_ledger.jsonl")
SAIDA = BASE / "estado" / "sinais_shorts.json"
CAMPOS = ("estilo_titulo", "legenda_estilo", "gancho_meio", "gancho_remotion", "fx_choque", "mascote", "curto",
          "fala_rapida", "saudacao", "ninguem_esperava", "teste_voz", "voz_base", "cobertura", "seo_versao", "midia",
          # 17/11 dona ("cruzar capa, dublador, obra, fonte... achar a receita do sucesso e testar se é ela ou sorte")
          "capa_pose", "capa_variante", "capa_no_inicio", "obra", "parceiro", "narrador")


def _dt(s):
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except ValueError:
        return None


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
        if (m.get("idade_h") or 0) < 48 or "completo" in (m.get("fonte") or ""):
            continue
        if m.get("erro") and not m.get("views"):
            continue
        x = led.get(vid, {})
        pj = {}
        if x.get("caminho"):
            try:
                pj = json.loads((Path(x["caminho"]).parent / "postar.json").read_text(encoding="utf-8"))
            except (OSError, ValueError):
                pj = {}
        quando = _dt(pj.get("agendado_para") or x.get("publish_at") or x.get("ts") or "")
        rl = m.get("ret_lista") or {}
        d = {"video": vid, "canal": m.get("canal_slug") or x.get("canal") or "?",
             "views": float(m.get("views") or rl.get("views") or 0),
             "continuaram": m.get("continuaram") if m.get("continuaram") is not None else rl.get("continuaram"),
             "pct": m.get("pct_media") if m.get("pct_media") is not None else rl.get("pct_media"),
             "dur": m.get("duracao_s") or m.get("duracao") or pj.get("duracao_s"),
             "titulo": m.get("titulo") or pj.get("titulo") or ""}
        if quando:
            loc = quando.astimezone()
            d["hora"] = loc.hour
            d["dia_semana"] = "seg ter qua qui sex sab dom".split()[loc.weekday()]
        for c in CAMPOS:
            if pj.get(c) is not None and pj.get(c) != "":
                d[c] = pj[c]
        if quando:
            d["_quando"] = quando.isoformat()
        d["projeto"] = m.get("fonte") or ""
        t = d["titulo"]
        d["titulo_len"] = "<=40" if len(t) <= 40 else "41-60" if len(t) <= 60 else "61-80" if len(t) <= 80 else ">80"
        d["titulo_pergunta"] = "?" in t
        d["titulo_caixa_alta"] = sum(1 for p in t.split() if len(p) > 3 and p.isupper()) >= 2
        d["titulo_emoji"] = any(ord(ch) > 0x1F000 for ch in t)
        linhas.append(d)
    por_canal = defaultdict(list)
    for l in linhas:
        por_canal[l["canal"]].append(l["views"])
    med = {c: st.median(v) for c, v in por_canal.items() if len(v) >= 5}
    out = []
    for l in linhas:
        if l["canal"] in med:
            l["razao"] = (l["views"] + 1) / (med[l["canal"]] + 1)
            out.append(l)
    return out


def tabela(linhas, campo, minimo):
    g = defaultdict(list)
    for l in linhas:
        if l.get(campo) is not None:
            g[str(l[campo])].append(l)
    rs = []
    for k, ls in g.items():
        if len(ls) < minimo:
            continue
        rz = [l["razao"] for l in ls]
        ct = [l["continuaram"] for l in ls if l.get("continuaram") is not None]
        rs.append({"valor": k, "n": len(ls), "razao_med": round(st.median(rz), 2),
                   "acerto": round(100 * sum(r >= 2 for r in rz) / len(rz)),
                   "zerado": round(100 * sum(l["views"] < 10 for l in ls) / len(ls)),
                   "continuaram": round(st.median(ct), 1) if ct else None})
    return sorted(rs, key=lambda r: -r["razao_med"])


def main():
    minimo = int(sys.argv[sys.argv.index("--min") + 1]) if "--min" in sys.argv else 15
    linhas = carregar()
    print(f"{len(linhas)} Shorts com 48 h+ em canais com >= 5 medidos")
    resumo = {}
    campos = ["hora", "dia_semana", "titulo_len", "titulo_pergunta", "titulo_caixa_alta", "titulo_emoji", *CAMPOS]
    for c in campos:
        rs = tabela(linhas, c, minimo)
        if len(rs) < 2:
            continue
        resumo[c] = rs
        print(f"\n=== {c}")
        print(f"{'valor':28} {'n':>4} {'razão':>6} {'acerto%':>7} {'zerado%':>7} {'contin%':>7}")
        for r in rs[:14]:
            print(f"{r['valor'][:28]:28} {r['n']:4} {r['razao_med']:6} {r['acerto']:7} {r['zerado']:7} {r['continuaram'] or '':>7}")
    # duração x retenção (se o Studio trouxe a duração)
    com_dur = [l for l in linhas if l.get("dur")]
    if len(com_dur) >= 30:
        for l in com_dur:
            d = float(l["dur"])
            l["faixa_dur"] = "<20s" if d < 20 else "20-30s" if d < 30 else "30-45s" if d < 45 else "45-60s" if d <= 60 else ">60s"
        rs = tabela(com_dur, "faixa_dur", minimo)
        resumo["faixa_dur"] = rs
        print("\n=== faixa_dur")
        for r in rs:
            print(f"{r['valor']:28} {r['n']:4} {r['razao_med']:6} {r['acerto']:7} {r['zerado']:7} {r['continuaram'] or '':>7}")
    receitas = receita_ou_sorte(linhas, campos, max(8, minimo // 2))
    print("\n=== RECEITAS (ganham nas DUAS metades do tempo = padrão; só numa = sorte)")
    for r in receitas[:25]:
        print(f"{r['veredito']:8} {r['campo']}={r['valor'][:30]:30} antigos {r['razao_antigos']} (n={r['n_antigos']}) "
              f"| recentes {r['razao_recentes']} (n={r['n_recentes']})")
    if "--json" in sys.argv:
        SAIDA.write_text(json.dumps({"_quando": datetime.now().isoformat(timespec="minutes"), "n": len(linhas),
                                     "sinais": resumo, "receitas": receitas}, ensure_ascii=False, indent=1),
                         encoding="utf-8")
        print(f"\n-> {SAIDA}")


DOC_RECEITAS = BASE / "RECEITAS_DO_SUCESSO.md"
_NOMES = {"hora": "hora da postagem", "parceiro": "fonte (parceiro)", "narrador": "voz", "capa_pose": "pose da capa",
          "capa_variante": "capa (variante)", "obra": "obra", "midia": "tipo de conteúdo", "dia_semana": "dia da semana"}


def gravar_receitas(minimo=15):
    """Roda o cruzamento e grava RECEITAS_DO_SUCESSO.md (pra dona ler) e o json (pra quem decide)."""
    linhas = carregar()
    campos = ["hora", "dia_semana", "titulo_len", "titulo_pergunta", "titulo_caixa_alta", "titulo_emoji", *CAMPOS]
    rec = receita_ou_sorte(linhas, campos, max(8, minimo // 2))
    try:
        atual = json.loads(SAIDA.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        atual = {}
    atual.update({"_quando": datetime.now().isoformat(timespec="minutes"), "n": len(linhas), "receitas": rec})
    SAIDA.write_text(json.dumps(atual, ensure_ascii=False, indent=1), encoding="utf-8")
    txt = [f"# Receitas do sucesso dos Shorts — {datetime.now():%d/%m %H:%M}", "",
           f"{len(linhas)} Shorts com 48 h+. Razão = views ÷ mediana do canal (1,0 = normal do canal). Os Shorts são "
           "divididos em 2 metades pela data: o que ganha nas DUAS é **receita** (repetiu, não foi sorte); o que ganha "
           "só numa é **sorte** (testar mais antes de apostar); o que perde nas duas é **evitar**.", ""]
    for ver, tit in (("RECEITA", "✅ Receitas confirmadas"), ("EVITAR", "⛔ Evitar"), ("SORTE", "🎲 Sorte (ainda não confirmou)")):
        txt += [f"## {tit}", "", "| sinal | valor | razão antigos (n) | razão recentes (n) |", "|---|---|---:|---:|"]
        for r in [r for r in rec if r["veredito"] == ver][:20]:
            txt.append(f"| {_NOMES.get(r['campo'], r['campo'])} | {r['valor']} | {r['razao_antigos']} ({r['n_antigos']}) "
                       f"| {r['razao_recentes']} ({r['n_recentes']}) |")
        txt.append("")
    DOC_RECEITAS.write_text("\n".join(txt), encoding="utf-8")
    return rec


def receita_ou_sorte(linhas, campos, minimo):
    """17/11 dona ("testar pra ver se é aquilo mesmo ou se foi sorte"): divide os Shorts em 2 metades pela DATA de
    postagem e mede cada valor de cada sinal nas duas. Mediana da razão >= 1,3 nas duas = RECEITA (repetiu); >= 1,3 só
    numa = SORTE (não repetiu); <= 0,77 nas duas = EVITAR. Ordena pelo menor das duas metades (o mais confiável)."""
    datadas = sorted((l for l in linhas if l.get("_quando")), key=lambda l: l["_quando"])
    if len(datadas) < 2 * minimo:
        return []
    meio = len(datadas) // 2
    metades = (datadas[:meio], datadas[meio:])
    out = []
    for c in campos:
        g = [defaultdict(list), defaultdict(list)]
        for i, parte in enumerate(metades):
            for l in parte:
                if l.get(c) is not None:
                    g[i][str(l[c])].append(l["razao"])
        for v in set(g[0]) & set(g[1]):
            a, b = g[0][v], g[1][v]
            if len(a) < minimo or len(b) < minimo:
                continue
            ma, mb = st.median(a), st.median(b)
            if ma >= 1.3 and mb >= 1.3:
                ver = "RECEITA"
            elif ma <= 0.77 and mb <= 0.77:
                ver = "EVITAR"
            elif max(ma, mb) >= 1.3:
                ver = "SORTE"
            else:
                continue
            out.append({"campo": c, "valor": v, "veredito": ver, "razao_antigos": round(ma, 2),
                        "razao_recentes": round(mb, 2), "n_antigos": len(a), "n_recentes": len(b)})
    ordem = {"RECEITA": 0, "EVITAR": 1, "SORTE": 2}
    return sorted(out, key=lambda r: (ordem[r["veredito"]], -min(r["razao_antigos"], r["razao_recentes"])))


if __name__ == "__main__":
    main()
