r"""garimpar_parecidos.py — acha recaps PARECIDOS com os longos que deram certo e põe na frente da fila, já com o canal
onde o parecido deu certo (12/11, dona: "esse último do InventoReact deu muito bom assim como o Medieval Age deu
certo no Fio da Meada; procure mais obras assim — sistema de gastar dinheiro com mulheres, sistema que ganha
dinheiro, ex-namorada humilhada, elementos similares — e põe lá pra ver se conseguimos replicar o resultado").

Campeões medidos (views_longos.json, 12/11):
  InventoReact  516  "His Ex Girlfriend wanted to Return when..."     -> ex arrependida / humilhada
  Fio da Meada  380  "(3) He got into the Medieval Age..."           -> engenheiro/tecnologia em reino medieval
  Fio da Meada  192  "The Fist King Reborn 100x Stronger and Richer" -> renasce mais forte e RICO
  Fio da Meada  109  "He Opens Loot Boxes in his Safe Hideout..."    -> caixas de prêmio / ex fugindo de zumbi
  Fio da Meada   85  "The Girl who Betrayed him Wanted to Return"    -> traidora quer voltar

Cada TEMA tem buscas (yt-dlp, 1 por vez, pausa de 25 s — sem rajada; respeita ytdlp_vez) e o canal de destino.
Filtro: 35-170 min, >= MIN_VIEWS, "recap"/"resumo" no título, sem adulto, sem repetir (mesmo conhecido do
garimpar_fontes). Entram LOGO DEPOIS da série Medieval na fontes_prioridade.json (antes dos mais vistos genéricos),
com "canal_destino"; o cliente.py grava esse canal no nuvem.json e o postar_longos só posta nele.
GARIMPAR_PARECIDOS=0 desliga.

    python garimpar_parecidos.py          # garimpa e grava
    python garimpar_parecidos.py --ver    # só mostra
"""
import json
import os
import re
import sys
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import garimpar_fontes as gf  # noqa: E402  (mesmo filtro e mesma lista de já conhecidos)

MIN_VIEWS = 150_000
POR_TEMA = 3
FIO, INVENTO = "novo_codigo_inteligente_n7j", "novo_ia_agora_h3n"
TEMAS = [
    # (tema, canal, buscas, palavras que o título precisa ter pelo menos uma)
    ("ex_arrependida", INVENTO,
     ["manhwa recap ex girlfriend regret", "manhwa recap ex girlfriend wanted to return", "manhwa recap girlfriend dumped him rich"],
     r"\bex\b|girlfriend|dumped|regret|betray|cheat|wife"),
    ("sistema_dinheiro", INVENTO,
     ["manhwa recap money system", "manhwa recap spend money system women", "manhwa recap billionaire system"],
     r"money|rich|billion|million|spend|wealth|gold|cash|debt"),
    ("loot_box_sistema", FIO,
     ["manhwa recap loot box system", "manhwa recap gacha system apocalypse"],
     r"loot|box|gacha|chest|drop|item"),
    ("medieval_tecnologia", FIO,
     ["manhwa recap medieval technology modern knowledge", "manhwa recap reincarnated noble kingdom develop"],
     r"medieval|kingdom|empire|lord|noble|territor|technolog|develop|engineer"),
    ("renasce_rico_forte", FIO,
     ["manhwa recap reborn stronger richer", "manhwa recap regressor revenge rich"],
     r"reborn|regress|return|richer|rich|revenge"),
]


def buscar_tema(q, rx):
    sys.path.insert(0, r"D:\hipercool-materiais\comum")
    import ytdlp_vez
    if ytdlp_vez.pausado():
        return None
    import subprocess
    cmd = [sys.executable, "-m", "yt_dlp", "--flat-playlist", "-J", f"ytsearch30:{q}"]
    px = ytdlp_vez.proxy_url()
    if px:
        cmd[3:3] = ["--proxy", px]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=240, encoding="utf-8", errors="replace",
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        ents = json.loads(r.stdout or "{}").get("entries") or []
    except Exception as e:  # noqa: BLE001
        print(f"busca '{q}' falhou ({type(e).__name__})", flush=True)
        return []
    out = []
    for e in ents:
        vid, t = e.get("id"), e.get("title") or ""
        dur, views = (e.get("duration") or 0) / 60, e.get("view_count") or 0
        if not vid or len(vid) != 11 or gf.ADULTO.search(t) or not re.search(rx, t, re.I):
            continue
        if not (gf.MIN_MIN <= dur <= gf.MAX_MIN) or views < MIN_VIEWS:
            continue
        if "recap" not in t.lower() and "resumo" not in t.lower():
            continue
        out.append({"id": vid, "canal": e.get("channel") or e.get("uploader") or "", "views": views,
                    "min": round(dur), "titulo": t[:110]})
    print(f"busca '{q}': {len(ents)} resultados, {len(out)} servem", flush=True)
    return out


def main(ver):
    if os.environ.get("GARIMPAR_PARECIDOS", "1") == "0":
        return
    conhecidos = gf._ja_conhecidos()
    escolhidos = []
    for tema, canal, buscas, rx in TEMAS:
        achados = {}
        for q in buscas:
            res = buscar_tema(q, rx)
            if res is None:
                print("yt-dlp pausado — paro aqui", flush=True)
                break
            for v in res:
                if v["id"] not in conhecidos and v["id"] not in {x["id"] for x in escolhidos}:
                    achados[v["id"]] = v
            time.sleep(25)
        top = sorted(achados.values(), key=lambda v: -v["views"])[:POR_TEMA]
        for v in top:
            v.update(tipo="manhwa", canal_destino=canal, tema=tema, garimpado=time.strftime("%Y-%m-%d"),
                     parecido=True)
            print(f"  + [{tema}] {v['views']:>10,} | {v['min']:>3} min | -> {canal} | {v['titulo'][:60]}", flush=True)
        escolhidos += top
    if ver or not escolhidos:
        print(f"{len(escolhidos)} parecidos{' (só mostrando)' if ver else ''}")
        return
    d = json.loads(gf.CFG.read_text(encoding="utf-8"))
    vs = d.get("videos", [])
    # logo depois da série que a dona acompanha (forcar_longo), antes dos mais vistos genéricos
    i = max((k + 1 for k, v in enumerate(vs) if v.get("forcar_longo") or "SÉRIE" in (v.get("titulo") or "")), default=0)
    d["videos"] = vs[:i] + escolhidos + vs[i:]
    d["ja_garimpados"] = sorted(set(d.get("ja_garimpados", [])) | {v["id"] for v in escolhidos})
    d["_leia_parecidos"] = ("12/11 dona: obras PARECIDAS com as que deram certo (ex arrependida/sistema de dinheiro -> "
                            "InventoReact; medieval/loot box/renasce rico -> Fio da Meada). garimpar_parecidos.py; "
                            "canal_destino = onde posta.")
    gf.CFG.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(escolhidos)} parecidos na frente da lista (posição {i})")


if __name__ == "__main__":
    main("--ver" in sys.argv)
