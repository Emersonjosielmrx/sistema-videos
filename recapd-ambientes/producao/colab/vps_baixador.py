"""vps_baixador.py — BAIXADOR do YouTube nas VPS (hermes-prod, hermes-staging, hermes-bloqueio), junto com as sessões do
Kaggle (kaggle_trabalhador.linha_baixador). 04/11 dona: "ainda tem mais 3 VPS pra baixar e esse IP, 15 lugares".

Mesma fila no Drive: manhwa-drive:baixador/pedidos/<id>.json -> tomados/<quem>_<id>.json (renomear = 1 por pedido)
-> prontos/<id>/ (source.mp4 + cap.<lang>.vtt + ok.json por ÚLTIMO, ou erro.json). IP barrado pelo YouTube ("Sign in to
confirm", 429) = devolve o pedido pra outro baixador e fica 1 h parado. 1 download por vez. Só baixa vídeo — não fala com
nenhuma conta (nem Kaggle, nem Google).
Cron (em cada VPS): */5 * * * * flock -n /tmp/vps_baixador.lock /opt/recap_central/venv/bin/python /opt/recap_central/vps_baixador.py
"""
import json
import re
import os
import shutil
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
CONF = AQUI / "rclone.conf"
BX = "manhwa-drive:baixador"
QUEM = "vps-" + socket.gethostname()
TRAB = Path("/tmp/vps_baixador")
DISCO_MIN = 5e9
LOG = AQUI / "baixador" / "vps_baixador.log"


def _agora():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def log(m):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now():%d/%m %H:%M:%S}] {m}\n")


# 04/11: no cron o PATH é só /usr/bin:/bin e o rclone de 2 VPS fica em /usr/local/bin — falhava calado
RCLONE = next((c for c in (shutil.which("rclone"), "/usr/local/bin/rclone", "/usr/bin/rclone") if c and Path(c).exists()),
              "rclone")


def rc(*args, timeout=600):
    r = subprocess.run([RCLONE, "--config", str(CONF), *args], capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError(f"rclone {args[0]}: {r.stderr[-300:]}")
    return r.stdout


def marcar(dados, destino):
    tmp = TRAB / "_sinal.json"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    rc("copyto", str(tmp), destino, timeout=120)


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
        txt = r.stdout + r.stderr
        linhas = [l for l in txt.splitlines() if "ERROR" in l] or txt.splitlines()[-1:]
        # 04/11: o "Sign in to confirm" fica no COMEÇO — o corte [-300:] escondia o bloqueio (erro em vez de devolver)
        barrado = bool(re.search(r"Sign in to confirm|not a bot|HTTP Error (?:429|403)|Too Many Requests|Forbidden", txt))
        return {"erro": ("BARRADO: " if barrado else "") + " ".join(linhas)[:300]}
    for lang in p.get("legendas") or []:
        subprocess.run([sys.executable, "-m", "yt_dlp", url, "--skip-download", "--write-auto-subs", "--sub-langs", lang,
                        "--sub-format", "vtt", "-o", str(d / "cap"), "--no-warnings", "--no-playlist"],
                       capture_output=True, text=True, timeout=180)
        if any(d.glob(f"cap*.{lang}*.vtt")):
            break
    return {"video": video.name, "mb": round(video.stat().st_size / 1e6, 1), "s": round(time.time() - t0),
            "legendas": sorted(f.name for f in d.glob("cap*.vtt"))}


def main():
    barrado_ate, sinal = 0.0, 0.0
    log(f"no ar ({QUEM})")
    while True:
        if time.time() - sinal > 120:
            sinal = time.time()
            try:
                marcar({"em": _agora(), "por": QUEM, "barrado": time.time() < barrado_ate}, f"{BX}/vivos/{QUEM}.json")
                if time.time() >= barrado_ate:
                    marcar({"em": _agora(), "por": QUEM}, f"{BX}/vivo.json")
            except Exception as e:  # noqa: BLE001
                log(f"sinal de vida falhou: {type(e).__name__}: {str(e)[:150]}")
        if time.time() < barrado_ate or shutil.disk_usage("/tmp").free < DISCO_MIN:
            time.sleep(120)
            continue
        try:
            pedidos = sorted(l.strip() for l in rc("lsf", f"{BX}/pedidos", "--files-only", timeout=120).splitlines()
                             if l.strip().endswith(".json"))
        except Exception as e:  # noqa: BLE001
            time.sleep(600 if any(s in str(e) for s in ("403", "ateLimit", "Quota")) else 60)
            continue
        if not pedidos:
            time.sleep(20)
            continue
        nome = pedidos[0]
        tomado = f"{BX}/tomados/{QUEM}_{nome}"
        try:
            rc("moveto", f"{BX}/pedidos/{nome}", tomado, timeout=120)
            p = json.loads(rc("cat", tomado, timeout=120))
        except Exception:  # noqa: BLE001
            time.sleep(5)
            continue
        try:
            res = baixar(p)
        except Exception as e:  # noqa: BLE001
            res = {"erro": f"{type(e).__name__}: {str(e)[:250]}"}
        erro = str(res.get("erro") or "")
        if erro.startswith("BARRADO") or any(s in erro for s in ("Sign in to confirm", "not a bot", "429",
                                                                  "Too Many Requests", "403", "Forbidden")):
            barrado_ate = time.time() + 3600
            try:
                rc("moveto", tomado, f"{BX}/pedidos/{nome}", timeout=120)
            except Exception:  # noqa: BLE001
                pass
            shutil.rmtree(TRAB / p["id"], ignore_errors=True)
            log(f"IP barrado pelo YouTube — {p['id']} devolvido; 1 h sem baixar")
            continue
        res.update(id=p["id"], em=_agora(), por=QUEM)
        d = TRAB / p["id"]
        d.mkdir(parents=True, exist_ok=True)
        (d / ("erro.json" if erro else "ok.json")).write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")
        try:
            for f in sorted(d.iterdir(), key=lambda x: x.name in ("ok.json", "erro.json")):
                rc("copyto", str(f), f"{BX}/prontos/{p['id']}/{f.name}")
            rc("deletefile", tomado, timeout=120)
        except Exception as e:  # noqa: BLE001
            log(f"subir {p['id']}: {e}")
            if any(s in str(e) for s in ("403", "ateLimit", "Quota")):
                time.sleep(600)
        shutil.rmtree(d, ignore_errors=True)
        log(f"{p['id']}: {json.dumps(res, ensure_ascii=False)[:200]}")


if __name__ == "__main__":
    main()
