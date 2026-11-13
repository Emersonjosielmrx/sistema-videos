"""videos_canais.py — TODOS os vídeos de cada canal do YouTube, de qualquer origem (dona 30/10: "o telão só mostra vídeo
com menos de 1.200 e 3 com mais; nos canais tem vídeo com 1,5 mil, 13 mil... não estamos contabilizando direito").

O painel/telão liam só o ledger do postador (uploads_ledger.jsonl): vídeo postado pela rede manhwa-react, à mão ou antes
de 04/10 não existia pra eles (30/10: 2.297 vídeos nos canais, 481 no ledger; 91 com 1.000+ views e o telão via no
máximo 12). Aqui: lista de uploads de cada canal (rede_canais.json "yt_id") pela API pública do YouTube, views/likes/
comentários ao vivo. Cache em estado\\videos_canais.json (1 h); ~100 unidades de cota por coleta.

    from videos_canais import videos    # lista [{id, canal, titulo, views, likes, comentarios, pub(iso), ...}]
    python videos_canais.py             # coleta agora e mostra os mais vistos
"""
import json
import sys
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

BASE = Path(__file__).resolve().parent
CACHE = BASE / "estado" / "videos_canais.json"
HIST = BASE / "estado" / "canais_views_hist.jsonl"  # 01/11: 1 linha por canal por coleta (painel :8790)
REDE = Path(r"D:\postador-de-videos\config\rede_canais.json")
CANAIS = Path(r"D:\postador-de-videos\config\canais.json")
MAX_POR_CANAL = 1000  # 31/10: 300 cortava inovare_french (382 vídeos) e inovare_ind (311)
VALIDADE_S = 3600
_TRAVA = threading.Lock()


def _tokens():
    """Access tokens de qualquer canal que leia a API (a leitura é pública: serve o token de qualquer conta)."""
    sys.path.insert(0, r"D:\postador-de-videos\bin")
    import politica
    for c in politica.carregar_creds():
        if not (c.get("clientId") and c.get("clientSecret") and c.get("refresh_token")):
            continue
        dados = urlencode({"client_id": c["clientId"], "client_secret": c["clientSecret"],
                           "refresh_token": c["refresh_token"], "grant_type": "refresh_token"}).encode()
        try:
            with urllib.request.urlopen(urllib.request.Request("https://oauth2.googleapis.com/token", data=dados),
                                        timeout=15) as r:
                yield json.loads(r.read())["access_token"]
        except (urllib.error.URLError, OSError, ValueError, KeyError):
            continue


class _API:
    def __init__(self):
        self.gen = _tokens()
        self.tok = next(self.gen, None)

    def get(self, caminho, **q):
        url = "https://www.googleapis.com/youtube/v3/" + caminho + "?" + urlencode(q)
        while self.tok:
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers={"Authorization": "Bearer " + self.tok}),
                                            timeout=30) as r:
                    return json.loads(r.read())
            except urllib.error.HTTPError as e:
                if e.code not in (401, 403):
                    raise
                self.tok = next(self.gen, None)  # conta suspensa/sem cota: próxima
        raise RuntimeError("nenhuma conta conseguiu ler a API do YouTube")


def _canais():
    """[{yt_id, nome, slug}] de rede_canais.json + config\\canais.json do postador (o rede não tem os "Noturno",
    Dorama, InovareManhwaVerse...). Suspensos ficam de fora."""
    import re
    vistos, out = set(), []
    try:
        for c in json.loads(REDE.read_text(encoding="utf-8")).get("canais", []):
            if c.get("yt_id") and c.get("status") != "suspenso" and c["yt_id"] not in vistos:
                vistos.add(c["yt_id"])
                out.append({"yt_id": c["yt_id"], "nome": c.get("nome"), "slug": c.get("slug")})
    except (OSError, ValueError):
        pass
    try:
        cad = json.loads(CANAIS.read_text(encoding="utf-8")).get("canais") or {}
    except (OSError, ValueError):
        cad = {}
    for slug, x in cad.items():
        if not isinstance(x, dict) or x.get("status") == "suspenso":
            continue
        cid = next((v for v in x.values() if isinstance(v, str) and re.fullmatch(r"UC[\w-]{22}", v)), None)
        if cid and cid not in vistos:
            vistos.add(cid)
            out.append({"yt_id": cid, "nome": x.get("nome") or slug, "slug": slug})
    return out


