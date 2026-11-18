"""Pós-processamento da narração dos Shorts (trecho de comum/narracao_curva.py)."""
import json
import os
import tempfile
import wave
from pathlib import Path

import numpy as np

LIMIAR_SILENCIO_DB = -40.0   # quadro de 10 ms abaixo disso (dBFS) é silêncio
GAP_MICROCORTE = 0.07        # segundos de silêncio que ficam entre as falas
CROSSFADE_S = 0.006          # crossfade de 6 ms na emenda


def ler_palavras(wav):
    """Lista de {"word", "start", "end"} (segundos) do <wav>.words.json, ou [] se não tem."""
    p = Path(str(wav) + ".words.json")
    return json.loads(p.read_text("utf-8")) if p.exists() else []


def gravar_palavras(wav, palavras):
    Path(str(wav) + ".words.json").write_text(json.dumps(palavras, ensure_ascii=False), "utf-8")


def _remap_tempo(t, cortes):
    desloc = 0.0
    for c0, c1 in cortes:
        if t <= c0:
            return t - desloc
        if t < c1:
            return c0 - desloc
        desloc += c1 - c0
    return t - desloc


def microcortes(wav, gap_s=None):
    """Encurta silêncios maiores que gap_s para gap_s no .wav (16 bits, mono/estéreo) no lugar.

    Mantém as pontas originais de cada pausa com crossfade de 6 ms na emenda, sem alterar a fala.
    Atualiza <wav>.words.json se existir. Devolve (dur_antes, dur_depois) em segundos, ou None
    quando não há nada a cortar (arquivo intocado).
    """
    if gap_s is None:
        gap_s = GAP_MICROCORTE
    if gap_s < 0:
        raise ValueError(f"gap_s deve ser >= 0, recebido {gap_s}")

    wav_path = Path(wav)
    with wave.open(str(wav_path), "rb") as wf:
        nchannels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        sr = wf.getframerate()
        nframes = wf.getnframes()
        raw = wf.readframes(nframes)

    if sampwidth != 2:
        raise ValueError(f"Apenas WAV 16 bits é suportado (sampwidth={sampwidth})")
    if nchannels not in (1, 2):
        raise ValueError(f"Apenas mono ou estéreo é suportado (nchannels={nchannels})")

    if nframes == 0:
        return None

    dur_antes = nframes / sr
    samples = np.frombuffer(raw, dtype=np.int16).reshape(-1, nchannels)
    n_samples = samples.shape[0]

    frame_len = max(1, int(round(sr * 0.010)))
    n_full = n_samples // frame_len
    rem_len = n_samples % frame_len

    rms_parts = []
    if n_full > 0:
        full = samples[: n_full * frame_len].reshape(n_full, frame_len, nchannels)
        sq_sum = np.sum(full.astype(np.int64) ** 2, axis=(1, 2))
        rms_parts.append(np.sqrt(sq_sum / (frame_len * nchannels)) / 32768.0)
    if rem_len > 0:
        rem = samples[n_full * frame_len :]
        sq_sum_rem = int(np.sum(rem.astype(np.int64) ** 2))
        rms_parts.append(np.array([np.sqrt(sq_sum_rem / (rem_len * nchannels)) / 32768.0]))

    rms = np.concatenate(rms_parts) if len(rms_parts) > 1 else rms_parts[0]
    db = 20.0 * np.log10(np.maximum(rms, 1e-12))
    is_silent = db < LIMIAR_SILENCIO_DB

    gap_n = int(round(gap_s * sr))
    xfade_n = int(round(CROSSFADE_S * sr))

    # Identifica intervalos contíguos de silêncio em amostras [s0, s1)
    silencios = []
    n_frames_q = len(is_silent)
    i = 0
    while i < n_frames_q:
        if is_silent[i]:
            j = i + 1
            while j < n_frames_q and is_silent[j]:
                j += 1
            s0 = i * frame_len
            s1 = min(j * frame_len, n_samples)
            if s1 - s0 > gap_n:
                silencios.append((s0, s1))
            i = j
        else:
            i += 1

    if not silencios:
        return None

    partes = []
    cortes = []
    cursor = 0

    for s0, s1 in silencios:
        if s0 > cursor:
            partes.append(samples[cursor:s0])

        if gap_n == 0:
            cortes.append((s0 / sr, s1 / sr))
        elif s0 == 0 and s1 < n_samples:
            # Silêncio inicial: preserva os gap_n finais imediatamente antes da fala
            partes.append(samples[s1 - gap_n : s1])
            cortes.append((0.0, (s1 - gap_n) / sr))
        elif s0 > 0 and s1 == n_samples:
            # Silêncio final: preserva os gap_n iniciais imediatamente após a fala
            partes.append(samples[s0 : s0 + gap_n])
            cortes.append(((s0 + gap_n) / sr, s1 / sr))
        elif s0 == 0 and s1 == n_samples:
            # Arquivo inteiro silencioso
            partes.append(samples[:gap_n])
            cortes.append((gap_n / sr, s1 / sr))
        else:
            # Silêncio entre falas: guarda as duas pontas e faz crossfade de 6 ms na emenda
            xf = min(xfade_n, gap_n)
            left_n = (gap_n + xf) // 2
            right_n = (gap_n + xf) - left_n
            left = samples[s0 : s0 + left_n]
            right = samples[s1 - right_n : s1]

            if xf > 0:
                if left_n > xf:
                    partes.append(left[:-xf])
                t = ((np.arange(xf, dtype=np.float64) + 0.5) / xf)[:, None]
                blended = left[-xf:].astype(np.float64) * (1.0 - t) + right[:xf].astype(np.float64) * t
                partes.append(np.clip(np.rint(blended), -32768, 32767).astype(np.int16))
                if right_n > xf:
                    partes.append(right[xf:])
            else:
                partes.append(left)
                partes.append(right)

            cortes.append(((s0 + left_n - xf / 2.0) / sr, (s1 - right_n + xf / 2.0) / sr))

        cursor = s1

    if cursor < n_samples:
        partes.append(samples[cursor:])

    out = np.concatenate(partes, axis=0) if partes else np.empty((0, nchannels), dtype=np.int16)
    dur_depois = out.shape[0] / sr

    fd, tmp_name = tempfile.mkstemp(dir=str(wav_path.parent), suffix=".tmp.wav")
    os.close(fd)
    try:
        with wave.open(tmp_name, "wb") as wf:
            wf.setnchannels(nchannels)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes(out.astype(np.int16, copy=False).tobytes())
        os.replace(tmp_name, str(wav_path))
    except Exception:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
        raise

    words_path = Path(str(wav_path) + ".words.json")
    if words_path.exists():
        palavras = ler_palavras(wav_path)
        atualizadas = []
        for w in palavras:
            novo = dict(w)
            if "start" in novo:
                novo["start"] = round(max(0.0, min(dur_depois, _remap_tempo(float(novo["start"]), cortes))), 4)
            if "end" in novo:
                novo["end"] = round(max(0.0, min(dur_depois, _remap_tempo(float(novo["end"]), cortes))), 4)
            atualizadas.append(novo)
        gravar_palavras(wav_path, atualizadas)

    return (dur_antes, dur_depois)
