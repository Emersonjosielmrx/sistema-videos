"""Pós-processamento da narração dos Shorts (trecho de comum/narracao_curva.py)."""
import json
import os
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
    """Corta silêncios maiores que gap_s para gap_s (in-place), mantendo pontas e crossfade de 6 ms."""
    if gap_s is None:
        gap_s = GAP_MICROCORTE
    wav_path = Path(wav)

    with wave.open(str(wav_path), "rb") as wf:
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        n_frames = wf.getnframes()
        raw = wf.readframes(n_frames)

    if sampwidth != 2 or n_frames == 0:
        return None

    dur_antes = n_frames / float(framerate)
    samples = np.frombuffer(raw, dtype=np.int16).reshape(-1, n_channels)

    # Quadros de 10 ms para detecção de silêncio
    frame_len = max(1, int(round(framerate * 0.010)))
    limiar_linear = 32768.0 * (10.0 ** (LIMIAR_SILENCIO_DB / 20.0))

    n_quadros = int(np.ceil(n_frames / frame_len))
    silencio = np.zeros(n_quadros, dtype=bool)
    for i in range(n_quadros):
        ini = i * frame_len
        fim = min(n_frames, ini + frame_len)
        bloco = samples[ini:fim].astype(np.float64)
        rms = np.sqrt(np.mean(bloco ** 2))
        silencio[i] = rms < limiar_linear

    gap_samples = int(round(gap_s * framerate))
    xfade_samples = min(int(round(0.006 * framerate)), gap_samples)

    # Identifica corridas contíguas de quadros silenciosos maiores que gap_s
    cortes = []  # lista de (inicio_sample, fim_sample) do silêncio original
    i = 0
    while i < n_quadros:
        if silencio[i]:
            j = i
            while j < n_quadros and silencio[j]:
                j += 1
            ini_s = i * frame_len
            fim_s = min(n_frames, j * frame_len)
            if (fim_s - ini_s) > gap_samples:
                cortes.append((ini_s, fim_s))
            i = j
        else:
            i += 1

    if not cortes:
        return None

    # Monta novo áudio mantendo fala intacta e encurtando cada silêncio longo para gap_samples
    # Guarda o som original das pontas do silêncio e faz crossfade de 6 ms na emenda central
    partes = []
    cursor = 0
    half_keep = (gap_samples + xfade_samples) // 2
    other_keep = (gap_samples + xfade_samples) - half_keep

    # Registro dos cortes em segundos: (ini_corte_s, fim_corte_s, dur_final_s)
    ajustes_tempo = []

    for ini_s, fim_s in cortes:
        if ini_s > cursor:
            partes.append(samples[cursor:ini_s])

        if gap_samples == 0:
            trecho_sil = samples[0:0]
        elif xfade_samples > 0 and (fim_s - ini_s) >= (half_keep + other_keep):
            ponta_esq = samples[ini_s : ini_s + half_keep].astype(np.float64)
            ponta_dir = samples[fim_s - other_keep : fim_s].astype(np.float64)

            pre = ponta_esq[: half_keep - xfade_samples]
            pos = ponta_dir[xfade_samples:]

            fade_out = np.linspace(1.0, 0.0, xfade_samples, endpoint=False)[:, None]
            fade_in = 1.0 - fade_out
            meio = ponta_esq[half_keep - xfade_samples :] * fade_out + ponta_dir[:xfade_samples] * fade_in

            trecho_sil = np.vstack([pre, meio, pos])
            trecho_sil = np.clip(np.round(trecho_sil), -32768, 32767).astype(np.int16)
        else:
            meio_esq = gap_samples // 2
            meio_dir = gap_samples - meio_esq
            trecho_sil = np.vstack([samples[ini_s : ini_s + meio_esq], samples[fim_s - meio_dir : fim_s]])

        partes.append(trecho_sil)
        ajustes_tempo.append((
            ini_s / float(framerate),
            fim_s / float(framerate),
            len(trecho_sil) / float(framerate),
        ))
        cursor = fim_s

    if cursor < n_frames:
        partes.append(samples[cursor:n_frames])

    novo_samples = np.vstack(partes) if partes else samples[0:0]
    dur_depois = len(novo_samples) / float(framerate)

    with wave.open(str(wav_path), "wb") as wf:
        wf.setnchannels(n_channels)
        wf.setsampwidth(sampwidth)
        wf.setframerate(framerate)
        wf.writeframes(novo_samples.tobytes())

    # Atualiza <wav>.words.json se existir
    palavras = ler_palavras(wav_path)
    if palavras:
        def mapear_tempo(t):
            deslocamento = 0.0
            for ini_t, fim_t, novo_dur in ajustes_tempo:
                if t <= ini_t:
                    break
                elif t >= fim_t:
                    deslocamento += (fim_t - ini_t) - novo_dur
                else:
                    # Caso um timestamp caia dentro do silêncio cortado, mapeia proporcionalmente
                    frac = (t - ini_t) / (fim_t - ini_t) if fim_t > ini_t else 0.0
                    return max(0.0, round((ini_t - deslocamento) + frac * novo_dur, 4))
            return max(0.0, round(t - deslocamento, 4))

        for w in palavras:
            if "start" in w:
                w["start"] = mapear_tempo(float(w["start"]))
            if "end" in w:
                w["end"] = mapear_tempo(float(w["end"]))
        gravar_palavras(wav_path, palavras)

    return (dur_antes, dur_depois)
