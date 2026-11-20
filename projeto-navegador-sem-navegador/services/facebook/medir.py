# -*- coding: utf-8 -*-
r"""services/facebook/medir.py — medição das Páginas do Facebook SEM Chrome (mesma saída do
postador-de-videos\bin\fb_medir.py: logs\fb_views.jsonl + FACEBOOK_VISUALIZACOES.md, que a escada fb_escada.py lê).

Testado 20/11: Anime Noturno em 5,3 s por HTTP, mesmos reels/views que o Chrome mediu às 09:53.
Cada conta pela SAÍDA FIXA dela (services.facebook.sessao); as Páginas da mesma conta em sequência (é a mesma conta,
o mesmo IP — não é laço de contas). Sessão vencida = colhe de novo pelo Chrome UMA vez e segue.

    python -m services.facebook.medir            # todas as Páginas (no lugar do fb_medir.py)
    python -m services.facebook.medir anime_noturno dorama
"""
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from services.facebook.paginas import ler_pagina  # noqa: E402
from services.facebook.sessao import Bloqueio, Deslogado, Sessao, colher  # noqa: E402

POST = Path(r"D:\postador-de-videos")
CFG = POST / "config" / "facebook_paginas.json"
OUT = POST / "logs" / "fb_views.jsonl"


def medir(so=()):
    cfg = json.loads(CFG.read_text("utf-8"))
    pags = {k: p for k, p in cfg["paginas"].items() if (not so or k in so) and not p.get("pausada") and p.get("id")}
    por_conta = {}
    for k, p in pags.items():
        por_conta.setdefault(p["conta"], []).append(k)
    feitas = 0
    for conta, chaves in por_conta.items():  # uma conta por vez, cada uma na saída dela
        try:
            s = Sessao(conta)
        except (Deslogado, SystemExit) as e:
            print(f"[{conta}] sem sessão: {e}", flush=True)
            continue
        recolheu = False
        for k in chaves:
            try:
                r = ler_pagina(s, pags[k]["id"])
            except Deslogado:
                if recolheu:
                    print(f"[{conta}] deslogada mesmo depois de colher — parei esta conta", flush=True)
                    break
                print(f"[{conta}] sessão vencida — colhendo de novo pelo Chrome", flush=True)
                colher(conta)
                s, recolheu = Sessao(conta), True
                r = ler_pagina(s, pags[k]["id"])
            except Bloqueio as e:
                print(f"[{conta}] BLOQUEIO: {e} — parei esta conta", flush=True)
                break
            except Exception as e:  # noqa: BLE001
                print(f"[{k}] falhou: {str(e)[:150]}", flush=True)
                continue
            linha = {"seguidores": r["seguidores"], "reels": [x for x in r["reels"] if x["views"] is not None],
                     "pagina": k, "nome": pags[k]["nome"], "quando": datetime.now().isoformat(timespec="seconds"),
                     "fonte": "http"}
            with open(OUT, "a", encoding="utf-8") as f:
                f.write(json.dumps(linha, ensure_ascii=False) + "\n")
            feitas += 1
            print(f"[{pags[k]['nome']}] seguidores {r['seguidores']} | reels {len(linha['reels'])} | "
                  f"views {sum(x['views'] for x in linha['reels'])}", flush=True)
    if OUT.exists():  # o relatório é o mesmo do fb_medir (reaproveita a função de lá)
        sys.path.insert(0, str(POST / "bin"))
        import fb_medir
        fb_medir.relatorio()
    return feitas


if __name__ == "__main__":
    if sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    # código 0 = mediu alguma Página; 3 = nenhuma (o cron cai no fb_medir.py com Chrome)
    sys.exit(0 if medir(sys.argv[1:]) else 3)
