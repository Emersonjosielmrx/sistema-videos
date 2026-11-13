"""Correcao de 2026-10-04: o distribuir_videos.py postou 13 Shorts e deixou os arquivos na fila de prontos.

Sem isto, o ciclo das 06:40 (manhwareact.py publicar) postaria os mesmos videos de novo nos canais principais.
Para cada upload do ledger feito pelo distribuir_videos.py: grava em publicados.json (canal real) e move
mp4/postar.json/meta/thumb para hipercool-materiais/_postados/react/<canal>/ (mesmo formato do publish._arquivar).
Idempotente: o que ja foi arquivado e pulado.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, r"D:\manhwa-react")
from mr.common import load_config, load_json, save_json  # noqa: E402
from mr import publish as PB  # noqa: E402

cfg = load_config()
politica, _ = PB._postador(cfg)
reg = PB._carregar_registro(cfg)
por_nome = {it["mp4"].name: it for it in PB.prontos(cfg)}

feitos = 0
for r in politica._ler_ledger():
    if r.get("script") != "distribuir_videos.py":
        continue
    stem = Path(r["arquivo"]).stem
    it = por_nome.get(r["arquivo"])
    extra = {"video_id": r["video_id"], "url": f"https://youtu.be/{r['video_id']}", "canal": r["canal"],
             "canal_id": r["canal_id"], "publish_at": r.get("publish_at"), "postado_em": r["ts"], "thumb": "sem",
             "comentario": "sem", "comentario_texto": "", "canal_slug": it["slug"] if it else None,
             "titulo": it["dados"]["titulo"] if it else "", "script": "distribuir_videos.py",
             "nota": "postado pelo distribuir_videos.py (fora do nicho/politica); arquivado em 2026-10-04"}
    if stem not in reg:
        reg[stem] = extra
    if it:
        PB._arquivar(cfg, it, extra)
        feitos += 1
        print(f"arquivado: {it['slug']}/{r['arquivo']} -> {r['canal']} {extra['url']}")
    else:
        print(f"ja fora da fila: {r['arquivo']} ({r['canal']})")

save_json(reg, PB._registro_path(cfg))
print(f"\n{feitos} arquivo(s) movido(s); publicados.json com {len(reg)} registro(s)")
