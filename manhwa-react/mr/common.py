import json, os, subprocess, sys, time, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def load_config(path=None):
    p = Path(path) if path else ROOT / "config.json"
    with open(p, encoding="utf-8") as f:
        cfg = json.load(f)
    _juntar_rede(cfg)
    return cfg


def _juntar_rede(cfg):
    """Canais ativos do mapa da rede (D:/postador-de-videos/config/rede_canais.json, fonte unica) entram em cfg['channels']:
    o editorial distribui entre eles e o render usa o handle/cor certos. Os do config.json mantem o resto (kit, divisoria...)."""
    rp = Path((cfg.get("rede") or {}).get("arquivo", "D:/postador-de-videos/config/rede_canais.json"))
    if not rp.exists():
        return
    try:
        rede = json.loads(rp.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        log(f"rede_canais.json ilegivel ({e}) - usando so config.json")
        return
    chans = cfg.setdefault("channels", [])
    by = {c["slug"]: c for c in chans}
    for rc in rede.get("canais", []):
        if rc.get("status") != "ativo":
            continue
        ch = by.get(rc["slug"])
        if not ch:
            ch = {"slug": rc["slug"]}
            chans.append(ch)
            by[rc["slug"]] = ch
        ch.update({"name": rc.get("nome") or ch.get("name"), "handle": rc.get("handle") or ch.get("handle"),
                   "color": ch.get("color") or rc.get("cor", "#FFD700"), "niche": rc.get("nicho") or ch.get("niche", ""),
                   "youtube_id": (rc.get("creds") or [ch.get("youtube_id")])[0], "rede": rc})

def log(msg):
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

def ffpath(p):
    """Escapa um caminho Windows para uso dentro de uma string de filtro do ffmpeg."""
    s = str(p).replace("\\", "/").replace("'", "")
    return "'" + s.replace(":", "\\:") + "'"

def run(cmd, check=True, capture=False, quiet=True, cwd=None, timeout=None):
    """Executa um comando (lista). Retorna CompletedProcess."""
    if not quiet:
        log("$ " + " ".join(f'"{c}"' if " " in str(c) else str(c) for c in cmd))
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=cwd, timeout=timeout)
    if check and res.returncode != 0:
        tail = (res.stderr or "")[-3000:]
        raise RuntimeError(f"Comando falhou ({res.returncode}): {cmd[0]}\n{tail}")
    return res

def ffmpeg(cfg, args, **kw):
    return run([cfg["paths"]["ffmpeg"], "-hide_banner", "-y", "-loglevel", "error", *args], **kw)

def ffprobe_json(cfg, path):
    res = run([cfg["paths"]["ffprobe"], "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)])
    return json.loads(res.stdout)

def save_json(obj, path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def fmt_t(t):
    m, s = divmod(float(t), 60)
    return f"{int(m):02d}:{s:05.2f}"
