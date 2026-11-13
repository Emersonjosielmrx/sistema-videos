#!/usr/bin/env python3
"""stats_views.py — Estatisticas de VIEWS dos videos postados por canal.

Pra cada canal com token valido, consulta a API do YouTube:
  1. pega o playlist de uploads do canal (channels.list -> uploads)
  2. lista os videos recentes (playlistItems.list)
  3. pega viewCount de cada um (videos.list statistics)
  4. filtra por data de publicacao (default: ontem e anteontem) e ordena por views

Uso:
    python bin/stats_views.py                 # ontem + anteontem, todos os canais
    python bin/stats_views.py --dias 3         # ultimos 3 dias
    python bin/stats_views.py --canal "inovare recap manga"
    python bin/stats_views.py --todos-periodos # ignora filtro de data (todos os recentes)
"""
import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

if sys.stdout:  # pythonw (tarefa agendada) não tem stdout

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BIN = Path(__file__).resolve().parent
sys.path.insert(0, str(BIN))
import youtube_poster as YP  # reusa refresh_access_token / _load_canais

BRT = timezone(timedelta(hours=-3))
API = "https://www.googleapis.com/youtube/v3"


def _get(url, token):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def uploads_playlist(token):
    d = _get(f"{API}/channels?part=contentDetails&mine=true", token)
    items = d.get("items", [])
    if not items:
        return None, None
    ch = items[0]
    pl = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    return pl, ch["id"]


def listar_videos(token, playlist, max_itens=50):
    ids, page = [], None
    while len(ids) < max_itens:
        url = f"{API}/playlistItems?part=contentDetails&maxResults=50&playlistId={playlist}"
        if page:
            url += f"&pageToken={page}"
        d = _get(url, token)
        for it in d.get("items", []):
            ids.append(it["contentDetails"]["videoId"])
        page = d.get("nextPageToken")
        if not page:
            break
    return ids[:max_itens]


def stats_videos(token, video_ids):
    out = []
    for i in range(0, len(video_ids), 50):
        chunk = video_ids[i:i + 50]
        url = f"{API}/videos?part=snippet,statistics&id={','.join(chunk)}"
        d = _get(url, token)
        for it in d.get("items", []):
            sn, st = it["snippet"], it.get("statistics", {})
            out.append({
                "id": it["id"],
                "titulo": sn["title"],
                "publicado": sn["publishedAt"],
                "views": int(st.get("viewCount", 0)),
                "likes": int(st.get("likeCount", 0)),
                "coments": int(st.get("commentCount", 0)),
            })
    return out


def main():
    ap = argparse.ArgumentParser(description="Views por canal dos videos postados")
    ap.add_argument("--dias", type=int, default=2, help="quantos dias atras (default 2 = ontem+anteontem)")
    ap.add_argument("--canal", help="so um canal (nome ou id)")
    ap.add_argument("--todos-periodos", action="store_true", help="ignora filtro de data")
    args = ap.parse_args()

    canais = YP._load_canais()
    if args.canal:
        c = YP._find_canal(canais, args.canal)
        canais = [c] if c else []

    hoje = datetime.now(BRT).date()
    corte = hoje - timedelta(days=args.dias)

    resumo_global = []
    print(f"\n{'='*72}")
    print(f"ESTATISTICAS DE VIEWS — periodo: {corte} ate {hoje} (BRT)")
    print(f"{'='*72}")

    for c in canais:
        nome = c["nome"]
        try:
            token = YP.refresh_access_token(c)
        except Exception as e:  # noqa
            print(f"\n[{nome}] TOKEN FALHOU: {str(e)[:80]}")
            continue
        try:
            pl, _ = uploads_playlist(token)
            if not pl:
                print(f"\n[{nome}] sem playlist de uploads (canal vazio?)")
                continue
            vids = listar_videos(token, pl, max_itens=50)
            sts = stats_videos(token, vids)
        except Exception as e:  # noqa
            print(f"\n[{nome}] ERRO API: {str(e)[:80]}")
            continue

        # filtra por data
        if not args.todos_periodos:
            filt = []
            for s in sts:
                dt = datetime.fromisoformat(s["publicado"].replace("Z", "+00:00")).astimezone(BRT).date()
                if dt >= corte:
                    s["_data"] = str(dt)
                    filt.append(s)
            sts = filt
        else:
            for s in sts:
                s["_data"] = datetime.fromisoformat(s["publicado"].replace("Z","+00:00")).astimezone(BRT).date().isoformat()

        if not sts:
            continue
        sts.sort(key=lambda s: s["views"], reverse=True)
        total = sum(s["views"] for s in sts)
        print(f"\n── {nome} — {len(sts)} video(s), {total} views totais ──")
        for s in sts:
            print(f"   {s['views']:>6} views | {s['likes']:>4}👍 | {s['_data']} | {s['titulo'][:46]}")
            resumo_global.append((s["views"], nome, s["titulo"], s["id"], s["_data"]))

    # ranking global
    if resumo_global:
        resumo_global.sort(reverse=True)
        print(f"\n{'='*72}")
        print(f"TOP 10 VIDEOS (todos os canais) no periodo:")
        print(f"{'='*72}")
        for views, nome, tit, vid, data in resumo_global[:10]:
            print(f"   {views:>6} views | {nome[:24]:<25} | {data} | {tit[:36]}")
        print(f"\nTotal geral: {sum(r[0] for r in resumo_global)} views em {len(resumo_global)} videos")
    else:
        print("\n(nenhum video no periodo — ou nenhum canal com upload recente)")


if __name__ == "__main__":
    main()
