# COMUM — fonte única: D:\hipercool-materiais\comum\content_analyzer.py. Mudou esta cópia? python D:\hipercool-materiais\bin\recursos.py subir content_analyzer.py --de <projeto>
"""content_analyzer.py — análise adaptativa da imagem do painel (porte do ContentAnalyzer do n8n).

Mede brilho/contraste/temperatura via ffmpeg signalstats e sugere uma CORREÇÃO de eq pra
ANEXAR ao grading já escolhido (não substitui): clareia painel escuro, sobe contraste lavado.

Padrão do projeto: cache por md5 (não re-mede no re-render), timeout curto, fallback neutro
(0.5) se falhar — nunca quebra o pipeline. Flag de uso fica no caller (CONTENT_ADAPT=1).
Técnica portada do fluxo n8n "3-cria video pequeno"; valores 9:16-safe (brilho independe de aspecto).
"""
import os
import json
import shutil
import hashlib
import subprocess
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = PROJECT_DIR / "workspace" / "content_analysis_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# thresholds do n8n (GLOBAL_CONFIG.contentAnalysis.adaptiveEffects)
BRIGHTNESS_THRESHOLD = float(os.environ.get("CONTENT_BRIGHTNESS_TH", "0.6"))
CONTRAST_THRESHOLD = float(os.environ.get("CONTENT_CONTRAST_TH", "0.4"))


def _ffmpeg():
    f = shutil.which("ffmpeg")
    if f:
        return f
    import glob as _g
    for pat in (str(Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/WinGet/**/ffmpeg.exe"),
                "C:/Users/*/AppData/Local/Microsoft/WinGet/**/ffmpeg.exe"):
        hits = _g.glob(pat, recursive=True)
        if hits:
            return hits[0]
    return "ffmpeg"


def _signalstats(img_path):
    """Roda 1 ffmpeg signalstats e extrai YAVG/YDIF/UAVG/VAVG. Cacheado por md5.
    Retorna dict {yavg,ydif,uavg,vavg} (0-255) ou None se falhar."""
    try:
        h = hashlib.md5(Path(img_path).read_bytes()).hexdigest()
    except Exception:
        return None
    cf = CACHE_DIR / f"{h}.json"
    if cf.exists():
        try:
            return json.loads(cf.read_text(encoding="utf-8"))
        except Exception:
            pass
    try:
        r = subprocess.run(
            [_ffmpeg(), "-i", str(img_path), "-vf", "signalstats,metadata=print:file=-", "-f", "null", "-"],
            capture_output=True, text=True, timeout=8)
        out = (r.stderr or "") + (r.stdout or "")
    except Exception:
        return None
    vals = {}
    for key, tag in (("yavg", "YAVG"), ("ydif", "YDIF"), ("uavg", "UAVG"), ("vavg", "VAVG")):
        v = None
        mark = f"lavfi.signalstats.{tag}="
        for line in out.splitlines():
            if mark in line:
                try:
                    v = float(line.split(mark)[1].strip().split()[0])
                except Exception:
                    v = None
        vals[key] = v
    if vals.get("yavg") is None:
        return None
    try:
        cf.write_text(json.dumps(vals, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass
    return vals


def brightness(img_path):
    """0-1 (0.5 neutro/fallback)."""
    s = _signalstats(img_path)
    if not s or s.get("yavg") is None:
        return 0.5
    return max(0.0, min(1.0, s["yavg"] / 255.0))


def contrast(img_path):
    """0-1 (0.5 neutro/fallback). YDIF/100 como o n8n."""
    s = _signalstats(img_path)
    if not s or s.get("ydif") is None:
        return 0.5
    return max(0.0, min(1.0, s["ydif"] / 100.0))


def palette(img_path):
    """{'type': warm|cool|neutral, 'warmth': 0-1}."""
    s = _signalstats(img_path)
    if not s or s.get("uavg") is None or s.get("vavg") is None:
        return {"type": "neutral", "warmth": 0.5}
    warmth = (s["vavg"] / 255.0 + s["uavg"] / 255.0) / 2.0
    t = "warm" if warmth > 0.6 else ("cool" if warmth < 0.4 else "neutral")
    return {"type": t, "warmth": warmth}


def adaptive_eq(img_path):
    """Retorna (eq_str|None, info). eq_str = trecho de filtro de CORREÇÃO p/ anexar ao grading.
    Regras do n8n: claro>0.6 → -0.05 brilho; escuro<0.4 → +0.05; contraste<0.4 → ×1.08."""
    b = brightness(img_path)
    c = contrast(img_path)
    pal = palette(img_path)
    badj = 0.0
    cadj = 1.0
    if b > BRIGHTNESS_THRESHOLD:
        badj = -0.05
    elif b < (1.0 - BRIGHTNESS_THRESHOLD):
        badj = 0.05
    if c < CONTRAST_THRESHOLD:
        cadj = 1.08
    info = {"brightness": round(b, 3), "contrast": round(c, 3),
            "palette": pal["type"], "brightnessAdjust": badj, "contrastAdjust": cadj}
    if badj == 0.0 and cadj == 1.0:
        return None, info
    parts = []
    if badj != 0.0:
        parts.append(f"brightness={badj:.3f}")
    if cadj != 1.0:
        parts.append(f"contrast={cadj:.3f}")
    return "eq=" + ":".join(parts), info
