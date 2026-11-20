# -*- coding: utf-8 -*-
r"""services/facebook/paginas.py — LER Páginas do Facebook sem Chrome: seguidores e views de cada Reel (substitui a
leitura pelo navegador do postador-de-videos\bin\fb_medir.py).

Mapeado em 20/11 (HTML real da aba Reels, capturas\fb_reels_tab.html): o GET de
`profile.php?id=<id>&sk=reels_tab` já traz, no JSON embutido:
  - "N seguidores"                                    -> seguidores
  - aggregated_fb_shorts.edges[].profile_reel_node    -> cada Reel: video_id + "play_count_reduced" (views, texto
                                                          curto: "220", "1,2 mil", "3,4 mi")
  - delegate_page_id                                  -> o asset_id do Business Suite
Sem rolar a página o HTML traz os primeiros reels (as Páginas novas têm poucos). Para Página com dezenas de reels a
paginação é GraphQL (falta capturar o doc_id da rolagem).

    python -m services.facebook.paginas <conta> <page_id>
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from services.facebook.sessao import Sessao  # noqa: E402


def _num(t):
    """'1,2 mil' / '3,4 mi' / '904' / '1.234' / '1.2K' -> int"""
    t = (t or "").strip().casefold().replace("\xa0", " ")
    m = re.match(r"([\d.,]+)\s*(mil|mi|k|m)?", t)
    if not m:
        return None
    n, suf = m.group(1), m.group(2)
    if suf:
        n = float(n.replace(".", "").replace(",", ".")) if "," in n else float(n)
        return int(n * (1000 if suf in ("mil", "k") else 1_000_000))
    return int(n.replace(".", "").replace(",", ""))


def ler_pagina(sessao, page_id):
    """{"seguidores", "reels": [{"id", "views"}], "asset_id", "nome"} da Página, só com GET."""
    h = sessao.get(f"https://www.facebook.com/profile.php?id={page_id}&sk=reels_tab").text
    seg = re.search(r'"text":"([\d.,]+(?:\s*(?:mil|mi))?)\s+seguidor', h)
    asset = re.search(r'"delegate_page_id":"(\d+)"', h)
    nome = re.search(r'"name":"Reels de ([^"]+)"', h)
    reels, vistos = [], set()
    i = h.find("aggregated_fb_shorts")
    bloco = h[i:] if i >= 0 else ""
    # cada edge: video_id (no tracking) ... play_count_reduced. Corta o bloco por "profile_reel_node".
    for parte in bloco.split('"profile_reel_node"')[1:]:
        vid = re.search(r'\\"video_id\\":\\"(\d+)\\"', parte) or re.search(r'"video_id":"(\d+)"', parte)
        pc = re.search(r'"play_count_reduced":"([^"]+)"', parte)
        if vid and vid.group(1) not in vistos:
            vistos.add(vid.group(1))
            reels.append({"id": vid.group(1), "views": _num(pc.group(1)) if pc else None})
    sessao.salvar()
    return {"seguidores": _num(seg.group(1)) if seg else None, "reels": reels,
            "asset_id": asset.group(1) if asset else None, "nome": nome.group(1) if nome else None}


def conferir_config(conta):
    """Confere, sem Chrome, cada Página da conta em config\\facebook_paginas.json: a conta consegue AGIR como ela
    (i_user) e o asset_id da config bate com o delegate_page_id que o Facebook mostra. Substitui fb_page_id /
    fb_ativos / fb_entrar_como para conferir. Devolve [(chave, ok, detalhe)]."""
    cfg = json.loads(Path(r"D:\postador-de-videos\config\facebook_paginas.json").read_text("utf-8"))
    s = Sessao(conta)
    out = []
    for k, p in cfg["paginas"].items():
        if p.get("conta") != conta or not p.get("id"):
            continue
        try:
            tok = s.como(p["id"])
            r = ler_pagina(s, p["id"])
            ok = r["asset_id"] == str(p.get("asset_id"))
            out.append((k, ok, f"age como {tok['user']} | asset config {p.get('asset_id')} x Facebook {r['asset_id']} | "
                                f"{len(r['reels'])} reels, {r['seguidores']} seguidores"))
        except Exception as e:  # noqa: BLE001
            out.append((k, False, str(e)[:150]))
    s.como(None)
    return out


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if sys.argv[1:2] == ["conferir"]:
        for k, ok, det in conferir_config(sys.argv[2]):
            print(f"{'OK ' if ok else 'ERRO'} {k:16s} {det}")
    else:
        print(json.dumps(ler_pagina(Sessao(sys.argv[1]), sys.argv[2]), ensure_ascii=False, indent=1))
