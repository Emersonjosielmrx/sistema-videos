#!/usr/bin/env python3
"""medir_metricas.py — Coletor CENTRAL de views/likes dos videos postados.

Fecha o loop de aprendizado: cada projeto (veo, historias, animes/recap) grava
posted_url quando posta; este coletor le esses posted_url, busca as metricas
REAIS via OAuth (mesmo motor do stats_views — sem YOUTUBE_API_KEY, sem adivinhar
video_id) e escreve de volta no formato de cada projeto.

Descoberta-chave: QUALQUER token OAuth valido le stats publicos de QUALQUER video
por id (videos.list?part=statistics&id=...). Entao basta 1 token que renova pra
medir todos os videos, de todos os canais.

Fontes de posted_url:
  - veo         : D:\\veo\\beta\\logs\\video_cache.json  (item.metrics.posted_url)
  - materiais   : D:\\hipercool-materiais\\**\\postar.json  (campo posted_url)
                  (recap/animes/historias postados pelo driver central)

Writeback:
  - veo         : metrics_client.update_cache_metrics(id, {views,likes,comments,...})
  - materiais   : grava views/likes no proprio postar.json
  - ranking     : D:\\postador-de-videos\\_analise\\ranking_canal.csv

Uso:
    python bin/medir_metricas.py --dry-run              # so lista quem vai medir
    python bin/medir_metricas.py                        # mede tudo, grava tudo
    python bin/medir_metricas.py --projeto veo          # so uma fonte
    python bin/medir_metricas.py --dias 2               # so posted nos ult. 2 dias
"""
import argparse
import csv
import json
import re
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

if sys.stdout:  # pythonw (tarefa agendada) não tem stdout

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BIN = Path(__file__).resolve().parent
sys.path.insert(0, str(BIN))
import youtube_poster as YP
import stats_views as SV

BRT = timezone(timedelta(hours=-3))
VEO_CACHE = Path(r"D:\veo\beta\logs\video_cache.json")
MATERIAIS = Path(r"D:\hipercool-materiais")
ANALISE = Path(r"D:\postador-de-videos\_analise")
VEO_BIN = Path(r"D:\veo\beta")
LOGS_DIR = Path(r"D:\postador-de-videos\logs")

# linha do driver: "[r1] historias -> [andre( fake news] TITULO OK https://youtu.be/VIDEOID"
_LOG_OK_RE = re.compile(r"\]\s*(\w+)\s*->\s*\[([^\]]+)\].*?OK\s+(https?://\S+)")

_VID_RE = re.compile(r"(?:v=|youtu\.be/|shorts/)([\w-]{6,})")


def extrair_video_id(url):
    if not url:
        return None
    m = _VID_RE.search(url)
    return m.group(1) if m else None


def _um_token():
    """Retorna 1 access_token de qualquer canal que renove. Serve pra ler stats
    publicos de QUALQUER video por id."""
    for c in YP._load_canais():
        try:
            return YP.refresh_access_token(c), c["nome"]
        except Exception:
            continue
    return None, None


def _dentro_periodo(iso_ts, dias):
    if not dias or not iso_ts:
        return True
    try:
        dt = datetime.fromisoformat(str(iso_ts).replace("Z", "+00:00"))
        return dt >= datetime.now(timezone.utc) - timedelta(days=dias)
    except Exception:
        return True


# ─── Fonte 1: veo ────────────────────────────────────────────────────────────
def coletar_veo(dias=None):
    """Retorna [{'fonte':'veo','id':cache_id,'canal':persona,'video_id':vid,'url':url}]."""
    itens = []
    if not VEO_CACHE.is_file():
        return itens
    cache = json.loads(VEO_CACHE.read_text(encoding="utf-8"))
    for x in cache:
        url = (x.get("metrics") or {}).get("posted_url")
        vid = extrair_video_id(url)
        if not vid:
            continue
        if not _dentro_periodo((x.get("metrics") or {}).get("posted_at") or x.get("ts"), dias):
            continue
        itens.append({"fonte": "veo", "id": x["id"], "canal": x.get("canal", "?"),
                      "video_id": vid, "url": url})
    return itens


