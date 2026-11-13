r"""garimpar_fontes.py — acha os RECAPS MAIS VISTOS do YouTube inteiro (anime, manhwa, manhua, webtoon, filme...) e põe na
lista de prioridade do alimentador (config/fontes_prioridade.json), por views (12/11, dona: "o alimentador tem que pegar
os vídeos mais vistos que seja possível recapar, sejam de anime, manhwa ou outro"). Antes ele só lia o @Manhwa_Fresh.

Uma vez por dia (tarefa GarimparFontes): BUSCAS do yt-dlp (1 por vez, pausa de 25 s — regra: sem rajada; respeita a
pausa do ytdlp_vez), junta, filtra e ordena por views:
  - duração 35-170 min (o que cabe numa sessão do Kaggle; LONGO_MAX_MIN do cliente);
  - views >= MIN_VIEWS (300 mil);
  - fora: escola/academia/bullying de colegial e título de conteúdo adulto (mesmo filtro do alimentador + extras);
  - não repete: já feito, já na lista, já ignorado/falhado (alimentar_estado.json), vídeo já postado.
Entram no FIM da lista atual (a ordem que a dona escolheu fica na frente), até MAX_NOVOS por dia.
GARIMPAR_FONTES=0 desliga.

    python garimpar_fontes.py          # garimpa e grava
    python garimpar_fontes.py --ver    # só mostra o que entraria
"""
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
CFG = AQUI.parent / "config" / "fontes_prioridade.json"
EST = AQUI / "alimentar_estado.json"
POSTADOS = AQUI / "longos_postados.json"
MIN_VIEWS = 300_000
MIN_MIN, MAX_MIN = 35, 170
MAX_NOVOS = 15
BUSCAS = [
    ("manhwa", "manhwa recap full"), ("manhwa", "manhwa recap apocalypse"), ("manhwa", "manhwa recap medieval kingdom"),
    ("manhwa", "manhua recap cultivation"), ("manhwa", "webtoon recap system dungeon"),
    ("anime", "anime recap full season"), ("anime", "anime recap isekai reincarnated"),
    ("anime", "anime recap overpowered mc"),
]
ESCOLA = re.compile(r"\b(school|academy|class(mate|room)?s?|bull(y|ies|ied)|student|teacher|high ?school|escola|"
                    r"academia|colegial|valent)", re.I)
ADULTO = re.compile(r"\b(hentai|ecchi|nsfw|18\+|harem\b.*\bschool|loli|incest)", re.I)


def _ja_conhecidos():
    ids = set()
    try:
        d = json.loads(CFG.read_text(encoding="utf-8"))
        ids |= {v["id"] for v in d.get("videos", [])} | set(d.get("ja_garimpados", []))
    except (OSError, ValueError):
        pass
    try:
        e = json.loads(EST.read_text(encoding="utf-8-sig"))
        ids |= set(e.get("enviados", {})) | set(e.get("ignorar", [])) | set(e.get("falhas", {}))
        ids |= set(e.get("longos_demais", []))
    except (OSError, ValueError):
        pass
    try:
        p = json.loads(POSTADOS.read_text(encoding="utf-8"))
        ids |= {x.get("nome", "")[:11] for x in p.get("postados", [])}
    except (OSError, ValueError):
        pass
    return ids


def buscar():
    sys.path.insert(0, r"D:\hipercool-materiais\comum")
    import ytdlp_vez
    achados = {}
    for tipo, q in BUSCAS:
        if ytdlp_vez.pausado():
            print("yt-dlp pausado (YouTube barrando o IP) — paro a busca aqui", flush=True)
            break
        cmd = [sys.executable, "-m", "yt_dlp", "--flat-playlist", "-J", f"ytsearch40:{q}"]
        px = ytdlp_vez.proxy_url()
        if px:
            cmd[3:3] = ["--proxy", px]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=240, encoding="utf-8", errors="replace",
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            ents = json.loads(r.stdout or "{}").get("entries") or []
        except Exception as e:  # noqa: BLE001
            print(f"busca '{q}' falhou ({type(e).__name__})", flush=True)
            ents = []
        for e in ents:
            vid, t = e.get("id"), e.get("title") or ""
            dur, views = (e.get("duration") or 0) / 60, e.get("view_count") or 0
            if not vid or len(vid) != 11 or ADULTO.search(t):
                continue
            # 12/11 dona ("por que bloquear o tema se deu muito bom? não seria usar mais ele?"): escola/bullying só sai
            # quando o original é fraco; com ESCOLA_MIN_VIEWS (1 mi) ou mais ele ENTRA. GARIMPO_ESCOLA=0 volta a barrar.
            if ESCOLA.search(t) and (os.environ.get("GARIMPO_ESCOLA", "1") == "0" or (e.get("view_count") or 0)
                                     < int(os.environ.get("ESCOLA_MIN_VIEWS", "1000000"))):
                continue
            if not (MIN_MIN <= dur <= MAX_MIN) or views < MIN_VIEWS:
                continue
            if "recap" not in t.lower() and "resumo" not in t.lower():
                continue
            achados[vid] = {"id": vid, "tipo": tipo, "canal": e.get("channel") or e.get("uploader") or "",
                            "views": views, "min": round(dur), "titulo": t[:110], "garimpado": time.strftime("%Y-%m-%d")}
        print(f"busca '{q}': {len(ents)} resultados", flush=True)
        time.sleep(25)
    return list(achados.values())


def main(ver):
    if os.environ.get("GARIMPAR_FONTES", "1") == "0":
        return
    conhecidos = _ja_conhecidos()
    novos = [v for v in buscar() if v["id"] not in conhecidos]
    novos.sort(key=lambda v: -v["views"])
    novos = novos[:MAX_NOVOS]
    for v in novos:
        print(f"  + {v['views']:>10,} views | {v['min']:>3} min | {v['tipo']:6} | {v['canal'][:20]:20} | {v['titulo'][:60]}")
    if ver or not novos:
        print(f"{len(novos)} novos{' (só mostrando)' if ver else ''}")
        return
    d = json.loads(CFG.read_text(encoding="utf-8"))
    d["videos"] = d.get("videos", []) + novos
    d["ja_garimpados"] = sorted(set(d.get("ja_garimpados", [])) | {v["id"] for v in novos})
    CFG.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(novos)} novos na lista de prioridade ({len(d['videos'])} no total)")


if __name__ == "__main__":
    main("--ver" in sys.argv)
