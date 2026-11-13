# -*- coding: utf-8 -*-
"""hp_common.py — base compartilhada do pipeline historias-em-frames.

Caminhos do projeto + log() + defaults.
"""
import os
import sys
from datetime import datetime
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent


def _dir_env(var, default):
    """Path de env var (se setada) ou default local. Permite que cada 'pista'
    (prod/beta/teste) aponte a saida pra uma pasta propria sem tocar no codigo."""
    v = os.environ.get(var)
    return Path(v) if v else default


def _settings():
    try:
        import json as _json
        return _json.loads((PROJECT_DIR / "config" / "settings.json").read_text(encoding="utf-8"))
    except Exception:
        return {}


# VIDEOS_DIR e a saida final e fica SEMPRE em hipercool-materiais (cada projeto grava os
# videos gerados la, nunca dentro da propria pasta):
#   <materiais_dir do settings.json>\videos\<pista>  ex.: ...\historias-em-frames\videos\prod
# HEF_VIDEOS_DIR (auto_producer) ainda tem prioridade. Antes, sem a env, caia em
# workspace/videos do projeto — foi assim que se acumularam 263 videos dentro da prod.
_S = _settings()
MATERIAIS_DIR = Path(os.environ.get("HEF_MATERIAIS_DIR")
                     or _S.get("materiais_dir")
                     or r"D:\hipercool-materiais\historias-em-frames")
PISTA = _S.get("pista", "dev")
VIDEOS_DIR = _dir_env("HEF_VIDEOS_DIR", MATERIAIS_DIR / "videos" / PISTA)
QUARANTINE_DIR = VIDEOS_DIR / "_quarantine"
CACHE_DIR = _dir_env("HEF_CACHE_DIR", PROJECT_DIR / "workspace" / "cache")
TMP_DIR = PROJECT_DIR / "workspace" / "tmp"
STORIES_DIR = PROJECT_DIR / "workspace" / "stories"
IMAGES_DIR = PROJECT_DIR / "workspace" / "images"
NARRATION_CACHE_DIR = PROJECT_DIR / "workspace" / "narration_cache"
WATERMARK_HANDLE = os.environ.get("STORIES_WATERMARK", "@InovareStories")
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
TMP_DIR.mkdir(parents=True, exist_ok=True)
STORIES_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
MAX_SCENES_DEFAULT = 12
TEST_MODE = int(os.environ.get("TEST_MODE", "0"))
_ERR_MARKERS = ("erro", "error", "falha", "fail", "⚠", "✗", "traceback", "exception")


CLIPES_DIR = TMP_DIR / "clipes_parado"


def clipe_parado(img, dur):
    """Imagem parada como clipe .mov curto (qtrle, com alfa), em cache.
    Evita '-loop 1 -i imagem' que trava o ffmpeg 8 (o ffmpeg relê o arquivo a cada quadro;
    PNGs com chunks duplicados ou muitas entradas -loop 1 no grafo fazem o render congelar
    sem usar CPU). Lendo uma vez e repetindo com loop= no filtro, o mesmo arquivo sai normal.

    Retorna (mov_path, ['-i', str(mov_path)]) — os args do ffmpeg já prontos."""
    import hashlib, subprocess
    img = Path(img)
    chave = hashlib.md5(f"{img.resolve()}|{img.stat().st_mtime_ns}|v2".encode()).hexdigest()[:10]
    mov = CLIPES_DIR / f"{img.stem[:40]}_{chave}_{dur:.2f}.mov"
    if not mov.exists():
        CLIPES_DIR.mkdir(parents=True, exist_ok=True)
        tmp = mov.with_name(mov.stem + "_tmp.mov")
        n = max(1, int(round(dur * 25)))
        subprocess.run(["ffmpeg", "-y", "-i", str(img),
                        "-vf", f"loop=loop={n - 1}:size=1:start=0,fps=25,format=argb",
                        "-frames:v", str(n), "-c:v", "qtrle", str(tmp)],
                       capture_output=True, timeout=120)
        os.replace(str(tmp), str(mov))
    return mov, ["-i", str(mov)]


def fix_loop1_cmd(cmd):
    """Reescreve uma lista de args ffmpeg: cada '-loop 1 -t X -i arquivo_de_imagem' vira
    '-i clipe.mov' (via clipe_parado). Entradas de vídeo/áudio ficam intactas.
    Chame logo antes de subprocess.run(cmd, ...)."""
    _IMG = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}
    out = []
    i = 0
    while i < len(cmd):
        s = str(cmd[i])
        # Detecta: -loop  1  [-t  X]  -i  imagem.ext
        if s == "-loop" and i + 1 < len(cmd) and str(cmd[i + 1]) == "1":
            j = i + 2
            dur = None
            if j + 1 < len(cmd) and str(cmd[j]) == "-t":
                try:
                    dur = float(cmd[j + 1])
                except (ValueError, TypeError):
                    dur = None
                j += 2
            if j + 1 < len(cmd) and str(cmd[j]) == "-i":
                caminho = str(cmd[j + 1])
                ext = Path(caminho).suffix.lower()
                if ext in _IMG and dur is not None and Path(caminho).is_file():
                    _, args = clipe_parado(caminho, dur)
                    out.extend(args)
                    i = j + 2
                    continue
        out.append(cmd[i])
        i += 1
    return out


def log(msg):
    """Log com timestamp no stderr."""
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", file=sys.stderr)
