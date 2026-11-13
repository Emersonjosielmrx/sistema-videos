#!/usr/bin/env python3
"""parallax_engine.py — movimento real (parallax 2.5D) nos painéis do hipercool.

Substitui o Ken Burns por parallax baseado em DEPTH MAP real (Depth-Anything V2, CPU).
Separa o painel em 3 camadas por profundidade e move cada uma em velocidade diferente
→ sensação de câmera entrando numa cena 3D.

CACHE: reusa o MESMO cache que o MotionFrames (D:\\hipercool-motionframes\\cache\\depth)
já popula em background. O depth (etapa cara ~20s) é cacheado por md5 do CONTEÚDO da
imagem → painel idêntico = 1 depth só, compartilhado entre cópias/máquinas.

FALLBACK TOTAL: qualquer falha (modelo, depth, ffmpeg) → retorna False e o caller usa
o build_clip (Ken Burns) de sempre. NUNCA trava o pipeline.

A duração do clip casa EXATO com a do áudio (o concat força durs_eff; drift = ruído).
"""
import os
# CRÍTICO: limitar threads do BLAS/OMP ANTES de importar numpy/torch. Sem isto,
# o OpenBLAS abre 1 pool de threads POR núcleo e cada um pré-aloca buffers enormes
# → "OpenBLAS error: Memory allocation still failed after 10 retries" quando há
# outros processos competindo por RAM (render paralelo). O depth roda em segundos
# mesmo com 2 threads, então limitar não custa velocidade perceptível e evita o
# crash que fazia TODO clip cair no fallback Ken Burns (2.5D nunca aparecia).
for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS",
           "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "2")

import hashlib
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter


def _tem_ram(min_gb=2.0):
    """Retorna True se há pelo menos min_gb GB de RAM disponível. Evita OOM no depth."""
    try:
        import psutil
        avail = psutil.virtual_memory().available / (1024 ** 3)
        return avail >= min_gb
    except Exception:
        return True  # assume OK se psutil indisponível

# Cache de depth. Default LOCAL a esta pista (independente de outros projetos).
# Se MOTIONFRAMES_DEPTH_CACHE estiver setada, reusa o cache compartilhado do
# MotionFrames como OTIMIZACAO (opcional). Sem ele, cada pista computa o proprio
# depth (o modelo carrega sozinho; ha fallback total pro Ken Burns).
_MF_CACHE = Path(os.environ.get(
    "MOTIONFRAMES_DEPTH_CACHE",
    str(Path(__file__).resolve().parent.parent / "workspace" / "cache" / "depth")))
_MODEL = "depth-anything/Depth-Anything-V2-Small-hf"
ALGO_VER = 1  # bump invalida lógica (não o depth, que é estável)

_pipe = None


def log(m):
    print(f"[parallax] {m}", file=sys.stderr, flush=True)


def _md5_file(p, chunk=1 << 20):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def _get_pipe():
    global _pipe
    if _pipe is None:
        try:
            import torch
            torch.set_num_threads(2)  # reforça o limite do env (evita OOM do OpenBLAS)
        except Exception:
            pass
        from transformers import pipeline
        t0 = time.time()
        _pipe = pipeline("depth-estimation", model=_MODEL)
        log(f"modelo carregado {time.time()-t0:.1f}s")
    return _pipe


def get_depth(img_path, target_wh):
    """Retorna PIL.Image L do depth, do cache se houver, senão calcula e cacheia.
    target_wh = (W,H) do vídeo final. O depth é salvo na resolução do vídeo."""
    W, H = target_wh
    try:
        md5 = _md5_file(img_path)
    except Exception:
        md5 = None
    cache_png = (_MF_CACHE / f"{md5}.png") if md5 else None
    if cache_png and cache_png.exists() and cache_png.stat().st_size > 0:
        try:
            d = Image.open(cache_png).convert("L")
            if d.size != (W, H):
                d = d.resize((W, H))
            return d
        except Exception:
            pass  # cache corrompido → recalcula
    # calcula
    img = Image.open(img_path).convert("RGB").resize((W, H))
    try:
        d = _get_pipe()(img)["depth"].convert("L")
    except (MemoryError, OSError) as _me:
        # FIX: "paging file too small" crash — RAM insuficiente pro depth estimation.
        # O caller (build_parallax_clip) já trata False como fallback Ken Burns.
        log(f"get_depth: RAM/memory error ({_me}) — retornando None")
        return None
    except Exception as _e:
        log(f"get_depth: erro {type(_e).__name__}: {_e}")
        return None
    if cache_png:
        try:
            _MF_CACHE.mkdir(parents=True, exist_ok=True)
            d.save(cache_png)
        except Exception:
            pass
    return d


