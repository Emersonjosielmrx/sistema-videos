"""Pós-processamento da narração dos Shorts (trecho de comum/narracao_curva.py)."""
import json
import os
import shutil
import wave
from pathlib import Path

import numpy as np

LIMIAR_SILENCIO_DB = -40.0   # quadro de 10 ms abaixo disso (dBFS) é silêncio
GAP_MICROCORTE = 0.07        # segundos de silêncio que ficam entre as falas


def ler_palavras(wav):
    """Lista de {"word", "start", "end"} (segundos) do <wav>.words.json, ou [] se não tem."""
    p = Path(str(wav) + ".words.json")
    return json.loads(p.read_text("utf-8")) if p.exists() else []


def gravar_palavras(wav, palavras):
    Path(str(wav) + ".words.json").write_text(json.dumps(palavras, ensure_ascii=False), "utf-8")


def microcortes(wav, gap_s=None):
    """No lugar. Devolve (duração antes, depois) ou None (nada a cortar: wav e words.json como vieram)."""
    wav = Path(wav)
    gap = float(gap_s if gap_s is not None else os.environ.get("NARRACAO_GAP_MICROCORTE") or GAP_MICROCORTE)
    with wave.open(str(wav)) as f:
        sr, ch, sw, n = f.getframerate(), f.getnchannels(), f.getsampwidth(), f.getnframes()
        bruto = f.readframes(n)
    if sw != 2 or n < sr // 10:
        return None
    y = np.frombuffer(bruto, dtype="<i2").reshape(-1, ch).astype(np.float32)
    quadro = max(1, sr // 100)  # 10 ms
    nq = len(y) // quadro
    mono = y[:nq * quadro].mean(axis=1) / 32768
    db = 10 * np.log10((mono.reshape(nq, quadro) ** 2).mean(axis=1) + 1e-12)
    som = db > LIMIAR_SILENCIO_DB
    bordas = np.flatnonzero(np.diff(np.concatenate([[0], som.astype(np.int8), [0]])))
    trechos = [(a * quadro, min(len(y), b * quadro)) for a, b in zip(bordas[::2], bordas[1::2]) if b - a >= 2]
    if not trechos:
        return None
    meio, xf = int(gap * sr / 2), max(1, int(0.006 * sr))
    pecas, ini = [], max(0, trechos[0][0] - meio)
    for (_a1, b1), (a2, _b2) in zip(trechos, trechos[1:]):
        if a2 - b1 > 2 * meio + 2 * xf:
            pecas.append((ini, b1 + meio + xf))
            ini = a2 - meio - xf
    pecas.append((ini, min(len(y), trechos[-1][1] + meio)))
    out, mapa = y[pecas[0][0]:pecas[0][1]], [(pecas[0][0], pecas[0][1], 0)]
    for a, b in pecas[1:]:
        p = y[a:b]
        f = min(xf, len(out), len(p))
        rampa = np.linspace(0, 1, f, dtype=np.float32)[:, None]
        mapa.append((a, b, len(out) - f))
        out = np.concatenate([out[:len(out) - f], out[len(out) - f:] * (1 - rampa) + p[:f] * rampa, p[f:]])
    dur0, dur1 = len(y) / sr, len(out) / sr
    if dur0 - dur1 < 0.02:
        return None
    tmp = wav.with_name(wav.stem + ".cortes.wav")
    with wave.open(str(tmp), "wb") as f:
        f.setnchannels(ch)
        f.setsampwidth(2)
        f.setframerate(sr)
        f.writeframes(np.clip(np.round(out), -32768, 32767).astype("<i2").tobytes())
    shutil.move(str(tmp), str(wav))

    def novo(t):
        s = t * sr
        for a, b, d in mapa:
            if s < a:
                return d / sr
            if s <= b:
                return (d + s - a) / sr
        return dur1

    palavras = ler_palavras(wav)
    if palavras:
        gravar_palavras(wav, [{**w, "start": round(novo(w["start"]), 3), "end": round(novo(w["end"]), 3)}
                              for w in palavras])
    return round(dur0, 3), round(dur1, 3)