def gravar_veo(medidos):
    """medidos: {cache_id: {views,likes,comments}}. Reusa metrics_client."""
    if not medidos:
        return 0
    sys.path.insert(0, str(VEO_BIN))
    import metrics_client as MC
    n = 0
    for cid, m in medidos.items():
        MC.update_cache_metrics(cid, m)
        n += 1
    return n


# ─── Fonte 2: materiais (recap/animes/historias postados pelo driver) ─────────
def coletar_materiais(dias=None):
    itens = []
    if not MATERIAIS.is_dir():
        return itens
    vistos_pj = set()
    for pj in list(MATERIAIS.rglob("postar.json")) + list(MATERIAIS.rglob("*.postar.json")):
        if str(pj) in vistos_pj:
            continue
        vistos_pj.add(str(pj))
        try:
            doc = json.loads(pj.read_text(encoding="utf-8"))
        except Exception:
            continue
        url = doc.get("posted_url")
        vid = extrair_video_id(url)
        if not vid:
            continue
        if not _dentro_periodo(doc.get("posted_at"), dias):
            continue
        canal = doc.get("canal") or (doc.get("canais") or ["?"])[0] or "?"
        itens.append({"fonte": doc.get("categoria", "materiais"), "id": str(pj),
                      "canal": canal, "video_id": vid, "url": url, "_path": pj})
    return itens


def gravar_materiais(itens, stats_por_vid):
    n = 0
    for it in itens:
        st = stats_por_vid.get(it["video_id"])
        if not st or "_path" not in it:
            continue  # fonte 'logs' nao tem postar.json — so entra no ranking
        pj = it["_path"]
        try:
            doc = json.loads(pj.read_text(encoding="utf-8"))
            doc["views"] = st["views"]
            doc["likes"] = st["likes"]
            doc["comments"] = st["coments"]
            doc["metrics_measured_at"] = datetime.now(BRT).isoformat(timespec="seconds")
            pj.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
            n += 1
        except Exception as e:
            print(f"  ! falha gravando {pj.name}: {str(e)[:60]}")
    return n


# ─── Busca de stats em lote (dedup por video_id) ─────────────────────────────
def buscar_stats(video_ids, token, max_chamadas=None):
    """Retorna {video_id: {views,likes,coments,titulo,publicado}}. 1 chamada/50 ids."""
    ids = list(dict.fromkeys(video_ids))  # dedup preservando ordem
    out = {}
    lotes = [ids[i:i + 50] for i in range(0, len(ids), 50)]
    if max_chamadas:
        lotes = lotes[:max_chamadas]
    for lote in lotes:
        try:
            for s in SV.stats_videos(token, lote):
                out[s["id"]] = s
        except Exception as e:
            print(f"  ! erro buscando lote: {str(e)[:80]}")
        time.sleep(0.1)
    return out


def escrever_ranking(itens, stats_por_vid):
    """Agrega por canal e escreve ranking_canal.csv ordenado por views_mediana."""
    por_canal = defaultdict(list)
    for it in itens:
        st = stats_por_vid.get(it["video_id"])
        if st:
            por_canal[(it["fonte"], it["canal"])].append(st)
    linhas = []
    for (fonte, canal), sts in por_canal.items():
        views = sorted(s["views"] for s in sts)
        n = len(views)
        med = views[n // 2] if n else 0
        linhas.append({
            "canal": canal, "fonte": fonte, "postados": n,
            "views_total": sum(views), "views_max": max(views) if views else 0,
            "views_mediana": med, "likes_total": sum(s["likes"] for s in sts),
        })
    linhas.sort(key=lambda r: -r["views_mediana"])
    ANALISE.mkdir(parents=True, exist_ok=True)
    saida = ANALISE / "ranking_canal.csv"
    with saida.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["canal", "fonte", "postados", "views_total",
                                          "views_max", "views_mediana", "likes_total"])
        w.writeheader()
        w.writerows(linhas)
    return saida, linhas


