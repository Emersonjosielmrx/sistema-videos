"""legendas: legenda queimada estilo Shorts (PIL com stroke, nao drawtext).

Timing: se audios_cache/<stem>.wav existir (modo antigo, com TTS no main),
usa a duracao do wav. Se nao existir (modo novo: audio original do Veo + TTS
so na propaganda), usa a duracao do video de entrada. Assim a fala eh
distribuida ao longo de TODO o video principal.

Layout: PNG com texto centralizado embaixo (85% da altura), branco + stroke preto,
fonte Impact/Arial Bold (Windows).

Se fala nao existir no meta, pula.
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

SUFFIX = "subs"
_BASE = Path(__file__).resolve().parent.parent.parent
_AUDIOS_CACHE = _BASE / "pos_producao" / "audios_cache"
_TMP = _BASE / "pos_producao" / "tmp"
_TMP.mkdir(parents=True, exist_ok=True)
_FFMPEG = r"D:\hipercool-materiais\bin\ffmpeg.exe"

sys.path.insert(0, str(_BASE / "pos_producao"))
from subtitles_veo import render_caption_png  # noqa: E402


def _ffprobe_duracao(path):
    try:
        r = subprocess.run(
            [_FFMPEG.replace("ffmpeg.exe", "ffprobe.exe"),
             "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1", str(path)],
            capture_output=True, text=True, timeout=15)
        for linha in (r.stdout or "").splitlines():
            if linha.startswith("duration="):
                return float(linha.split("=", 1)[1])
    except Exception:
        pass
    return None


def _chunk_fala(texto: str, audio_dur: float, max_chars=35, max_chunks=4):
    """Divide fala em N pedacos de ate max_chars, distribuindo duracao."""
    palavras = texto.split()
    chunks, cur = [], ""
    for p in palavras:
        test = (cur + " " + p).strip()
        if len(test) > max_chars and cur:
            chunks.append(cur)
            cur = p
        else:
            cur = test
    if cur:
        chunks.append(cur)
    if not chunks:
        return []
    chunks = chunks[:max_chunks]
    # distribuicao proporcional ao tamanho (palavras mais longas -> mais tempo)
    pesos = [max(1, len(c)) for c in chunks]
    total = sum(pesos)
    dt = audio_dur / total
    out = []
    for c, w in zip(chunks, pesos):
        d = dt * w
        out.append((c, d))
    return out


def processar(input_mp4: str, output_mp4: str, meta: dict) -> bool:
    fala = meta.get("fala")
    stem = meta.get("stem", "")
    if not fala or not stem:
        return False

    # descobre a duracao do video - se audio do TTS existir em cache usa
    # a duracao dele, senao (modo novo sem TTS no main) usa duracao do video
    vid_dur = meta.get("duracao_s") or _ffprobe_duracao(input_mp4)
    if not vid_dur:
        return False

    audio_path = _AUDIOS_CACHE / f"{stem}.wav"
    if not audio_path.exists():
        # tenta mp3
        audio_path = _AUDIOS_CACHE / f"{stem}.mp3"
    if audio_path.exists():
        audio_dur = _ffprobe_duracao(audio_path)
        if not audio_dur or audio_dur < 0.5:
            audio_dur = vid_dur
    else:
        # sem audio cache (TTS nao rodou no main) - distribui a fala pela duracao do video
        audio_dur = vid_dur

    # limita legenda ate min(audio_dur, vid_dur) e deixa o resto sem
    cap_dur = min(audio_dur, vid_dur)

    chunks = _chunk_fala(fala, cap_dur)
    if not chunks:
        return False

    # gera PNG pra cada chunk
    legendas = []
    t = 0.0
    pngs = []
    for texto, dur in chunks:
        png = _TMP / f"{stem}_sub_{int(t*1000)}.png"
        result = render_caption_png(texto, png, fontsize=85)
        if not result:
            continue
        png_path, x, y = result
        legendas.append({"png": str(png_path), "x": x, "y": y,
                         "start": t, "end": t + dur})
        pngs.append(png_path)
        t += dur

    if not legendas:
        return False

    # monta overlay com ffmpeg
    inputs = ["-i", str(input_mp4)]
    for leg in legendas:
        inputs += ["-loop", "1", "-t", f"{leg['end'] - leg['start']:.3f}", "-i", leg["png"]]

    fc_parts = []
    cur_v = "[0:v]"
    for i, leg in enumerate(legendas):
        idx = i + 1
        next_v = f"[v{i}]"
        fc_parts.append(
            f"{cur_v}[{idx}:v]overlay={leg['x']}:{leg['y']}:"
            f"enable='between(t,{leg['start']:.3f},{leg['end']:.3f})'{next_v}"
        )
        cur_v = next_v
    fc = ";".join(fc_parts)

    cmd = [_FFMPEG, "-y", "-hide_banner", "-loglevel", "error"] + inputs + [
        "-filter_complex", fc,
        "-map", cur_v, "-map", "0:a?",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
        "-c:a", "copy", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart", str(output_mp4),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)

    # limpa PNGs
    for p in pngs:
        try:
            Path(p).unlink()
        except Exception:
            pass

    return r.returncode == 0 and Path(output_mp4).exists()