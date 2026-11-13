import subprocess
import json

print("Testando busca real de shorts...")
# Vamos forçar a usar a URL interna do YT Shorts
cmd = [
    "yt-dlp", f"ytsearch10:curiosidades anime #shorts",
    "--flat-playlist", "--no-warnings",
    "--print", "%(id)s\x1f%(duration)s\x1f%(title)s"
]
out = subprocess.run(cmd, capture_output=True, text=True)

for line in out.stdout.strip().splitlines():
    vid, dur, title = line.split('\x1f')
    # Faz probe da dimensao
    pcmd = ["yt-dlp", vid, "--skip-download", "--no-warnings", "--print", "%(width)sx%(height)s"]
    res = subprocess.run(pcmd, capture_output=True, text=True).stdout.strip()
    print(f"Vídeo {vid} | {dur}s | {res} | {title}")
