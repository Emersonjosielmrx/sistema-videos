"""config.py — parâmetros ajustáveis num lugar SÓ (fim das constantes mágicas
espalhadas). Cada script importa daqui. Tudo é sobrescrevível por env var.

    import config as cfg
    dur = cfg.SHORTS_TARGET_DUR
"""
import os
import shutil


def _i(k, d): return int(os.environ.get(k, str(d)))
def _f(k, d): return float(os.environ.get(k, str(d)))
def _b(k, d): return os.environ.get(k, "1" if d else "0") == "1"


# ── Corte de Shorts (split-shorts.py) ──────────────────────────────
SHORTS_TARGET_DUR = _i("SHORTS_TARGET_DUR", 55)     # alvo por parte (s)
SHORTS_MIN_DUR    = _i("SHORTS_MIN_DUR", 30)        # mínimo por parte
SHORTS_MAX_DUR    = _i("SHORTS_MAX_DUR", 58)        # máximo (cabe no 60s c/ CTA)
SHORTS_CTA_DUR    = _f("SHORTS_CTA_DUR", 3.5)       # duração do CTA final
SILENCE_NOISE_DB  = _i("SILENCE_NOISE_DB", -35)     # limiar de silêncio (dB)
SILENCE_MIN_DUR   = _f("SILENCE_MIN_DUR", 0.3)

# ── ffmpeg / máquina ───────────────────────────────────────────────
FFMPEG_THREADS = os.environ.get("FFMPEG_THREADS", "4")   # limita p/ não travar a máquina toda
LOUDNORM       = _b("LOUDNORM", True)                    # normaliza volume dos shorts (YouTube pune volume irregular)

# ── Disco (o D: vive cheio) ────────────────────────────────────────
MIN_DISK_GB = _f("MIN_DISK_GB", 3.0)   # aborta antes de render se sobrar menos que isso


# ── Helpers de robustez (reusáveis) ────────────────────────────────
def disk_free_gb(path="D:\\"):
    try:
        return shutil.disk_usage(path).free / (1024 ** 3)
    except Exception:
        return 999.0


def timeout_por_duracao(dur_s, base=60, por_seg=4, teto=1800):
    """Timeout ffmpeg proporcional à duração do vídeo (não fixo)."""
    try:
        return int(min(teto, base + por_seg * max(0, float(dur_s))))
    except Exception:
        return base


def md5_file(path, chunk=1 << 20):
    import hashlib
    h = hashlib.md5()
    try:
        with open(path, "rb") as f:
            while True:
                b = f.read(chunk)
                if not b:
                    break
                h.update(b)
        return h.hexdigest()
    except Exception:
        return None


def validar_video(path):
    """ffprobe: retorna (ok, motivo). Checa dur>0, tem vídeo, áudio≥vídeo-5s, moov legível."""
    import subprocess
    p = str(path)
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                            "stream=codec_type,duration:format=duration",
                            "-of", "json", p], capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            return False, f"ffprobe falhou (moov?): {(r.stderr or '')[-150:]}"
        import json as _j
        d = _j.loads(r.stdout or "{}")
        fdur = float(d.get("format", {}).get("duration", 0) or 0)
        if fdur <= 0:
            return False, "duração 0 (arquivo vazio/corrompido)"
        vt = [s for s in d.get("streams", []) if s.get("codec_type") == "video"]
        at = [s for s in d.get("streams", []) if s.get("codec_type") == "audio"]
        if not vt:
            return False, "sem stream de vídeo"
        if at:
            adur = float(at[0].get("duration", 0) or 0)
            if adur and adur < fdur - 5.0:
                return False, f"áudio ({adur:.0f}s) muito menor que vídeo ({fdur:.0f}s) — QUEBRADO"
        return True, f"ok ({fdur:.0f}s)"
    except Exception as e:
        return False, f"erro: {e}"
