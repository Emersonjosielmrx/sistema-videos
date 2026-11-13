import json, shutil, subprocess, time
from datetime import datetime
from pathlib import Path
f = Path(r"D:\recapd-ambientes\producao\config\parceiro.json")
j = json.loads(f.read_text(encoding="utf-8"))
novos = [x for x in j["fontes"] if "09/11" in x.get("_obs", "")]
sem = []
for x in novos:
    r = subprocess.run(["yt-dlp", "--flat-playlist", "--playlist-end", "1", "--print", "%(id)s", x["url"]],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    if "does not have a shorts tab" in r.stderr:
        sem.append(x["nome"])
        print("SEM SHORTS:", x["nome"], flush=True)
    time.sleep(6)  # sem rajada no IP de casa
shutil.copy2(f, f.with_name(f"parceiro.json.bkp_{datetime.now():%Y%m%d_%H%M}_semshorts"))
for x in j["fontes"]:
    if x["nome"] in sem:
        x["peso"] = 0
        x["_peso_obs"] = ("09/11: canal sem aba de Shorts (só vídeo longo) — fora do rodízio de Shorts; serve pros "
                          "cortes de longos. Desfazer: apagar peso")
f.write_text(json.dumps(j, ensure_ascii=False, indent=1), encoding="utf-8")
print("total sem shorts:", len(sem), sem)
