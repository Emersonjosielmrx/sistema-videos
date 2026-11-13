"""Roda o comando que vai para a Rendi aqui no PC (baixa as entradas, troca {{in_x}} pelos arquivos locais).
Uso: python roda_local.py saida_no.json"""
import base64, json, os, re, shlex, subprocess, sys, urllib.request

r = json.load(open(sys.argv[1], encoding="utf-8"))[0]["json"]
corpo = json.loads(r["corpo"])
os.makedirs("ent", exist_ok=True)
open("ent/textos.ass", "wb").write(base64.b64decode(r["textos"]))
open("ent/textos_m.ass", "wb").write(base64.b64decode(r["textos_musica"]))
mapa = {"in_textos": "ent/textos.ass", "in_textos_m": "ent/textos_m.ass"}
for k, u in corpo["input_files"].items():
    if k in mapa:
        continue
    dest = f"ent/{k}" + (".mp3" if k.startswith("in_v") or k == "in_trilha" else ".jpg")
    if u.startswith("LOCAL:"):
        dest = u[6:]
    elif not os.path.exists(dest):
        urllib.request.urlretrieve(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}).full_url, dest) if False else \
            open(dest, "wb").write(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=120).read())
    mapa[k] = dest
for k, n in corpo["output_files"].items():
    mapa[k] = "sai_" + n
cmd = re.sub(r"\{\{(\w+)\}\}", lambda m: mapa[m.group(1)], corpo["ffmpeg_command"])
print("total:", r["total"], "| tamanho do comando:", len(corpo["ffmpeg_command"]))
p = subprocess.run(["ffmpeg", "-y", "-v", "error", *shlex.split(cmd)], capture_output=True, text=True)
print("ffmpeg:", p.returncode, p.stderr[-2500:])
