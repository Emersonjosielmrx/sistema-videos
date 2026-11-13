import subprocess
import json

print("Testando busca shorts estritos...")
cmd = [
    "yt-dlp", "https://www.youtube.com/hashtag/shorts",
    "--flat-playlist", "--no-warnings", "--playlist-items", "1-10",
    "--print", "%(id)s\x1f%(duration)s\x1f%(title)s"
]
out = subprocess.run(cmd, capture_output=True, text=True)

for line in out.stdout.strip().splitlines():
    vid, dur, title = line.split('\x1f')
    pcmd = ["yt-dlp", vid, "--skip-download", "--no-warnings", "--print", "%(width)sx%(height)s"]
    res = subprocess.run(pcmd, capture_output=True, text=True).stdout.strip()
    print(f"Vídeo {vid} | {dur}s | {res} | {title}")