def _fit(img_path, W, H):
    img = Image.open(img_path).convert("RGB")
    img = img.resize((W, int(W * img.height / img.width)))
    if img.height < H:
        img = img.resize((int(H * img.width / img.height), H))
    return img.crop((0, 0, W, H)) if img.size != (W, H) else img


# Estilos de câmera do catálogo (orbit/push_in/float/sweep). Cada um define, por
# camada i (s = velocidade da camada), as expressões ffmpeg de deslocamento x/y do
# crop e o zoom base z. Variar isto por mood quebra a monotonia do movimento 2.5D
# (antes era SEMPRE o mesmo float). t = tempo em segundos; PI/sin/cos são do ffmpeg.
def _camera_expr(move, s, W, H):
    """Retorna (x_expr, y_expr, z) para a camada com velocidade s."""
    cx = f"(in_w-{W})/2"
    cy = f"(in_h-{H})/2"
    if move == "orbit":
        # órbita elíptica: x=sin, y=cos (meia amplitude) → câmera girando ao redor
        return (f"{cx}+{s*7:.1f}*sin(2*PI*t/9)",
                f"{cy}+{s*4:.1f}*cos(2*PI*t/9)", 1.06)
    if move == "push_in":
        # empurra pra dentro: sem deslocamento lateral, o zoom cresce (feito no scale)
        return (cx, cy, 1.10)
    if move == "sweep":
        # varredura lateral (esquerda→direita ao longo de 9s) + leve respiro vertical
        return (f"{cx}+{s*9:.1f}*(2*t/9-1)",
                f"{cy}+{s*2:.1f}*sin(2*PI*t/11)", 1.05)
    # float (default): dois senos defasados → flutuação suave
    return (f"{cx}+{s*6:.1f}*sin(2*PI*t/8)",
            f"{cy}+{s*3.5:.1f}*sin(2*PI*t/11)", 1.05)


# Mapa mood → estilo de câmera. Ação/tensão pede órbita/varredura (mais dinâmico);
# emoção/calma pede float/push suave. Assim o movimento CASA com o clima da cena.
_MOOD_MOVE = {
    "tense_dramatic": "orbit", "action": "sweep", "battle": "sweep",
    "sad_emotional": "push_in", "romantic_sexy": "float", "romance": "float",
    "funny_lighthearted": "float", "calm_chill": "push_in", "neutral_chill": "float",
    "suspense": "orbit", "fear": "orbit", "dark": "orbit", "mystery": "orbit",
}


# Para cada "clima" há uma LISTA de movimentos que combinam, em vez de um só. Assim,
# mesmo num vídeo inteiro do mesmo mood (ex: terror = tudo tenso), o movimento varia
# de cena pra cena (orbit→sweep→push_in...) e não fica monótono. O índice da cena
# escolhe qual da lista usar (rotação determinística, reproduzível).
_MOOD_MOVES = {
    "tense_dramatic": ["orbit", "sweep", "push_in"],
    "suspense": ["orbit", "push_in", "sweep"],
    "fear": ["orbit", "push_in", "sweep"],
    "dark": ["orbit", "sweep", "push_in"],
    "mystery": ["orbit", "float", "push_in"],
    "action": ["sweep", "orbit", "push_in"],
    "battle": ["sweep", "orbit", "push_in"],
    "sad_emotional": ["push_in", "float", "orbit"],
    "romantic_sexy": ["float", "push_in", "orbit"],
    "romance": ["float", "push_in", "orbit"],
    "funny_lighthearted": ["float", "sweep", "orbit"],
    "calm_chill": ["push_in", "float", "orbit"],
    "neutral_chill": ["float", "push_in", "sweep"],
}
_ALL_MOVES = ["orbit", "push_in", "float", "sweep"]


