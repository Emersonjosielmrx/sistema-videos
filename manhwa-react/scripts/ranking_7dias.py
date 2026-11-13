#!/usr/bin/env python3
"""ranking_7dias.py - SOMENTE LEITURA. Coleta os ultimos uploads de cada canal da rede (mesma coleta do painel_canais.py,
sem gravar painel/historico/aprendizado), confere os agendados dos logs da rede e imprime o ranking dos ultimos 7 dias.
Grava so work/ranking_7dias.json."""
import json
import re
import sys
import urllib.error
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"D:\postador-de-videos\bin")
import politica  # noqa: E402
import painel_canais as pc  # noqa: E402

LOGS = Path(r"D:\manhwa-react\logs")
agora = datetime.now(timezone.utc)
corte = agora - timedelta(days=7)


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None


creds = {c["id"]: c for c in politica.carregar_creds()}
todos, erros = [], {}
for canal in politica.rede().get("canais", []):
    if canal.get("status") != "ativo":
        continue
    cred = next((creds[i] for i in canal.get("creds", []) if i in creds), None)
    try:
        d = pc.coletar(canal, cred)
    except urllib.error.HTTPError as ex:
        erros[canal["nome"]] = f"{ex.code} {ex.read()[:120]!r}"
        continue
    except Exception as ex:  # noqa: BLE001
        erros[canal["nome"]] = str(ex)[:150]
        continue
    for v in d["uploads"]:
        v["canal"] = d["nome"]
        v["inscritos"] = d["inscritos"]
        todos.append(v)

por_id = {v["id"]: v for v in todos}

# agendados registrados nos logs da rede
agendados = []
for lg in sorted(LOGS.glob("rede_2026*.log")):
    for ln in lg.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.search(r"rede: (.+?): AGENDADO https://youtu\.be/(\S+) -> (\S+) \((\d\d:\d\d)\) \| (.*)", ln)
        if m:
            agendados.append({"canal": m[1], "id": m[2], "publishAt": m[3], "hora": m[4], "titulo": m[5], "log": lg.name})

print(f"== AGENDADOS PELA REDE (logs) : {len(agendados)} ==")
res = {"postado": 0, "ainda_agendado": 0, "privado_ou_removido": 0}
for a in agendados:
    v = por_id.get(a["id"])
    if not v:
        est = "NAO ACHEI na lista dos ultimos 30 uploads do canal (removido/privado ou fora da janela)"
        res["privado_ou_removido"] += 1
    elif v["privacy"] == "public":
        est = f"POSTADO  views={v['views']}"
        res["postado"] += 1
    elif v["privacy"] == "private" and v["publishAt"]:
        est = f"AINDA AGENDADO para {v['publishAt']}"
        res["ainda_agendado"] += 1
    else:
        est = f"{v['privacy']} (sem agendamento)"
        res["privado_ou_removido"] += 1
    print(f"{a['publishAt'][:16]}  {a['canal'][:26]:26}  {a['id']}  {est}")
print(res)

rec = [v for v in todos if v["privacy"] == "public" and ts(v["pub"]) >= corte]
rec.sort(key=lambda v: (v["views"], v["likes"], v["coments"]), reverse=True)
print(f"\n== RANKING PUBLICOS NOS ULTIMOS 7 DIAS ({len(rec)} videos, janela desde {corte:%d/%m %H:%M} UTC) ==")
for i, v in enumerate(rec, 1):
    print(f"{i:2}. {v['views']:6} views {v['likes']:4} likes {v['coments']:3} com | {v['canal'][:24]:24} | {v['pub'][5:16]} | "
          f"https://youtu.be/{v['id']} | {v['titulo'][:70]}")
if erros:
    print("\nERROS:", json.dumps(erros, ensure_ascii=False, indent=1))
Path(r"D:\manhwa-react\work\ranking_7dias.json").write_text(
    json.dumps({"gerado": agora.isoformat(), "agendados": agendados, "ranking": rec, "erros": erros},
               ensure_ascii=False, indent=1), encoding="utf-8")
