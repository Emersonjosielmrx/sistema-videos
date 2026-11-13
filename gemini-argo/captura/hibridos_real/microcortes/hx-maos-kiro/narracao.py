"""Pós-processamento da narração dos Shorts (trecho de comum/narracao_curva.py)."""
import json
import os
from pathlib import Path
import numpy as np
import wave

LIMIAR_SILENCIO_DB = -40.0   # quadro de 10 ms abaixo disso (dBFS) é silêncio
GAP_MICROCORTE = 0.07        # segundos de silêncio que ficam entre as falas


def ler_palavras(wav):
    """Lista de {"word", "start", "end"} (segundos) do <wav>.words.json, ou [] se não tem."""
    p = Path(str(wav) + ".words.json")
    return json.loads(p.read_text("utf-8")) if p.exists() else []


def gravar_palavras(wav, palavras):
    Path(str(wav) + ".words.json").write_text(json.dumps(palavras, ensure_ascii=False), "utf-8")


def microcortes(wav, gap_s=None):
    """
    Remove silêncios maiores que gap_s (padrão GAP_MICROCORTE) no arquivo wav in-place.
    Aplica crossfade de 6 ms na emenda. Atualiza <wav>.words.json se existir.
    Devolve (duração antes, duração depois) em segundos, ou None se nada foi cortado.
    """
    if gap_s is None:
        gap_s = GAP_MICROCORTE

    wav_path = Path(wav)
    if not wav_path.exists():
        return None

    # Ler o arquivo WAV
    with wave.open(str(wav_path), 'rb') as wf:
        nchannels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        nframes = wf.getnframes()
        comptype = wf.getcomptype()
        compname = wf.getcompname()
        frames_bytes = wf.readframes(nframes)

    # Só processa 16 bits
    if sampwidth != 2:
        return None

    duration_before = nframes / float(framerate)

    # Converter para numpy array
    audio = np.frombuffer(frames_bytes, dtype=np.int16)

    if nchannels > 1:
        audio_reshaped = audio.reshape((-1, nchannels))
    else:
        audio_reshaped = audio.reshape((-1, 1))

    # Detectar silêncios (quadros de 10 ms)
    frame_samples = int(framerate * 0.01)
    if frame_samples < 1:
        frame_samples = 1

    limiar_rms = 32768.0 * (10.0 ** (LIMIAR_SILENCIO_DB / 20.0))
    n_total_samples = audio_reshaped.shape[0]

    # Encontrar blocos de silêncio
    silence_blocks = []
    i = 0
    while i < n_total_samples:
        end_i = min(i + frame_samples, n_total_samples)
        block = audio_reshaped[i:end_i]
        rms = np.sqrt(np.mean(block.astype(np.float64) ** 2))

        if rms < limiar_rms:
            # Início de silêncio
            s_start = i
            s_end = end_i
            i = end_i

            # Continuar enquanto for silêncio
            while i < n_total_samples:
                next_end = min(i + frame_samples, n_total_samples)
                next_block = audio_reshaped[i:next_end]
                next_rms = np.sqrt(np.mean(next_block.astype(np.float64) ** 2))
                if next_rms < limiar_rms:
                    s_end = next_end
                    i = next_end
                else:
                    break

            silence_blocks.append((s_start, s_end))
        else:
            i = end_i

    if not silence_blocks:
        return None

    # Processar cortes
    gap_samp = int(round(gap_s * framerate))
    crossfade_samp = int(round(0.006 * framerate))

    kept_segments = []
    last_pos = 0
    word_shifts = []  # (posição_corte_em_samples, quantidade_removida)
    total_removed = 0

    for s_start, s_end in silence_blocks:
        s_len = s_end - s_start

        if s_len > gap_samp:
            # Guardar pontas do silêncio original
            keep_start = gap_samp // 2
            keep_end = gap_samp - keep_start

            # Cortar o meio
            cut_start = s_start + keep_start
            cut_end = s_end - keep_end
            remove_len = cut_end - cut_start

            if cut_start > last_pos:
                kept_segments.append(audio_reshaped[last_pos:cut_start])

            last_pos = cut_end
            word_shifts.append((cut_start, remove_len))
            total_removed += remove_len

    if total_removed == 0:
        return None

    # Adicionar último segmento
    if last_pos < n_total_samples:
        kept_segments.append(audio_reshaped[last_pos:n_total_samples])

    if not kept_segments:
        return None

    # Aplicar crossfade de 6 ms nas emendas
    if crossfade_samp > 0 and len(kept_segments) > 1:
        final_parts = [kept_segments[0]]

        for seg in kept_segments[1:]:
            prev = final_parts[-1]
            cf = min(crossfade_samp, len(prev), len(seg))

            if cf > 0:
                # Fade out no final do segmento anterior
                # Fade in no início do segmento atual
                fade_out = np.linspace(1.0, 0.0, cf).reshape(-1, 1)
                fade_in = np.linspace(0.0, 1.0, cf).reshape(-1, 1)

                blended = prev[-cf:] * fade_out + seg[:cf] * fade_in

                # Remover a parte que será blended e adicionar o blend
                final_parts[-1] = prev[:-cf]
                final_parts.append(blended)
                final_parts.append(seg[cf:])
            else:
                final_parts.append(seg)

        final_audio = np.concatenate(final_parts, axis=0)
    else:
        final_audio = np.concatenate(kept_segments, axis=0)

    final_nframes = final_audio.shape[0]
    duration_after = final_nframes / float(framerate)

    # Gravar arquivo WAV in-place
    with wave.open(str(wav_path), 'wb') as wf:
        wf.setnchannels(nchannels)
        wf.setsampwidth(sampwidth)
        wf.setframerate(framerate)
        wf.setnframes(final_nframes)
        wf.setcomptype(comptype, compname)
        wf.writeframes(final_audio.astype(np.int16).tobytes())

    # Atualizar words.json se existir
    palavras = ler_palavras(wav_path)
    if palavras and word_shifts:
        for w in palavras:
            w_start_samp = int(w["start"] * framerate)
            w_end_samp = int(w["end"] * framerate)

            # Calcular quanto deslocar baseado nos cortes antes desta palavra
            total_shift_samples = 0
            for cut_samp, remove_len in word_shifts:
                if w_start_samp >= cut_samp:
                    total_shift_samples += remove_len

            if total_shift_samples > 0:
                w["start"] = max(0.0, (w_start_samp - total_shift_samples) / float(framerate))
                w["end"] = max(w["start"], (w_end_samp - total_shift_samples) / float(framerate))

        gravar_palavras(wav_path, palavras)

    return (duration_before, duration_after)