def move_for_mood(mood, idx=0):
    """Escolhe o estilo de câmera a partir do mood + índice da cena. O mood define
    a LISTA de movimentos que combinam com o clima; idx rotaciona dentro dela para
    dar variedade visual mesmo quando o mood não muda ao longo do vídeo."""
    moves = None
    if mood:
        m = str(mood).lower()
        for k, v in _MOOD_MOVES.items():
            if k in m:
                moves = v
                break
    if not moves:
        moves = _ALL_MOVES
    return moves[idx % len(moves)]


def build_parallax_clip(img_path, audio_path, out_path, duration=None,
                        W=720, H=1280, fps=30, terror=False, move="float"):
    """Gera o clip de parallax 2.5D. duration: se None, lê do áudio.
    terror=True adiciona atmosfera (vinheta/grão/tom frio).
    move: estilo de câmera (orbit/push_in/float/sweep) — varia o movimento por cena.
    Retorna True/False."""
    t0 = time.time()
    try:
        if duration is None:
            r = subprocess.run(
                ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                 "-of", "csv=p=0", str(audio_path)],
                capture_output=True, text=True, timeout=10)
            duration = float(r.stdout.strip())
        duration = max(duration, 1.2)

        img = _fit(img_path, W, H)
        # FIX: verificar RAM antes de depth (~2GB adicional). Se insuficiente,
        # retorna False imediatamente em vez de OOM crashar o ffmpeg.
        if not _tem_ram(min_gb=2.0):
            log(f"build_parallax_clip: RAM < 2GB — abortando depth (fallback)")
            return False
        depth = get_depth(img_path, (W, H))
        if depth is None:
            return False  # RAM error, caller handles fallback
        d = np.asarray(depth, dtype=np.float32) / 255.0

        base = Path(out_path).with_suffix("")
        layers = []
        for name, lo, hi in [("far", 0.0, 0.4), ("mid", 0.4, 0.7), ("near", 0.7, 1.01)]:
            mask = ((d >= lo) & (d < hi)).astype(np.uint8) * 255
            m = Image.fromarray(mask).filter(ImageFilter.GaussianBlur(6))
            rgba = img.convert("RGBA")
            rgba.putalpha(m)
            p = f"{base}_pl_{name}.png"
            rgba.save(p)
            layers.append(p)

        speed = [0.5, 1.1, 2.0]
        inputs, fc = [], []
        for i, p in enumerate(layers):
            inputs += ["-loop", "1", "-i", p]
            s = speed[i]
            x_expr, y_expr, zbase = _camera_expr(move, s, W, H)
            # push_in cresce o zoom ao longo do tempo (o scale é fixo, então o crop
            # simula o avanço reduzindo a janela via zoom base maior nas camadas perto).
            z = zbase + 0.015 * i
            bw, bh = int(W * z * 1.1), int(H * z * 1.1)
            fc.append(
                f"[{i}:v]scale={bw}:{bh},crop={W}:{H}:"
                f"'{x_expr}':'{y_expr}'[l{i}]")
        fc.append("[l0][l1]overlay=0:0[m1]")
        fc.append("[m1][l2]overlay=0:0[stk]")
        if terror:
            fc.append(
                "[stk]eq=saturation=0.55:contrast=1.12:brightness=-0.04,"
                "colorbalance=rs=-0.03:gs=0:bs=0.06,vignette=PI/4.5,"
                "noise=alls=11:allf=t[vout]")
        else:
            fc.append("[stk]null[vout]")

        cmd = ["ffmpeg", "-y", *inputs, "-i", str(audio_path),
               "-filter_complex", ";".join(fc),
               "-map", "[vout]", "-map", f"{len(layers)}:a",
               "-t", f"{duration:.3f}", "-r", str(fps),
               "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
               "-preset", "veryfast", "-threads", "4",
               "-c:a", "aac", "-b:a", "128k", "-shortest", str(out_path)]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        for p in layers:
            try:
                Path(p).unlink()
            except Exception:
                pass
        if r.returncode != 0:
            log(f"ffmpeg falhou: {r.stderr[-400:]}")
            return False
        ok = Path(out_path).exists() and Path(out_path).stat().st_size > 0
        if ok:
            log(f"clip {Path(img_path).name} {time.time()-t0:.1f}s (dur {duration:.2f}s)")
        return ok
    except Exception as e:
        log(f"erro ({type(e).__name__}: {str(e)[:80]}) → fallback Ken Burns")
        return False
