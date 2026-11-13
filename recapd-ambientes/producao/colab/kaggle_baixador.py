"""Roda no KAGGLE (kernel CPU com internet): BAIXADOR do YouTube para a casa (30/10/2026, D43; dona: "usar as VPS e as
GPUs que têm outros IPs"). O IP de casa (PC1/PC2/notebooks = 191.36.137.42) leva a checagem de robô do YouTube e o
yt-dlp do PC inteiro pausa; o IP do Kaggle baixou sem bloqueio (teste 30/10: 2 vídeos em 5 s e 2 s).

Fila pelo Drive (rclone, conf do dataset privado recap-worker-conf, igual ao kaggle_trabalhador.py):
  manhwa-drive:baixador/pedidos/<id>.json   {"id", "url", "max_height", "legendas": ["pt", "es"]}  (o PC1 escreve)
  manhwa-drive:baixador/prontos/<id>/       source.mp4 + cap.<lang>.vtt + ok.json (por ÚLTIMO) ou erro.json
  manhwa-drive:baixador/vivo.json           sinal de vida a cada volta (o PC1 só pede se estiver vivo)
Mesmo formato do anime_fetch.download_video (em pé até 720 de largura, senão até 720p; H.264; mp4) e da
fetch_captions (auto-legenda, 1 idioma por vez, es só se o pt não vier).
"""
import io
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

INICIO = time.time()
LIMITE_S = float(os.environ.get("BAIXADOR_LIMITE_H", "11.5")) * 3600  # o Kaggle corta em 12 h; a tarefa relança
BASE = Path("/kaggle/working")
CONF = next(Path("/kaggle/input").rglob("rclone.conf"))
RC = Path("/tmp/rclone")
RAIZ = "manhwa-drive:baixador"
os.environ["RCLONE_DRIVE_USE_TRASH"] = "false"
TRAB = Path("/tmp/baixador")


def _agora():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def rc(*args):
    r = subprocess.run([str(RC), "--config", str(CONF), *args], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"rclone {args[0]}: {r.stderr[-300:]}")
    return r.stdout


def preparar():
    conf = Path("/tmp/rclone.conf")  # gravável (o rclone regrava o token) e fora do /kaggle/working (saída pública)
    shutil.copy(CONF, conf)
    globals()["CONF"] = conf
    pedido = urllib.request.Request("https://downloads.rclone.org/rclone-current-linux-amd64.zip",
                                    headers={"User-Agent": "Mozilla/5.0"})
    with zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(pedido).read())) as zf:
        RC.write_bytes(zf.read(next(n for n in zf.namelist() if n.endswith("/rclone"))))
    RC.chmod(0o755)
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-U", "yt-dlp"], check=True)


def _motivo(r):
    linhas = [l for l in (r.stdout + r.stderr).splitlines() if "ERROR" in l] or (r.stdout + r.stderr).splitlines()[-1:]
    return " ".join(linhas)[-300:]


def baixar(p):
    vid, url, mh = p["id"], p["url"], int(p.get("max_height") or 720)
    d = TRAB / vid
    shutil.rmtree(d, ignore_errors=True)
    d.mkdir(parents=True)
    t0 = time.time()
    fmt = f"bv*[aspect_ratio<0.9][width<={mh}]+ba/bv*[height<={mh}]+ba/b[height<={mh}]/b"
    r = subprocess.run([sys.executable, "-m", "yt_dlp", url, "-f", fmt, "-S", "res,vcodec:h264",
                        "--merge-output-format", "mp4", "-o", str(d / "source.%(ext)s"), "--no-warnings",
                        "--no-playlist"], capture_output=True, text=True, timeout=1800)
    video = next((f for f in d.glob("source.*") if f.suffix.lower() in (".mp4", ".mkv", ".webm")), None)
    if r.returncode != 0 or not video:
        return {"erro": _motivo(r)}
    for lang in p.get("legendas") or []:
        subprocess.run([sys.executable, "-m", "yt_dlp", url, "--skip-download", "--write-auto-subs", "--sub-langs", lang,
                        "--sub-format", "vtt", "-o", str(d / "cap"), "--no-warnings", "--no-playlist"],
                       capture_output=True, text=True, timeout=180)
        if any(d.glob(f"cap*.{lang}*.vtt")):
            break
    return {"video": video.name, "mb": round(video.stat().st_size / 1e6, 1), "s": round(time.time() - t0),
            "legendas": sorted(f.name for f in d.glob("cap*.vtt"))}


def loop():
    while time.time() - INICIO < LIMITE_S:
        try:
            (TRAB / "vivo.json").parent.mkdir(parents=True, exist_ok=True)
            (TRAB / "vivo.json").write_text(json.dumps({"em": _agora(), "desde": INICIO}), encoding="utf-8")
            rc("copyto", str(TRAB / "vivo.json"), f"{RAIZ}/vivo.json")
            pedidos = sorted(l.strip() for l in rc("lsf", f"{RAIZ}/pedidos", "--files-only").splitlines()
                             if l.strip().endswith(".json"))
        except Exception as e:  # noqa: BLE001
            print("fila:", e, flush=True)
            time.sleep(30)
            continue
        if not pedidos:
            time.sleep(15)
            continue
        nome = pedidos[0]
        try:
            rc("copyto", f"{RAIZ}/pedidos/{nome}", str(TRAB / nome))
            p = json.loads((TRAB / nome).read_text(encoding="utf-8"))
            rc("deletefile", f"{RAIZ}/pedidos/{nome}")  # pegou: sai da fila (1 baixador por vez)
        except Exception as e:  # noqa: BLE001
            print("pegar", nome, e, flush=True)
            time.sleep(10)
            continue
        try:
            res = baixar(p)
        except Exception as e:  # noqa: BLE001
            res = {"erro": f"{type(e).__name__}: {str(e)[:250]}"}
        res.update(id=p["id"], em=_agora(), ip=_ip())
        d = TRAB / p["id"]
        d.mkdir(parents=True, exist_ok=True)
        fim = d / ("erro.json" if res.get("erro") else "ok.json")
        fim.write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")
        try:  # arquivos primeiro, o marcador por último (o PC1 só pega com ok.json lá)
            for f in sorted(d.iterdir(), key=lambda x: x.name in ("ok.json", "erro.json")):
                rc("copyto", str(f), f"{RAIZ}/prontos/{p['id']}/{f.name}")
        except Exception as e:  # noqa: BLE001
            print("subir", p["id"], e, flush=True)
        shutil.rmtree(d, ignore_errors=True)
        print(p["id"], json.dumps(res, ensure_ascii=False)[:300], flush=True)


_IP = None


def _ip():
    global _IP
    if _IP is None:
        try:
            _IP = urllib.request.urlopen("https://api.ipify.org", timeout=10).read().decode()
        except Exception:  # noqa: BLE001
            _IP = "?"
    return _IP


if __name__ == "__main__":
    preparar()
    print("baixador no ar, IP", _ip(), flush=True)
    loop()
