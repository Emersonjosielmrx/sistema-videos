r"""medir_cortes.py — 15/11 dona ("os cortes dos longos postados em Shorts estão valendo a pena ou só enchendo linguiça?").
Mediana de views (API do YouTube, só leitura, mesma do painel :8790) dos CORTES DO LONGO e dos Shorts de PARCEIRO por
canal, desde 31/10. Grava cortes_x_parceiro.json, que postar_longos._corte_nao_rende usa pra decidir em que canal o
corte sai (o corte gasta a mesma vaga diária do parceiro). Tarefa MedirCortes 1x/dia.
    python medir_cortes.py
"""
import json
import re
import statistics
import sys
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, r"D:\video-fila")
import painel_controlador as pc  # noqa: E402

DESDE = datetime(2026, 10, 31)


def main():
    cortes = {}
    for linha in (AQUI / "postar_longos.log").read_text(encoding="utf-8", errors="ignore").splitlines():
        m = re.search(r"cortes: (.+?) corte_\d+\.mp4 — ok: https://youtu\.be/(\S+)", linha)
        if m:
            cortes[m.group(2)] = m.group(1)
    canal_de = {}
    for r in pc._ler_jsonl(pc.LEDGER):
        vid = r.get("video_id")
        q = pc._abre_em(r) if vid else None
        if vid and vid not in cortes and q and q.replace(tzinfo=None) >= DESDE \
                and "animes recap\\shorts" in str(r.get("caminho", "")):
            canal_de[vid] = r.get("canal")
    api = pc._yt_videos(list(cortes) + list(canal_de))

    def views(i):
        s = (api.get(i) or {}).get("statistics") or {}
        return int(s["viewCount"]) if "viewCount" in s else None
    ct, pa = {}, {}
    for i, c in cortes.items():
        if views(i) is not None:
            ct.setdefault(c, []).append(views(i))
    for i, c in canal_de.items():
        if views(i) is not None:
            pa.setdefault(c, []).append(views(i))
    out = {"medido": datetime.now().isoformat(timespec="minutes"),
           "cortes": {c: statistics.median(v) for c, v in ct.items()},
           "cortes_n": {c: len(v) for c, v in ct.items()},
           "parceiro": {c: statistics.median(v) for c, v in pa.items()},
           "parceiro_n": {c: len(v) for c, v in pa.items()}}
    (AQUI / "cortes_x_parceiro.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(cortes)} cortes e {len(canal_de)} Shorts de parceiro medidos em {len(ct)} canais")


if __name__ == "__main__":
    main()
