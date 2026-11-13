#!/usr/bin/env python3
"""analise_canais.py — Coleta dados de CADA canal (Data API + Analytics API) e salva
JSON bruto+derivado em _analise/<handle>.json. Base pros dossies por canal.

Coleta:
  - Data API: canal (inscritos/views/nvideos/pais/idioma) + ate 200 uploads
    (titulo/tags/data/duracao/views/likes/coments)
  - Analytics API: idade+sexo, top paises, top trafego, dispositivo, retencao media
  - Derivadas: media/mediana views, engajamento, top10/bottom10, cadencia, split short/longo

Uso:
    python bin/analise_canais.py                 # todos os canais nao-manga vivos
    python bin/analise_canais.py --canal "seebotstia (inovare com ia"
    python bin/analise_canais.py --dias 365      # janela analytics (default 365)
"""
import argparse
import json
import re
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

if sys.stdout:  # pythonw (tarefa agendada) não tem stdout

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BIN = Path(__file__).resolve().parent
sys.path.insert(0, str(BIN))
import youtube_poster as YP

BRT = timezone(timedelta(hours=-3))
DATA = "https://www.googleapis.com/youtube/v3"
YTA = "https://youtubeanalytics.googleapis.com/v2/reports"
OUT = Path(r"D:\postador-de-videos\_analise")
OUT.mkdir(parents=True, exist_ok=True)

# canais de manga/manhwa a EXCLUIR (pedido da dona)
EXCLUIR = ["manga", "manhwa"]


def _get(url, tok):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {tok}"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read().decode())


def _iso_dur_seg(iso):
    h = re.search(r"(\d+)H", iso); m = re.search(r"(\d+)M", iso); s = re.search(r"(\d+)S", iso)
    return (int(h.group(1))*3600 if h else 0)+(int(m.group(1))*60 if m else 0)+(int(s.group(1)) if s else 0)


def coletar_canal(c, dias):
    nome = c["nome"]
    tok = YP.refresh_access_token(c)
    # --- nivel canal ---
    d = _get(f"{DATA}/channels?part=snippet,statistics,contentDetails&mine=true", tok)
    it = d.get("items", [])
    if not it:
        return {"nome": nome, "erro": "sem canal"}
    ch = it[0]
    cid = ch["id"]
    sn, st = ch["snippet"], ch.get("statistics", {})
    uploads_pl = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    info = {
        "nome": nome, "channel_id": cid,
        "titulo_canal": sn.get("title"), "handle": sn.get("customUrl"),
        "descricao_canal": sn.get("description", "")[:500],
        "pais": sn.get("country"), "idioma_default": sn.get("defaultLanguage"),
        "criado_em": sn.get("publishedAt"),
        "inscritos": int(st.get("subscriberCount", 0)),
        "views_totais": int(st.get("viewCount", 0)),
        "n_videos": int(st.get("videoCount", 0)),
        "coletado_em": datetime.now(BRT).isoformat(),
    }
    # --- uploads (ate 200) ---
    ids, page = [], None
    while len(ids) < 200:
        u = f"{DATA}/playlistItems?part=contentDetails&maxResults=50&playlistId={uploads_pl}"
        if page:
            u += f"&pageToken={page}"
        pd = _get(u, tok)
        ids += [x["contentDetails"]["videoId"] for x in pd.get("items", [])]
        page = pd.get("nextPageToken")
        if not page:
            break
    videos = []
    for i in range(0, len(ids), 50):
        chunk = ids[i:i+50]
        vd = _get(f"{DATA}/videos?part=snippet,statistics,contentDetails&id={','.join(chunk)}", tok)
        for v in vd.get("items", []):
            vsn, vst = v["snippet"], v.get("statistics", {})
            dur = _iso_dur_seg(v["contentDetails"]["duration"])
            videos.append({
                "id": v["id"], "titulo": vsn["title"],
                "publicado": vsn["publishedAt"], "dur_seg": dur,
                "tags": vsn.get("tags", []),
                "views": int(vst.get("viewCount", 0)),
                "likes": int(vst.get("likeCount", 0)),
                "coments": int(vst.get("commentCount", 0)),
                "is_short": dur <= 65,
            })
    info["videos"] = videos

    # --- Analytics (publico real) ---
    fim = datetime.now(BRT).strftime("%Y-%m-%d")
    ini = (datetime.now(BRT) - timedelta(days=dias)).strftime("%Y-%m-%d")

    def anq(metrics, dims, extra=""):
        url = (f"{YTA}?ids=channel=={cid}&startDate={ini}&endDate={fim}"
               f"&metrics={metrics}&dimensions={dims}{extra}")
        try:
            return _get(url, tok).get("rows", [])
        except urllib.error.HTTPError:
            return []

    info["analytics"] = {
        "janela_dias": dias,
        "idade_sexo": anq("viewerPercentage", "ageGroup,gender"),
        "paises": anq("views", "country", "&sort=-views&maxResults=8"),
        "trafego": anq("views", "insightTrafficSourceType", "&sort=-views&maxResults=6"),
        "dispositivo": anq("views", "deviceType", "&sort=-views"),
        "retencao": anq("views,averageViewDuration,averageViewPercentage,estimatedMinutesWatched", "day", "&maxResults=1"),
    }

    info["derivadas"] = derivar(videos)
    return info


