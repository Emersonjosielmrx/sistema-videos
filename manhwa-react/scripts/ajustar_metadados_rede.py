"""Reescreve titulo/descricao/tags (agente do canal) dos videos PUBLICOS desde 01/10 nos canais ativos da rede.
Idempotente (logs/metadados_ajustados.json). Uso: python scripts/ajustar_metadados_rede.py [--executar]"""
import sys
import urllib.error
from pathlib import Path

sys.path.insert(0, r"D:\manhwa-react")
from mr.common import load_config, load_json, save_json  # noqa: E402
from mr import publish as PB, rede as RD  # noqa: E402

EXEC = "--executar" in sys.argv
LOG = Path(r"D:\manhwa-react\logs\metadados_ajustados.json")
cfg = load_config()
politica, yp = PB._postador(cfg)
feito = load_json(LOG) if LOG.exists() else {}
DUPLICADOS = {"IbYPz9gxMLA", "ScChA9RtYrs", "g6gYsCp0VK4", "tjib-lV_tKY"}  # copias do ManhwaReact no inovaremanhwabr (privados)
for canal in RD.canais(cfg, politica):
    cred = canal["cred"]
    ch = RD._req(yp, cred, "https://www.googleapis.com/youtube/v3/channels?part=contentDetails&mine=true")["items"][0]
    pl = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    itens = RD._req(yp, cred, f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet,status&maxResults=30&playlistId={pl}")["items"]
    for it in itens:
        sn = it["snippet"]
        vid = sn["resourceId"]["videoId"]
        if vid in feito or it["status"]["privacyStatus"] != "public" or sn["publishedAt"] < "2026-10-01":
            continue
        # canais de produto (AssistIA/Dicas): os videos proprios do dono NAO sao reescritos; so o react que caiu la
        if canal["slug"] in ("assistiainvestimentos", "dicasfinanceirasdaia") and vid not in {"Lk5EbXnFKI4"}:
            continue
        if vid in DUPLICADOS:
            continue
        v = RD.video_info(yp, cred, vid)
        item = {"id": f"pub_{vid}", "fonte": "publicado", "sintetico": False, "slug_origem": canal["slug"],
                "dados": {"titulo": v["snippet"]["title"], "descricao": v["snippet"].get("description", ""),
                          "tags": v["snippet"].get("tags", [])},
                "resumo": {"titulo": v["snippet"]["title"], "descricao": v["snippet"].get("description", "")[:300]}}
        meta = RD.adaptar(cfg, item, canal)
        print(f"{canal['nome']:24} {vid}: {v['snippet']['title'][:45]}  ->  {meta['titulo'][:55]}")
        if not EXEC:
            continue
        try:
            RD.editar_meta(yp, cred, vid, meta, categoria=canal.get("categoria"), idioma=canal.get("idioma", "pt-BR"))
            feito[vid] = {"canal": canal["nome"], "antes": v["snippet"]["title"], "depois": meta["titulo"]}
            save_json(feito, LOG)
        except urllib.error.HTTPError as e:
            print(f"   ERRO {e.code} {e.read()[:150]!r}")
            if e.code == 403:
                break
