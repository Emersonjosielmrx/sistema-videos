"""Pós-processamento da narração dos Shorts (trecho de comum/narracao_curva.py)."""
import json
import os
from pathlib import Path
import wave
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
    """
    Remove silêncios excessivos maiores que gap_s (padrão GAP_MICROCORTE),
    aplicando crossfade nas emendas e atualizando o arquivo .words.json correspondente.
    Retorna (duração_antes, duração_depois) em segundos, ou None se nada foi alterado.
    """
    if gap_s is None:
        gap_s = GAP_MICROCORTE

    wav_path = Path(wav)
    if not wav_path.exists():
        return None

    with wave.open(str(wav_path), 'rb') as wf:
        nchannels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        nframes = wf.getnframes()
        frames = wf.readframes(nframes)

    if sampwidth != 2:
        # Suporta apenas PCM de 16-bit
        return None

    duration_before = nframes / float(framerate)
    audio_data = np.frombuffer(frames, dtype=np.int16)
    if nchannels > 1:
        audio_data = audio_data.reshape((-1, nchannels))

    # Análise em blocos de 10 ms
    block_size = int(framerate * 0.01)
    if block_size < 1:
        block_size = 1

    total_len = len(audio_data)
    num_blocks = (total_len + block_size - 1) // block_size

    # Prepara array para blocos
    block_dbs = []
    for i in range(num_blocks):
        start_idx = i * block_size
        end_idx = min((i + 1) * block_size, total_len)
        block = audio_data[start_idx:end_idx]
        if len(block) == 0:
            block_dbs.append(LIMIAR_SILENCIO_DB - 1)
            continue

        # Calcula RMS
        rms = np.sqrt(np.mean(block.astype(np.float32) ** 2))

        if rms < 1e-5:
            db = -100.0
        else:
            db = 20 * np.log10(rms / 32768.0)
        block_dbs.append(db)

    # Identifica blocos de silêncio vs fala
    is_silence = [db < LIMIAR_SILENCIO_DB for db in block_dbs]

    # Agrupa blocos consecutivos em regiões (fala ou silêncio)
    regions = []
    if num_blocks > 0:
        curr_type = 'silence' if is_silence[0] else 'speech'
        curr_start = 0
        for i in range(1, num_blocks):
            t = 'silence' if is_silence[i] else 'speech'
            if t != curr_type:
                regions.append((curr_type, curr_start, i))
                curr_type = t
                curr_start = i
        regions.append((curr_type, curr_start, num_blocks))

    # Determina o gap máximo em número de blocos
    gap_blocks = int(round(gap_s / 0.01))
    if gap_blocks < 0:
        gap_blocks = 0

    # Processa cada região
    processed_regions = []
    for r_type, r_start, r_end in regions:
        length = r_end - r_start
        if r_type == 'silence' and length > gap_blocks:
            # Corta o silêncio para gap_blocks
            processed_regions.append(('silence', r_start, r_start + gap_blocks))
        else:
            processed_regions.append((r_type, r_start, r_end))

    # Verifica se houve alguma alteração real
    changed = False
    for (t1, s1, e1), (t2, s2, e2) in zip(regions, processed_regions):
        if (e1 - s1) != (e2 - s2):
            changed = True
            break

    if not changed:
        return None

    # Reconstrói o áudio com crossfade de 6ms nas junções
    crossfade_samples = int(framerate * 0.006)
    if crossfade_samples < 1:
        crossfade_samples = 1

    # Constroi os segmentos finais
    final_blocks = []
    for r_type, r_start, r_end in processed_regions:
        s_sample = r_start * block_size
        e_sample = min(r_end * block_size, total_len)
        final_blocks.append((s_sample, e_sample))

    accumulated_audio_parts = []
    current_pos_samples = 0
    mapping_spans = []

    for idx, (s_samp, e_samp) in enumerate(final_blocks):
        chunk = audio_data[s_samp:e_samp].copy()
        chunk_len = len(chunk)
        if chunk_len == 0:
            continue

        orig_start_sec = s_samp / float(framerate)
        orig_end_sec = e_samp / float(framerate)

        # Aplica crossfade com o chunk anterior se não for o primeiro
        if len(accumulated_audio_parts) > 0 and crossfade_samples > 0:
            cf_len = min(crossfade_samples, len(chunk), len(accumulated_audio_parts[-1]))
            if cf_len > 0:
                prev_chunk = accumulated_audio_parts[-1]
                fade_out = np.linspace(1.0, 0.0, cf_len, dtype=np.float32)
                fade_in = np.linspace(0.0, 1.0, cf_len, dtype=np.float32)

                if nchannels > 1:
                    fade_out = fade_out[:, np.newaxis]
                    fade_in = fade_in[:, np.newaxis]

                # Mix crossfade
                mixed = (prev_chunk[-cf_len:].astype(np.float32) * fade_out +
                        chunk[:cf_len].astype(np.float32) * fade_in).astype(np.int16)
                prev_chunk[-cf_len:] = mixed
                chunk[:cf_len] = mixed

        new_start_sec = current_pos_samples / float(framerate)
        new_end_sec = (current_pos_samples + chunk_len) / float(framerate)

        mapping_spans.append({
            'orig_start': orig_start_sec,
            'orig_end': orig_end_sec,
            'new_start': new_start_sec,
            'new_end': new_end_sec
        })

        accumulated_audio_parts.append(chunk)
        current_pos_samples += chunk_len

    if not accumulated_audio_parts:
        return None

    final_audio = np.concatenate(accumulated_audio_parts)
    duration_after = len(final_audio) / float(framerate)

    # Salva o arquivo de áudio modificado (no lugar)
    with wave.open(str(wav_path), 'wb') as wf:
        wf.setnchannels(nchannels)
        wf.setsampwidth(sampwidth)
        wf.setframerate(framerate)
        wf.writeframes(final_audio.tobytes())

    # Atualiza o arquivo <wav>.words.json se existir
    palavras = ler_palavras(wav_path)
    if palavras and mapping_spans:
        updated_palavras = []
        for w in palavras:
            w_start = w.get('start', 0)
            w_end = w.get('end', 0)

            # Mapeia start e end
            new_w_start = None
            new_w_end = None

            for span in mapping_spans:
                if span['orig_start'] <= w_start <= span['orig_end']:
                    span_orig_dur = span['orig_end'] - span['orig_start']
                    if span_orig_dur > 0:
                        ratio = (w_start - span['orig_start']) / span_orig_dur
                        new_w_start = span['new_start'] + ratio * (span['new_end'] - span['new_start'])
                    else:
                        new_w_start = span['new_start']

                if span['orig_start'] <= w_end <= span['orig_end']:
                    span_orig_dur = span['orig_end'] - span['orig_start']
                    if span_orig_dur > 0:
                        ratio = (w_end - span['orig_start']) / span_orig_dur
                        new_w_end = span['new_start'] + ratio * (span['new_end'] - span['new_start'])
                    else:
                        new_w_end = span['new_end']

            # Se a palavra estiver em trecho cortado, ajusta para o span mais próximo
            if new_w_start is None:
                closest = min(mapping_spans, key=lambda sp: min(abs(sp['orig_start'] - w_start), abs(sp['orig_end'] - w_start)))
                if w_start < closest['orig_start']:
                    diff = w_start - closest['orig_start']
                    new_w_start = closest['new_start'] + diff
                else:
                    diff = w_start - closest['orig_end']
                    new_w_start = closest['new_end'] + diff

            if new_w_end is None:
                closest = min(mapping_spans, key=lambda sp: min(abs(sp['orig_start'] - w_end), abs(sp['orig_end'] - w_end)))
                if w_end < closest['orig_start']:
                    diff = w_end - closest['orig_start']
                    new_w_end = closest['new_start'] + diff
                else:
                    diff = w_end - closest['orig_end']
                    new_w_end = closest['new_end'] + diff

            # Garante consistência
            if new_w_start < 0:
                new_w_start = 0.0
            if new_w_end < new_w_start:
                new_w_end = new_w_start + 0.05

            w_copy = dict(w)
            w_copy['start'] = round(new_w_start, 3)
            w_copy['end'] = round(new_w_end, 3)
            updated_palavras.append(w_copy)

        gravar_palavras(wav_path, updated_palavras)

    return (round(duration_before, 3), round(duration_after, 3))
