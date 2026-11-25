r"""Mede views dos Reels e seguidores das Páginas pela Graph API (25/11/2026) — complementa services.facebook.medir.

Cada conta pela SAÍDA FIXA dela (fb_reel_api._sessao); as Páginas da mesma conta em sequência (mesma conta, mesmo IP —
não é laço de contas). Usa `read_insights` (blue_reels_play_count) se o app tiver; sem ela usa o campo
"views", que bate com a medição HTTP (25/11: Bicho 1231 x 1232). Grava 1 linha por Página em logs\fb_views.jsonl com "fonte": "api".

    python fb_medir_api.py                 # todas as Páginas com token
    python fb_medir_api.py <chave> ...     # só estas
"""
import json
import sys
from datetime import datetime
from pathlib import Path

BIN = Path(__file__).resolve().parent
sys.path.insert(0, str(BIN))
import fb_reel_api as A  # noqa: E402

OUT = BIN.parent / "logs" / "fb_views.jsonl"
CFG = BIN.parent / "config" / "facebook_paginas.json"
METRICAS = ("blue_reels_play_count", "fb_reels_total_plays", "post_impressions_unique")


def _views_reel(s, rid, tok):
    r = s.get(f"{A.G}/{rid}/video_insights", params={"access_token": tok}, timeout=30).json()
    if "data" in r:
        vals = {m.get("name"): (m.get("values") or [{}])[0].get("value") for m in r["data"]}
        for m in METRICAS:
            if isinstance(vals.get(m), (int, float)):
                return int(vals[m]), "insights"
    r = s.get(f"{A.G}/{rid}", params={"fields": "views", "access_token": tok}, timeout=30).json()
    return int(r.get("views") or 0), "campo"


def medir(so=()):
    cfg = json.loads(CFG.read_text(encoding="utf-8"))["paginas"]
    por_conta = {}
    for k, p in cfg.items():
        if p.get("pausada") or (so and k not in so) or not A.token_pagina(p["conta"], p["asset_id"]):
            continue
        por_conta.setdefault(p["conta"], []).append(k)
    for conta, chaves in por_conta.items():  # uma conta por vez, cada uma pela saída dela
        s = A._sessao(conta)
        for k in chaves:
            p = cfg[k]
            tok = A.token_pagina(conta, p["asset_id"])
            try:
                pag = s.get(f"{A.G}/{p['asset_id']}", params={"fields": "followers_count", "access_token": tok},
                            timeout=30).json()
                lst = s.get(f"{A.G}/{p['asset_id']}/video_reels", params={"fields": "id", "limit": 100,
                                                                             "access_token": tok}, timeout=30).json()
                reels, fontes = [], set()
                for v in lst.get("data", []):
                    n, f = _views_reel(s, v["id"], tok)
                    reels.append({"id": v["id"], "views": n}); fontes.add(f)
            except Exception as e:  # noqa: BLE001
                print(f"[{p['nome']}] falhou: {str(e)[:120]}", flush=True); continue
            linha = {"seguidores": pag.get("followers_count"), "reels": reels, "pagina": k, "nome": p["nome"],
                     "quando": datetime.now().isoformat(timespec="seconds"), "fonte": "api",
                     "metrica": "insights" if fontes == {"insights"} else ("misto" if "insights" in fontes else "campo")}
            with open(OUT, "a", encoding="utf-8") as f:
                f.write(json.dumps(linha, ensure_ascii=False) + "\n")
            print(f"[{p['nome']}] seguidores {linha['seguidores']} | reels {len(reels)} | views "
                  f"{sum(r['views'] for r in reels)} ({linha['metrica']})", flush=True)


if __name__ == "__main__":
    if sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    medir(tuple(sys.argv[1:]))
