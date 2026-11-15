r"""pesar_fila.py — 14/11 dona ("tem que ter essas métricas automáticas pra IA analisar e pesar os próximos da fila"):
reordena config\fontes_prioridade.json pelo DESEMPENHO REAL dos nossos longos por TEMA.

Para cada tema (campo "tema" da fila; nos postados, deduzido do título original da obra) mede, pelo painel :8790:
  - horas assistidas por longo (views x duração média assistida) — o que o YouTube conta pra monetizar (4.000 h)
  - views por dia
nota = 0,6 x (horas/longo normalizadas) + 0,4 x (views/dia normalizadas). Tema sem dado = nota média (não some da fila).
Dentro do mesmo tema mantém a ordem que já estava (views da fonte). Série que a dona acompanha (serie=medieval) vai
pro fim (dona 13/11 23h: "pode parar de focar no Medieval").

Grava estado\pesos_temas.json (a tabela que o relatório mostra) e reordena a fila (backup antes).
    python pesar_fila.py          # pesa e reordena
    python pesar_fila.py --ver    # só mostra a tabela
PESAR_FILA=0 desliga (não mexe na fila).
"""
import json
import os
import re
import shutil
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
CFG = AQUI.parent / "config" / "fontes_prioridade.json"
POSTADOS = AQUI / "longos_postados.json"
PESOS = Path(r"D:\video-fila\estado\pesos_temas.json")
FICHAS = Path(r"D:\hipercool-materiais\animes recap\na_nuvem")

# palavras do título ORIGINAL (inglês, da obra) -> tema. A ordem importa: o primeiro que casa vence.
TEMAS_RX = [
    ("jardineiro_academia", r"academ|janitor|gardener|arrogant student|underestimat|staff"),
    ("ex_arrependida", r"\bex\b|girlfriend|dumped|regret|betray|cheat|divorce|wife"),
    ("sistema_dinheiro", r"money|rich|billion|million|spend|wealth|gold|cash|debt|bought"),
    ("medieval_tecnologia", r"medieval age|technolog|develop the|engineer"),
    ("loot_box_sistema", r"loot|gacha|chest"),
    ("renasce_rico_forte", r"reborn|regress|return|reincarnat"),
]


def tema_do(titulo):
    t = (titulo or "").lower()
    return next((n for n, rx in TEMAS_RX if re.search(rx, t)), "outros")


def medir():
    post = json.loads(POSTADOS.read_text(encoding="utf-8"))["postados"]
    rank = {v["id"]: v for v in json.loads(urllib.request.urlopen(
        "http://127.0.0.1:8790/api/ranking?dias=60", timeout=140).read().decode("utf-8")).get("videos", [])}
    por = {}
    for p in post:
        yid = str(p.get("url", "")).rstrip("/").split("/")[-1].split("?")[0]
        v = rank.get(yid)
        if not v or v.get("views") is None:
            continue
        # título original da obra: na ficha (nuvem.json) ou o nome da pasta (id_titulo_em_ingles)
        orig = ""
        try:
            orig = json.loads((FICHAS / p["nome"] / "nuvem.json").read_text(encoding="utf-8")).get("titulo_original", "")
        except (OSError, ValueError, KeyError):
            orig = p.get("nome", "")[12:].replace("_", " ")
        tema = tema_do(orig)
        try:
            dias = max((datetime.now() - datetime.fromisoformat(p["em"])).total_seconds() / 86400, 0.5)
        except (KeyError, ValueError):
            continue
        horas = v["views"] * float(v.get("dur_media") or 0) / 3600
        d = por.setdefault(tema, {"longos": 0, "views": 0, "horas": 0.0, "vd": 0.0})
        d["longos"] += 1
        d["views"] += v["views"]
        d["horas"] += horas
        d["vd"] += v["views"] / dias
    for d in por.values():
        d["horas_por_longo"] = round(d["horas"] / d["longos"], 2)
        d["vd_por_longo"] = round(d["vd"] / d["longos"], 2)
        d["horas"] = round(d["horas"], 1)
        d["vd"] = round(d["vd"], 1)
    mh = max((d["horas_por_longo"] for d in por.values()), default=1) or 1
    mv = max((d["vd_por_longo"] for d in por.values()), default=1) or 1
    for d in por.values():
        d["nota"] = round(0.6 * d["horas_por_longo"] / mh + 0.4 * d["vd_por_longo"] / mv, 3)
    return por


def main(ver):
    try:
        por = medir()
    except Exception as e:  # noqa: BLE001 — painel :8790 lento/fora: usa a última pesagem em vez de falhar
        try:
            por = json.loads(PESOS.read_text(encoding="utf-8"))["temas"]
            print(f"painel não respondeu ({type(e).__name__}) — uso a pesagem anterior")
        except (OSError, ValueError, KeyError):
            print(f"painel não respondeu ({type(e).__name__}) e não há pesagem anterior — fila fica como está")
            return
        ver = ver or False
        mostrar_e_aplicar(por, ver, gravar=False)
        return
    mostrar_e_aplicar(por, ver, gravar=True)


def mostrar_e_aplicar(por, ver, gravar):
    if gravar:
        PESOS.write_text(json.dumps({"em": datetime.now().isoformat(timespec="minutes"), "temas": por},
                                    ensure_ascii=False, indent=1), encoding="utf-8")
    print("tema | longos | views | horas | h/longo | views/dia/longo | NOTA")
    for t, d in sorted(por.items(), key=lambda kv: -kv[1]["nota"]):
        print(f"{t} | {d['longos']} | {d['views']} | {d['horas']} | {d['horas_por_longo']} | {d['vd_por_longo']} | {d['nota']}")
    if ver or os.environ.get("PESAR_FILA", "1") == "0":
        return
    cfg = json.loads(CFG.read_text(encoding="utf-8"))
    vs = cfg.get("videos", [])
    media = sum(d["nota"] for d in por.values()) / len(por) if por else 0.5

    def chave(iv):
        i, v = iv
        if v.get("serie") == "medieval":
            return (1, 0, i)  # série no fim (dona 13/11)
        t = v.get("tema") or tema_do(v.get("titulo", ""))
        return (0, -(por.get(t, {}).get("nota", media)), i)

    novo = [v for _, v in sorted(enumerate(vs), key=chave)]
    if [v["id"] for v in novo] == [v["id"] for v in vs]:
        print("fila já está na ordem certa")
        return
    shutil.copy2(CFG, CFG.with_name(f"fontes_prioridade.json.bkp_{time.strftime('%Y%m%d_%H%M')}_pesar"))
    cfg["videos"] = novo
    cfg["_leia_pesar"] = ("14/11 dona: fila pesada pelo desempenho REAL por tema (horas assistidas 60% + views/dia "
                          "40%) — pesar_fila.py; tabela em video-fila\\estado\\pesos_temas.json.")
    CFG.write_text(json.dumps(cfg, ensure_ascii=False, indent=1), encoding="utf-8")
    print("fila reordenada; 1ºs:", [f"{(v.get('tema') or tema_do(v.get('titulo','')))}:{v['titulo'][:30]}" for v in novo[:6]])


if __name__ == "__main__":
    main("--ver" in sys.argv)
