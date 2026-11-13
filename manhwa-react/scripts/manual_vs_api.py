#!/usr/bin/env python3
"""manual_vs_api.py - SOMENTE LEITURA. Compara views de videos postados a mao x subidos pela rede (API), por canal."""
import json
import re
import statistics as st
import sys
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"D:\postador-de-videos\bin")
import politica  # noqa: E402
import painel_canais as pc  # noqa: E402

api_ids = set()
reg = json.loads(Path(r"D:\hipercool-materiais\_postados\react\publicados.json").read_text(encoding="utf-8"))
api_ids |= {v["video_id"] for v in reg.values() if isinstance(v, dict) and v.get("video_id")}
for lg in Path(r"D:\manhwa-react\logs").glob("rede_2026*.log"):
    api_ids |= set(re.findall(r"AGENDADO https://youtu\.be/(\S+)", lg.read_text(encoding="utf-8", errors="replace")))
for f in Path(r"D:\postador-de-videos\logs").glob("*.log"):
    api_ids |= set(re.findall(r"youtu\.be/([\w-]{11})", f.read_text(encoding="utf-8", errors="replace")))

creds = {c["id"]: c for c in politica.carregar_creds()}
agora = datetime.now(timezone.utc)
linhas = []
for canal in politica.rede().get("canais", []):
    if canal.get("status") != "ativo":
        continue
    cred = next((creds[i] for i in canal.get("creds", []) if i in creds), None)
    try:
        tok = pc.yp.refresh_access_token(cred)
        ch = pc.get(tok, f"{pc.API}/channels?part=snippet,statistics,contentDetails&mine=true")["items"][0]
        up = ch["contentDetails"]["relatedPlaylists"]["uploads"]
        ids, page = [], ""
        while len(ids) < 100:
            r = pc.get(tok, f"{pc.API}/playlistItems?part=snippet&maxResults=50&playlistId={up}{page}")
            ids += [i["snippet"]["resourceId"]["videoId"] for i in r.get("items", [])]
            if not r.get("nextPageToken"):
                break
            page = "&pageToken=" + r["nextPageToken"]
        vids = []
        for k in range(0, len(ids), 50):
            vids += pc.get(tok, f"{pc.API}/videos?part=snippet,statistics,status,contentDetails&id={','.join(ids[k:k+50])}")["items"]
    except Exception as ex:  # noqa: BLE001
        print("ERRO", canal["nome"], str(ex)[:100])
        continue
    for v in vids:
        if v["status"]["privacyStatus"] != "public":
            continue
        pub = datetime.fromisoformat(v["snippet"]["publishedAt"].replace("Z", "+00:00"))
        linhas.append({"canal": canal["nome"], "insc": int(ch["statistics"].get("subscriberCount", 0)), "id": v["id"],
                       "api": v["id"] in api_ids, "views": int(v["statistics"].get("viewCount", 0)),
                       "idade_d": (agora - pub).days, "pub": v["snippet"]["publishedAt"][:10], "titulo": v["snippet"]["title"][:60],
                       "dur": v["contentDetails"]["duration"], "synth": v["status"].get("containsSyntheticMedia"),
                       "kids": v["status"].get("madeForKids")})

def resumo(rows):
    if not rows:
        return "-"
    vs = [r["views"] for r in rows]
    return f"n={len(rows)} mediana={st.median(vs)} media={st.mean(vs):.0f} max={max(vs)}"

print("GERAL  manual:", resumo([r for r in linhas if not r["api"]]))
print("GERAL  API   :", resumo([r for r in linhas if r["api"]]))
for nome in sorted({r["canal"] for r in linhas}):
    cs = [r for r in linhas if r["canal"] == nome]
    print(f"\n{nome} (insc={cs[0]['insc']})\n   manual: {resumo([r for r in cs if not r['api']])}\n   API   : {resumo([r for r in cs if r['api']])}")
print("\nTop 15 MANUAIS:")
for r in sorted([r for r in linhas if not r["api"]], key=lambda r: -r["views"])[:15]:
    print(f"{r['views']:7} {r['pub']} {r['canal'][:22]:22} {r['dur']:9} synth={r['synth']} {r['titulo']}")
print("\nFlags API: synth", {r['synth'] for r in linhas if r['api']}, "| manual synth", {r['synth'] for r in linhas if not r['api']})
Path(r"D:\manhwa-react\work\manual_vs_api.json").write_text(json.dumps(linhas, ensure_ascii=False, indent=1), encoding="utf-8")
