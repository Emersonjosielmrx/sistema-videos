"""ranking_views.py — ranking de views de TODOS os vídeos por canal (YouTube), lendo estado\\videos_canais.json.

    python ranking_views.py            # usa o cache (1 h); imprime o ranking e grava os CSVs em relatorios\\
    python ranking_views.py --atualizar # coleta de novo pela API antes (~100 unidades de cota)
"""
import csv
import json
import statistics
import sys
from datetime import datetime
from pathlib import Path

if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = Path(__file__).resolve().parent
ORIGEM = BASE / "estado" / "videos_canais.json"
SAIDA = BASE / "relatorios"


def n(x):
    return f"{x:,}".replace(",", ".")


def main():
    if "--atualizar" in sys.argv:
        sys.path.insert(0, str(BASE))
        import videos_canais
        videos_canais.coletar()
    d = json.loads(ORIGEM.read_text(encoding="utf-8"))
    vs = d.get("videos", [])
    conf = d.get("conferencia") or {}
    por = {nome: [] for nome in conf}
    for v in vs:
        por.setdefault(v["canal"], []).append(v)

    linhas = []
    for nome, lst in por.items():
        views = [v["views"] for v in lst]
        topo = max(lst, key=lambda v: v["views"]) if lst else None
        c = conf.get(nome) or {}
        linhas.append({
            "canal": nome, "videos": len(lst), "views_total": sum(views),
            "media": round(sum(views) / len(views)) if views else 0,
            "mediana": int(statistics.median(views)) if views else 0,
            "max": max(views) if views else 0,
            "videos_1000+": sum(x >= 1000 for x in views),
            "views_total_canal_youtube": c.get("views_canal"),
            "melhor_video": topo["titulo"][:80] if topo else "",
            "melhor_video_id": topo["id"] if topo else "",
        })
    linhas.sort(key=lambda r: -r["views_total"])
    for i, r in enumerate(linhas, 1):
        r["posicao"] = i

    SAIDA.mkdir(parents=True, exist_ok=True)
    dia = datetime.now().strftime("%Y-%m-%d")
    arq_canais = SAIDA / f"ranking_canais_{dia}.csv"
    arq_videos = SAIDA / f"ranking_videos_por_canal_{dia}.csv"
    campos = ["posicao", "canal", "videos", "views_total", "media", "mediana", "max", "videos_1000+",
              "views_total_canal_youtube", "melhor_video", "melhor_video_id"]
    with open(arq_canais, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=campos, delimiter=";")
        w.writeheader()
        w.writerows(linhas)
    with open(arq_videos, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["canal", "posicao_no_canal", "views", "likes", "comentarios", "publicado", "titulo", "link"])
        for r in linhas:
            lst = sorted(por[r["canal"]], key=lambda v: -v["views"])
            for i, v in enumerate(lst, 1):
                w.writerow([r["canal"], i, v["views"], v.get("likes"), v.get("comentarios"),
                            (v.get("pub") or "")[:10], v["titulo"], f"https://youtu.be/{v['id']}"])

    print(f"Lido em {d.get('lido')} | {len(vs)} vídeos | {len(por)} canais | erros: {d.get('erros') or 'nenhum'}")
    print(f"Total de views: {n(sum(r['views_total'] for r in linhas))}\n")
    print(f"{'#':>2} {'Canal':<26}{'Vídeos':>7}{'Views':>11}{'Média':>8}{'Mediana':>8}{'Máx':>9}{'1000+':>6}")
    for r in linhas:
        print(f"{r['posicao']:>2} {r['canal'][:25]:<26}{r['videos']:>7}{n(r['views_total']):>11}{n(r['media']):>8}"
              f"{n(r['mediana']):>8}{n(r['max']):>9}{r['videos_1000+']:>6}")
    print("\nTOP 3 vídeos de cada canal:")
    for r in linhas:
        if not por[r["canal"]]:
            continue
        print(f"\n{r['posicao']}. {r['canal']}")
        for i, v in enumerate(sorted(por[r["canal"]], key=lambda v: -v["views"])[:3], 1):
            print(f"   {i}) {n(v['views']):>8}  {v['titulo'][:70]}  https://youtu.be/{v['id']}")
    print(f"\nCSV canais: {arq_canais}\nCSV vídeos: {arq_videos}")


if __name__ == "__main__":
    main()
