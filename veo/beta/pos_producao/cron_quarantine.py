"""cron_quarantine: detecta videos processados com defeito grave.

Uso: python -m pos_producao.cron_quarantine
Log: D:/veo/beta/pos_producao/cron_logs/cron_quarantine.jsonl

Heuristica (CPU-only):
  - extrai 5 frames espaçados do video
  - converte cada pra cinza
  - calcula variancia entre frames consecutivos (motion)
  - se variancia < threshold em >80% dos pares, eh estatico
  - tela preta: pixels < 20 em media

Se defeito: marca como _QUARANTINE.mp4 e cria flag pra agente revisar.
"""

import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime, timezone

_BASE = Path(r"D:/veo/beta")
_SRC = _BASE / "videos" / "cron_shorts"
_OUT = _BASE / "videos_pos" / "cron_shorts"
_QUARENTINE = _OUT / "_quarentine"
_QUARENTINE.mkdir(parents=True, exist_ok=True)
_LOGS = _BASE / "pos_producao" / "cron_logs"
_LOG_FILE = _LOGS / "cron_quarantine.jsonl"
_FFMPEG = r"D:\hipercool-materiais\bin\ffmpeg.exe"


def _log(obj: dict):
    obj["ts"] = datetime.now(timezone.utc).isoformat()
    obj["agente"] = "cron_quarantine"
    line = json.dumps(obj, ensure_ascii=False)
    with _LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line, flush=True)


def _extrair_frames(mp4: Path, n_frames=5):
    """Extrai n_frames espaçados e devolve lista de paths."""
    tmp = mp4.parent / f"_q_{mp4.stem}"
    tmp.mkdir(exist_ok=True)
    paths = []
    cmd = [
        _FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(mp4),
        "-vf", f"fps=1/{max(1, int(_dur(mp4)) // n_frames)}",
        "-frames:v", str(n_frames),
        str(tmp / "f_%02d.jpg"),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    for f in sorted(tmp.glob("f_*.jpg")):
        paths.append(f)
    return paths, tmp


def _dur(mp4: Path):
    try:
        r = subprocess.run(
            [r"D:\hipercool-materiais\bin\ffprobe.exe", "-v", "error",
             "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1", str(mp4)],
            capture_output=True, text=True, timeout=10,
        )
        for linha in (r.stdout or "").splitlines():
            if linha.startswith("duration="):
                return float(linha.split("=", 1)[1])
    except Exception:
        pass
    return 8.0


def _motion_score(frames):
    """Calcula variancia media entre frames consecutivos (PIL)."""
    if len(frames) < 2:
        return 0.0
    from PIL import Image, ImageChops
    grays = []
    for f in frames:
        try:
            img = Image.open(f).convert("L")
            img.thumbnail((160, 284))
            grays.append(img)
        except Exception:
            return 0.0
    diffs = []
    for i in range(len(grays) - 1):
        d = ImageChops.difference(grays[i], grays[i + 1])
        # variancia simples: media dos pixels
        hist = d.histogram()
        total = sum(i * c for i, c in enumerate(hist))
        n = sum(hist) or 1
        diffs.append(total / n)
    return sum(diffs) / len(diffs) if diffs else 0.0


def _eh_tela_preta(frames):
    """Verifica se pelo menos 1 frame eh majoritariamente preto."""
    from PIL import Image
    for f in frames:
        try:
            img = Image.open(f).convert("L")
            img.thumbnail((160, 284))
            hist = img.histogram()
            # soma dos 20 primeiros bins (pixels muito escuros)
            escuros = sum(hist[:20])
            total = sum(hist) or 1
            if escuros / total > 0.9:
                return True
        except Exception:
            return False
    return False


def _avaliar(mp4: Path):
    frames, tmp = _extrair_frames(mp4)
    if not frames:
        return {"motion": 0, "preto": False, "estatico": True}
    motion = _motion_score(frames)
    preto = _eh_tela_preta(frames)
    shutil.rmtree(tmp, ignore_errors=True)
    return {"motion": round(motion, 2), "preto": preto,
            "estatico": motion < 5.0 or preto}


def run():
    if not _OUT.exists():
        _log({"acao": "quarantine", "status": "erro", "detalhes": "out nao existe"})
        return
    avaliados = []
    quarentine = []
    # so processa mp4s recentes (ultimas 2h)
    import time
    cutoff = time.time() - 2 * 3600
    for mp4 in sorted(_OUT.glob("*.mp4")):
        if mp4.stem.startswith("_") or "_quarentine" in str(mp4):
            continue
        if mp4.stat().st_mtime < cutoff:
            continue
        try:
            res = _avaliar(mp4)
        except Exception as e:
            avaliados.append({"stem": mp4.stem, "erro": str(e)})
            continue
        avaliados.append({"stem": mp4.stem, **res})
        if res.get("estatico"):
            qpath = _QUARENTINE / mp4.name
            try:
                shutil.move(str(mp4), str(qpath))
                quarentine.append(mp4.name)
            except Exception as e:
                avaliados.append({"stem": mp4.stem, "erro_move": str(e)})
    _log({
        "acao": "quarantine", "status": "ok" if not quarentine else "warn",
        "detalhes": {"avaliados": avaliados, "quarentine": quarentine},
    })


if __name__ == "__main__":
    run()