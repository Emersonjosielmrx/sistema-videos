# Testa se o ffmpeg do Very Good FFmpeg lê SVG (librsvg): sobe um card SVG bonito no tmp-file e pede PNG.
import json, time, urllib.request, urllib.error
from pathlib import Path

K = open(r"D:\hipercool-materiais\fluxo-anuncio-api\vgf_chave.txt").read().split()[0]
AQUI = Path(__file__).parent
SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="900" height="300" viewBox="0 0 900 300">
<defs>
 <linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#8B5CF6"/><stop offset="1" stop-color="#5B21B6"/></linearGradient>
 <linearGradient id="brilho" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".35"/><stop offset=".5" stop-color="#fff" stop-opacity="0"/></linearGradient>
 <filter id="sombra" x="-20%" y="-20%" width="140%" height="160%"><feDropShadow dx="0" dy="14" stdDeviation="16" flood-color="#000" flood-opacity=".45"/></filter>
</defs>
<rect x="40" y="30" width="820" height="200" rx="46" fill="url(#g)" filter="url(#sombra)"/>
<rect x="40" y="30" width="820" height="200" rx="46" fill="url(#brilho)"/>
<rect x="42" y="32" width="816" height="196" rx="44" fill="none" stroke="#fff" stroke-opacity=".35" stroke-width="3"/>
<circle cx="140" cy="130" r="54" fill="#fff" fill-opacity=".18"/>
<text x="140" y="150" font-size="60" text-anchor="middle" fill="#fff" font-family="sans-serif" font-weight="700">1</text>
<text x="230" y="150" font-size="56" fill="#fff" font-family="sans-serif" font-weight="800">Residencial Barãoville</text>
</svg>"""


def chama(m, u, c=None):
    r = urllib.request.Request(u, method=m, data=json.dumps(c).encode() if c is not None else None,
                               headers={"Authorization": "Bearer " + K, "Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=60) as x:
        return json.loads(x.read())


lugar = chama("POST", "https://verygoodffmpeg.com/api/tmp-file", {})["data"]
urllib.request.urlopen(urllib.request.Request(lugar["upload_url"], method="PUT", data=SVG.encode(), headers={"Content-Type": "image/svg+xml"}), timeout=60)
d = chama("POST", "https://verygoodffmpeg.com/api/ffmpeg", {"input_files": {"c.svg": lugar["download_url"]}, "output_files": ["c.png"],
          "machine": "cpu", "timeout_seconds": 60, "ffmpeg_commands": ["-i inputs/c.svg -frames:v 1 outputs/c.png"]})["data"]
for _ in range(40):
    time.sleep(4)
    d = chama("GET", f"https://verygoodffmpeg.com/api/jobs/{d['id']}")["data"]
    if d.get("status") in ("succeeded", "failed", "error", "timed_out"):
        break
print(d.get("status"), (d.get("error_message") or "")[:600])
for nome, url in (d.get("output_files") or {}).items():
    (AQUI / ("vgf_" + nome)).write_bytes(urllib.request.urlopen(url, timeout=60).read())
    print("baixou", nome)
