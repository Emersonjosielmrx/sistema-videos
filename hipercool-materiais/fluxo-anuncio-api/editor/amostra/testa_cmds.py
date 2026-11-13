"""Testa comandos ffmpeg no Very Good FFmpeg, um trabalho por comando: python testa_cmds.py"""
import json, sys, time, urllib.request, urllib.error

K = open(r"D:\hipercool-materiais\fluxo-anuncio-api\vgf_chave.txt").read().split()[0]
DN = open(r"D:\hipercool-materiais\fluxo-anuncio-api\editor\amostra\dn.txt").read().strip()
CMDS = [
    ("a.mp3", "-i inputs/in_video.mp4 -vn -ac 1 -ar 16000 -b:a 48k outputs/a.mp3"),
    ("q.jpg", "-ss 1 -i inputs/in_video.mp4 -frames:v 1 -vf scale=720:-2 -q:v 3 outputs/q.jpg"),
    ("m.json", "ffprobe -v error -print_format json -show_streams -show_format inputs/in_video.mp4 -o outputs/m.json"),
]


def chama(m, u, c=None):
    r = urllib.request.Request(u, method=m, data=json.dumps(c).encode() if c else None,
                               headers={"Authorization": "Bearer " + K, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(r, timeout=60) as x:
            return json.loads(x.read())
    except urllib.error.HTTPError as e:
        return json.loads(e.read() or b"{}")


for saida, cmd in CMDS:
    r = chama("POST", "https://verygoodffmpeg.com/api/ffmpeg", {"input_files": {"in_video.mp4": DN}, "output_files": [saida],
                                                             "machine": "cpu", "timeout_seconds": 120, "ffmpeg_commands": [cmd]})
    d = r.get("data") or {}
    if not d.get("id"):
        print(saida, "recusado:", json.dumps(r)[:300]); continue
    while True:
        time.sleep(3)
        d = chama("GET", f"https://verygoodffmpeg.com/api/jobs/{d['id']}")["data"]
        if d["status"] not in ("queued", "running"):
            break
    print(saida, d["status"], d["error_message"][:200], (list((d.get("output_files") or {}).values()) or [""])[0][:90])
