"""Busca o final_anime_deitado.mp4 do PC2 e roda anime_publish.py AQUI
(pasta hipercool-materiais só existe no PC principal)."""
import sys, subprocess, base64, urllib.request, os
from pathlib import Path

HOST, PORT = "100.125.7.77", 8772
TITULO = "He Was Born With Zero Magic But Became Strongest"
SRC_URL = "https://www.youtube.com/watch?v=Jx4UTsdeam0"
# path do vídeo final no PC2 (vem do resultado do dispatch)
remote_video = sys.argv[1] if len(sys.argv) > 1 else None
if not remote_video:
    print("uso: _fetch_and_publish.py <caminho_remoto_do_mp4>"); sys.exit(1)

local = Path("workspace/anime") / "final_anime_deitado.mp4"
local.parent.mkdir(parents=True, exist_ok=True)

# baixa via endpoint /download/<base64>
enc = base64.urlsafe_b64encode(remote_video.encode()).decode()
url = f"http://{HOST}:{PORT}/download/{enc}"
print(f"[fetch] baixando {remote_video} ...")
with urllib.request.urlopen(url, timeout=600) as r, open(local, "wb") as f:
    while True:
        chunk = r.read(1024*1024)
        if not chunk: break
        f.write(chunk)
mb = local.stat().st_size/1_048_576
print(f"[fetch] baixado: {local} ({mb:.1f}MB)")

# roda o publish local
cmd = [sys.executable, "bin/anime_publish.py", "--video", str(local),
       "--anime", TITULO, "--cap", "1", "--formato", "deitado", "--source-url", SRC_URL]
print("[publish] rodando anime_publish.py ...")
r = subprocess.run(cmd, env=dict(os.environ, PYTHONUTF8="1"))
print("[publish] rc =", r.returncode)
