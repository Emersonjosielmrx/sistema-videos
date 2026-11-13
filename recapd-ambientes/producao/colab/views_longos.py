"""views_longos.py — views de cada longo postado (página pública do vídeo, sem chave de API; 1 pedido a cada 3 s, nunca em
rajada). Grava colab\\views_longos.json {yt_id: {views, canal, lido}} e devolve {canal_nome: {views, longos, views_por_longo}}.
Usado pelo postar_longos (02/11 dona: "proporção de vídeos postados por views ganhas — quem dá mais recebe mais").

    python views_longos.py        # lê agora e mostra a tabela por canal
"""
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
POSTADOS = AQUI / "longos_postados.json"
ARQ = AQUI / "views_longos.json"
MAX_IDADE_H = 6  # releitura do mesmo vídeo no máximo a cada 6 h


def _ler_views(yid):
    import requests
    r = requests.get(f"https://www.youtube.com/watch?v={yid}", timeout=20,
                     headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                              "Accept-Language": "pt-BR,pt;q=0.9"})
    m = re.search(r'"viewCount":"(\d+)"', r.text)
    return int(m.group(1)) if m else None


def atualizar():
    post = json.loads(POSTADOS.read_text(encoding="utf-8")).get("postados", [])
    try:
        cache = json.loads(ARQ.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        cache = {}
    agora = datetime.now()
    for p in post:
        yid = str(p.get("url", "")).rstrip("/").split("/")[-1].split("?")[0].split("=")[-1]
        if not yid:
            continue
        c = cache.get(yid) or {}
        try:
            idade = (agora - datetime.fromisoformat(c["lido"])).total_seconds() / 3600
        except (KeyError, ValueError):
            idade = 999
        if idade < MAX_IDADE_H:
            continue
        try:
            v = _ler_views(yid)
        except Exception:  # noqa: BLE001
            v = None
        if v is not None:
            cache[yid] = {"views": v, "canal": p.get("canal_nome"), "cred": p.get("canal"), "lido": agora.isoformat("T", "minutes"),
                          "postado": p.get("em")}
        time.sleep(3)
    ARQ.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
    return cache


def por_canal(cache=None):
    cache = cache if cache is not None else json.loads(ARQ.read_text(encoding="utf-8"))
    out = {}
    for y in cache.values():
        c = out.setdefault(y["cred"], {"canal": y["canal"], "views": 0, "longos": 0})
        c["views"] += y["views"]
        c["longos"] += 1
    for c in out.values():
        c["views_por_longo"] = round(c["views"] / max(1, c["longos"]), 1)
    return out


if __name__ == "__main__":
    tab = por_canal(atualizar())
    for cred, c in sorted(tab.items(), key=lambda x: -x[1]["views"]):
        print(f"{c['canal']:28} {c['longos']} longos  {c['views']:>7} views  {c['views_por_longo']:>8} por longo")
    sys.exit(0)