def coletar():
    api = _API()
    out, erros = [], []
    for c in _canais():
        cid = c["yt_id"]
        try:
            ids, page = [], None
            while len(ids) < MAX_POR_CANAL:
                q = {"part": "contentDetails", "maxResults": 50, "playlistId": "UU" + cid[2:]}
                if page:
                    q["pageToken"] = page
                d = api.get("playlistItems", **q)
                ids += [i["contentDetails"]["videoId"] for i in d.get("items", [])]
                page = d.get("nextPageToken")
                if not page:
                    break
            for i in range(0, len(ids), 50):
                for v in api.get("videos", part="snippet,statistics,status", id=",".join(ids[i:i + 50])).get("items", []):
                    st, sn = v.get("statistics") or {}, v.get("snippet") or {}
                    if (v.get("status") or {}).get("privacyStatus") not in ("public", "unlisted"):
                        continue
                    out.append({"id": v["id"], "canal": c.get("nome") or sn.get("channelTitle"),
                                "slug": c.get("slug"), "titulo": sn.get("title") or "", "pub": sn.get("publishedAt"),
                                "views": int(st.get("viewCount", 0)), "likes": int(st["likeCount"]) if "likeCount" in st else None,
                                "comentarios": int(st["commentCount"]) if "commentCount" in st else None})
        except Exception as e:  # noqa: BLE001 — um canal ruim não derruba os outros
            erros.append(f"{c.get('nome')}: {type(e).__name__}: {str(e)[:80]}")
    # 01/11 (dona: "pegar os dados gerais de cada canal do Studio e ver se bate com o adicionado individual"): total do
    # canal (channels.statistics) x soma dos vídeos lidos — 1 unidade de cota por 50 canais
    conferencia, hist = {}, []
    try:
        canais = _canais()
        for i in range(0, len(canais), 50):
            lote = canais[i:i + 50]
            for it in api.get("channels", part="statistics", id=",".join(c["yt_id"] for c in lote)).get("items", []):
                s = it.get("statistics") or {}
                nome = next((c.get("nome") for c in lote if c["yt_id"] == it["id"]), it["id"])
                vs = [v for v in out if v["canal"] == nome]
                total, soma = int(s.get("viewCount", 0)), sum(v["views"] for v in vs)
                slug = next((c.get("slug") for c in lote if c["yt_id"] == it["id"]), None) or nome
                hist.append({"ts": datetime.now().isoformat(timespec="minutes"),
                             "slug": "".join(ch for ch in str(slug).lower() if ch.isalnum()),
                             "nome": nome, "inscritos": int(s.get("subscriberCount", 0)),
                             "views": int(s.get("viewCount", 0)), "videos": int(s.get("videoCount", 0))})
                conferencia[nome] = {"videos_canal": int(s.get("videoCount", 0)), "videos_lidos": len(vs),
                                     "views_canal": total, "views_soma": soma,
                                     # 01/11 medido: a soma fica 0–15% ACIMA do total em todos (o total do canal
                                     # atualiza com atraso). Vídeo faltando = soma ABAIXO do total.
                                     "bate": soma >= total - max(50, total * 0.05)}
    except Exception as e:  # noqa: BLE001
        erros.append(f"conferência: {type(e).__name__}: {str(e)[:80]}")
    if hist:  # 01/11: histórico dos 30 canais (o painel_canais só grava 12; os Noturnos sumiam da tabela do :8790)
        with open(HIST, "a", encoding="utf-8") as f:
            f.writelines(json.dumps(h, ensure_ascii=False) + "\n" for h in hist)
    dados = {"t": time.time(), "lido": datetime.now().isoformat(timespec="minutes"), "videos": out, "erros": erros,
             "conferencia": conferencia}
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    tmp = CACHE.with_suffix(".tmp")
    tmp.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    tmp.replace(CACHE)
    return dados


def dados(max_idade_s=VALIDADE_S):
    """Cache se novo; senão coleta (1 por vez). Coleta falhou = devolve o cache velho (ou vazio)."""
    with _TRAVA:
        try:
            d = json.loads(CACHE.read_text(encoding="utf-8"))
            if time.time() - d.get("t", 0) < max_idade_s:
                return d
        except (OSError, ValueError):
            d = {"videos": []}
        try:
            return coletar()
        except Exception:  # noqa: BLE001
            return d


def videos(max_idade_s=VALIDADE_S):
    return dados(max_idade_s).get("videos", [])


def pub_local(v):
    try:
        return datetime.fromisoformat(v["pub"].replace("Z", "+00:00")).astimezone()
    except (KeyError, ValueError, AttributeError):
        return None


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure") and sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    d = coletar()
    vs = sorted(d["videos"], key=lambda v: -v["views"])
    agora = datetime.now(timezone.utc).astimezone()
    print(f"{len(vs)} vídeos, {len({v['canal'] for v in vs})} canais, erros: {d['erros'] or 'nenhum'}")
    print("1.000+ views:", sum(v["views"] >= 1000 for v in vs),
          "| nos últimos 30 dias:", sum(v["views"] >= 1000 and (agora - pub_local(v)).days <= 30 for v in vs if pub_local(v)))
    for v in vs[:15]:
        print(f"{v['views']:>9}  {v['canal'][:22]:22} {v['id']}  {v['titulo'][:60]}")