# ─── Fonte 3: logs do driver (backfill — postagens sem posted_url gravado) ────
def coletar_logs(dias=None):
    """Parseia os logs postar_tudo_*.log pra pegar canal+URL das postagens OK.
    Backfill: mede postagens antigas que rodaram antes do posted_url ser gravado."""
    itens = []
    if not LOGS_DIR.is_dir():
        return itens
    vistos = set()
    for log in sorted(LOGS_DIR.glob("postar_tudo_*.log")):
        for linha in log.read_text(encoding="utf-8", errors="replace").splitlines():
            m = _LOG_OK_RE.search(linha)
            if not m:
                continue
            cat, canal, url = m.group(1), m.group(2).strip(), m.group(3)
            vid = extrair_video_id(url)
            if not vid or vid in vistos:
                continue
            vistos.add(vid)
            itens.append({"fonte": cat, "id": f"log:{vid}", "canal": canal,
                          "video_id": vid, "url": url})
    return itens


def main():
    ap = argparse.ArgumentParser(description="Coletor central de views dos postados")
    ap.add_argument("--projeto", choices=["veo", "materiais", "logs", "todos"], default="todos")
    ap.add_argument("--dias", type=int, default=None, help="so posted nos ult. N dias")
    ap.add_argument("--max-chamadas", type=int, default=None, help="limite de chamadas API")
    ap.add_argument("--dry-run", action="store_true", help="so lista, nao busca nem grava")
    args = ap.parse_args()

    fontes = ["veo", "materiais", "logs"] if args.projeto == "todos" else [args.projeto]
    itens = []
    if "veo" in fontes:
        itens += coletar_veo(args.dias)
    if "materiais" in fontes:
        itens += coletar_materiais(args.dias)
    # logs: backfill. Dedup — nao repete video_id ja coberto por veo/materiais
    # (essas fontes tem writeback estruturado; log so serve pro ranking).
    if "logs" in fontes:
        ja = {it["video_id"] for it in itens}
        itens += [x for x in coletar_logs(args.dias) if x["video_id"] not in ja]

    print(f"\n{'='*68}")
    print(f"COLETOR DE METRICAS — {len(itens)} videos com posted_url")
    print(f"{'='*68}")
    por_fonte = defaultdict(int)
    for it in itens:
        por_fonte[it["fonte"]] += 1
    for f, n in sorted(por_fonte.items()):
        print(f"  {f:12} {n:4} videos")

    if args.dry_run:
        print("\n>>> DRY-RUN. Amostra:")
        for it in itens[:10]:
            print(f"  [{it['fonte']:9}] {it['video_id']:12} <- {it['canal'][:30]}")
        print(f"\n(total {len(itens)}) Rode sem --dry-run pra medir.")
        return

    if not itens:
        print("\n(nada pra medir)")
        return

    token, via = _um_token()
    if not token:
        print("\n! nenhum token OAuth renovou — impossivel medir")
        return
    print(f"\ntoken via: {via}")

    stats = buscar_stats([it["video_id"] for it in itens], token, args.max_chamadas)
    print(f"medidos: {len(stats)}/{len(itens)} videos")

    # writeback veo
    if "veo" in fontes:
        medidos_veo = {}
        for it in itens:
            if it["fonte"] == "veo" and it["video_id"] in stats:
                s = stats[it["video_id"]]
                v = max(s["views"], 1)
                medidos_veo[it["id"]] = {
                    "views": s["views"], "likes": s["likes"], "comments": s["coments"],
                    "engagement_rate": round((s["likes"] + 3 * s["coments"]) / v, 4),
                }
        n = gravar_veo(medidos_veo)
        print(f"  veo: {n} entradas atualizadas no video_cache.json")

    # writeback materiais
    if "materiais" in fontes:
        mats = [it for it in itens if it["fonte"] not in ("veo",)]
        n = gravar_materiais(mats, stats)
        print(f"  materiais: {n} postar.json atualizados")

    saida, linhas = escrever_ranking(itens, stats)
    print(f"\nranking: {saida}")
    print(f"\n{'TOP CANAIS (por views mediana)':<40}")
    print(f"  {'canal':<32} {'post':>4} {'med':>5} {'max':>6} {'total':>7}")
    for r in linhas[:15]:
        print(f"  {r['canal'][:32]:<32} {r['postados']:>4} {r['views_mediana']:>5} "
              f"{r['views_max']:>6} {r['views_total']:>7}")


if __name__ == "__main__":
    main()
