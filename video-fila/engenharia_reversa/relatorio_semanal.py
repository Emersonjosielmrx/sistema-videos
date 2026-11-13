"""Relatório SEMANAL da engenharia reversa (29/10). Sem IA, sem yt-dlp: compara os Shorts publicados nos últimos 7
dias com os 7 anteriores (views de 48–120 h), por canal, nicho, idioma e faixa de hora; diz o que subiu, o que caiu
e de onde veio a mudança (mix: postou mais em canal/hora ruim, ou o mesmo canal piorou). Grava
relatorios/<data>.md e manda um resumo curto pelo portão do Telegram (rotina, vai no resumo 9h/14h/21h).

    python relatorio_semanal.py [--sem-telegram] [--fim AAAA-MM-DD]
"""
import argparse
import json
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

AQUI = Path(__file__).parent
sys.path.insert(0, r"D:\hipercool-materiais\comum")
import sem_janela  # noqa: E402,F401

sys.path.insert(0, str(AQUI))
from dados_nossos import BR, L, led  # noqa: E402
RELS = AQUI / "relatorios"


def faixa(h):
    return ("0-5" if h < 6 else "6-10" if h < 11 else "11-14" if h < 15 else "15-18" if h < 19
            else "19-21" if h < 22 else "22-23") if h is not None else "?"


def enriquecer():
    out = []
    for x in L:
        r = led[x["vid"]]
        try:
            f = json.loads((Path(r["caminho"]).parent / "postar.json").read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            f = {}
        try:
            dt = datetime.fromisoformat((r.get("publish_at") or r["ts"]).replace("Z", "+00:00")).astimezone(BR)
        except Exception:  # noqa: BLE001
            continue
        out.append({**x, "canal": r.get("canal") or x["canal"], "dt": dt, "nicho": f.get("midia") or x["projeto"], "idioma": f.get("idioma") or "?",
                    "faixa": faixa(x["hora"])})
    return out


def taxa(xs):
    return sum(x["v"] >= 500 for x in xs) / len(xs) if xs else 0.0


def bloco(xs):
    return f"n {len(xs)} · ≥500 {taxa(xs):.0%} · mediana {statistics.median([x['v'] for x in xs]) if xs else 0:.0f}"


def comparar(agora, antes, campo, minimo=3):
    ga, gb = defaultdict(list), defaultdict(list)
    for x in agora:
        ga[x[campo]].append(x)
    for x in antes:
        gb[x[campo]].append(x)
    linhas = []
    for k in set(ga) | set(gb):
        a, b = ga.get(k, []), gb.get(k, [])
        if len(a) >= minimo and len(b) >= minimo:
            linhas.append((taxa(a) - taxa(b), k, a, b))
    linhas.sort(key=lambda t: -t[0])
    return linhas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sem-telegram", action="store_true")
    ap.add_argument("--fim", help="último dia da semana (padrão: hoje − 2, para todos já terem 48 h)")
    a = ap.parse_args()
    fim = (datetime.fromisoformat(a.fim).replace(tzinfo=BR) if a.fim
           else datetime.now(BR).replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=2)) + timedelta(days=1)
    ini, ini_antes = fim - timedelta(days=7), fim - timedelta(days=14)
    xs = enriquecer()
    agora = [x for x in xs if ini <= x["dt"] < fim]
    antes = [x for x in xs if ini_antes <= x["dt"] < ini]
    t = [f"# Engenharia reversa — semana {ini:%d/%m} a {fim - timedelta(days=1):%d/%m}",
         "", f"Gerado {datetime.now(BR):%d/%m %H:%M} por `{Path(__file__).name}` (views de 48–120 h; ≥500 = passou o lote de teste).", "",
         f"- Esta semana: {bloco(agora)}", f"- Semana anterior: {bloco(antes)}", ""]
    resumo = [f"Engenharia reversa {ini:%d/%m}–{fim - timedelta(days=1):%d/%m}: ≥500 {taxa(antes):.0%} → {taxa(agora):.0%} "
              f"({len(agora)} Shorts)"]
    # de onde veio a mudança: mix (peso de cada grupo mudou) x desempenho (o mesmo grupo piorou/melhorou)
    for campo, titulo in (("canal", "Canal"), ("nicho", "Nicho"), ("idioma", "Idioma"), ("faixa", "Hora (BR)")):
        linhas = comparar(agora, antes, campo)
        t += [f"## {titulo}", "", "| grupo | antes | agora | mudança |", "|---|---|---|---|"]
        for d, k, a_, b_ in linhas:
            t.append(f"| {k} | {bloco(b_)} | {bloco(a_)} | {d:+.0%} |")
        t.append("")
        if linhas and campo in ("canal", "faixa"):
            sobe, cai = linhas[0], linhas[-1]
            if sobe[0] > 0.1:
                resumo.append(f"subiu {titulo.lower()} {sobe[1]} ({sobe[0]:+.0%})")
            if cai[0] < -0.1:
                resumo.append(f"caiu {titulo.lower()} {cai[1]} ({cai[0]:+.0%})")
    # mix de hora: quanto da semana foi para as faixas que a análise achou ruins (19–21 h)
    ruim = lambda l: sum(x["faixa"] == "19-21" for x in l) / len(l) if l else 0  # noqa: E731
    t += ["## Mix de hora", "", f"Shorts às 19–21 h (faixa ruim em 6 de 6 canais, 29/10): antes {ruim(antes):.0%}, "
          f"agora {ruim(agora):.0%}.", ""]
    top = sorted(agora, key=lambda x: -x["v"])[:5]
    t += ["## Os 5 melhores da semana", ""] + [f"- {x['v']:.0f} — {x['canal']} {x['nicho']} {x['dt']:%d/%m %H:%M} — "
                                               f"{x['titulo'][:80]}" for x in top] + [""]
    RELS.mkdir(exist_ok=True)
    arq = RELS / f"{fim - timedelta(days=1):%Y-%m-%d}.md"
    arq.write_text("\n".join(t), encoding="utf-8")
    print("\n".join(t))
    if not a.sem_telegram and agora:
        sys.path.insert(0, r"D:\video-fila")
        import avisos
        avisos.enviar("; ".join(resumo) + f". Detalhe: {arq}", "engenharia_reversa")


if __name__ == "__main__":
    main()