def derivar(videos):
    if not videos:
        return {"n": 0}
    vs = [v["views"] for v in videos]
    shorts = [v for v in videos if v["is_short"]]
    longos = [v for v in videos if not v["is_short"]]
    ordenados = sorted(videos, key=lambda v: v["views"], reverse=True)
    # cadencia (dias entre uploads)
    datas = sorted(datetime.fromisoformat(v["publicado"].replace("Z", "+00:00")) for v in videos)
    gaps = [(datas[i+1]-datas[i]).days for i in range(len(datas)-1)] if len(datas) > 1 else []
    def eng(v):
        return round((v["likes"]+v["coments"])/v["views"]*100, 2) if v["views"] else 0
    return {
        "n": len(videos),
        "views_media": round(statistics.mean(vs), 1),
        "views_mediana": statistics.median(vs),
        "views_max": max(vs), "views_min": min(vs),
        "n_shorts": len(shorts), "n_longos": len(longos),
        "dur_mediana_seg": statistics.median([v["dur_seg"] for v in videos]),
        "engajamento_medio_pct": round(statistics.mean([eng(v) for v in videos]), 2),
        "cadencia_dias_mediana": statistics.median(gaps) if gaps else None,
        "top10": [{"t": v["titulo"][:70], "views": v["views"], "eng%": eng(v),
                   "dur": v["dur_seg"], "id": v["id"]} for v in ordenados[:10]],
        "bottom10": [{"t": v["titulo"][:70], "views": v["views"], "id": v["id"]}
                     for v in ordenados[-10:]],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--canal", help="um canal so (nome/id)")
    ap.add_argument("--dias", type=int, default=365, help="janela analytics")
    args = ap.parse_args()

    canais = YP._load_canais()
    if args.canal:
        c = YP._find_canal(canais, args.canal)
        canais = [c] if c else []
    else:
        canais = [c for c in canais
                  if not any(x in c["nome"].lower() for x in EXCLUIR)]

    print(f"Analisando {len(canais)} canais (janela {args.dias}d)...\n")
    ok = 0
    for c in canais:
        nome = c["nome"]
        try:
            info = coletar_canal(c, args.dias)
            if info.get("erro"):
                print(f"  [SKIP] {nome}: {info['erro']}")
                continue
            handle = (info.get("handle") or info["channel_id"]).replace("@", "").replace("/", "_")
            saida = OUT / f"{handle}.json"
            saida.write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
            d = info["derivadas"]
            print(f"  [OK] {nome[:26]:<27} {info['inscritos']}insc {d['n']}vids "
                  f"media={d['views_media']}v -> {saida.name}")
            ok += 1
        except urllib.error.HTTPError as e:
            print(f"  [ERRO] {nome[:26]:<27} HTTP {e.code}")
        except Exception as e:  # noqa
            print(f"  [ERRO] {nome[:26]:<27} {type(e).__name__}: {str(e)[:50]}")
        time.sleep(1)
    print(f"\n{ok}/{len(canais)} canais coletados em {OUT}")


if __name__ == "__main__":
    main()
