"""Pós-processamento da narração dos Shorts (trecho de comum/narracao_curva.py)."""
import json
import os
import wave
from pathlib import Path
import numpy as np

LIMIAR_SILENCIO_DB = -40.0   # quadro de 10 ms abaixo disso (dBFS) é silêncio
GAP_MICROCORTE = 0.07        # segundos de silêncio que ficam entre as falas
CROSSFADE_MS = 6             # duração do crossfade nas emendas (ms)


def ler_palavras(wav):
    """Lista de {"word", "start", "end"} (segundos) do <wav>.words.json, ou [] se não tem."""
    p = Path(str(wav) + ".words.json")
    return json.loads(p.read_text("utf-8")) if p.exists() else []


def gravar_palavras(wav, palavras):
    Path(str(wav) + ".words.json").write_text(json.dumps(palavras, ensure_ascii=False), "utf-8")


def microcortes(wav, gap_s=None):
    """
    Corta pausas longas no áudio, substituindo por gap_s segundos de silêncio.

    Remove silêncios maiores que gap_s, mantendo as bordas originais e aplicando
    crossfade de 6ms nas emendas. A fala não é acelerada nem modificada.

    Args:
        wav: caminho do arquivo .wav (16 bits, mono ou estéreo)
        gap_s: duração máxima do gap em segundos (padrão: GAP_MICROCORTE = 0.07s)

    Returns:
        (duração_antes, duração_depois) em segundos, ou None se não há nada a cortar
    """
    if gap_s is None:
        gap_s = GAP_MICROCORTE

    wav_path = Path(wav)

    # Ler o arquivo WAV
    with wave.open(str(wav_path), 'rb') as wf:
        nchannels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        nframes = wf.getnframes()
        audio_bytes = wf.readframes(nframes)

    # Verificar formato (16 bits)
    if sampwidth != 2:
        raise ValueError(f"Esperado 16 bits (sampwidth=2), encontrado sampwidth={sampwidth}")

    # Converter para numpy array
    dtype = np.int16
    audio = np.frombuffer(audio_bytes, dtype=dtype)

    # Reshape para (nframes, nchannels) se estéreo
    if nchannels > 1:
        audio = audio.reshape(-1, nchannels)

    duracao_antes = nframes / framerate

    # Tamanho do quadro de análise: 10 ms
    frame_size = int(0.010 * framerate)
    gap_frames = int(gap_s * framerate)
    crossfade_frames = int(CROSSFADE_MS * 0.001 * framerate)

    # Detectar regiões de silêncio
    # Calcular RMS por quadro de 10ms e converter para dBFS
    n_analysis_frames = len(audio) // frame_size
    silence_mask = np.zeros(n_analysis_frames, dtype=bool)

    for i in range(n_analysis_frames):
        start_sample = i * frame_size
        end_sample = start_sample + frame_size
        frame = audio[start_sample:end_sample]

        # Calcular RMS (considerando todos os canais)
        if nchannels > 1:
            rms = np.sqrt(np.mean(frame.astype(np.float64) ** 2))
        else:
            rms = np.sqrt(np.mean(frame.astype(np.float64) ** 2))

        # Converter para dBFS (referência: 32768 para int16)
        if rms > 0:
            db = 20 * np.log10(rms / 32768.0)
        else:
            db = -100.0  # silêncio absoluto

        silence_mask[i] = db < LIMIAR_SILENCIO_DB

    # Encontrar regiões contíguas de silêncio
    silent_regions = []
    in_silence = False
    start_idx = 0

    for i, is_silent in enumerate(silence_mask):
        if is_silent and not in_silence:
            start_idx = i
            in_silence = True
        elif not is_silent and in_silence:
            silent_regions.append((start_idx, i))
            in_silence = False

    if in_silence:
        silent_regions.append((start_idx, len(silence_mask)))

    # Filtrar apenas regiões maiores que gap_s
    regions_to_cut = []
    for start_frame_idx, end_frame_idx in silent_regions:
        silence_duration_frames = (end_frame_idx - start_frame_idx) * frame_size
        if silence_duration_frames > gap_frames:
            start_sample = start_frame_idx * frame_size
            end_sample = end_frame_idx * frame_size
            regions_to_cut.append((start_sample, end_sample, silence_duration_frames))

    # Se não há nada a cortar, retornar None
    if not regions_to_cut:
        return None

    # Construir novo áudio cortando as regiões e mantendo bordas com crossfade
    new_segments = []
    current_pos = 0
    total_cut = 0

    for start_sample, end_sample, silence_duration_frames in regions_to_cut:
        # Adicionar áudio antes da região de silêncio
        if current_pos < start_sample:
            new_segments.append(audio[current_pos:start_sample])

        # Manter início e fim da região de silêncio com crossfade
        edge_frames = min(crossfade_frames, gap_frames // 2)

        # Extrair bordas do silêncio original
        silence_start = audio[start_sample:start_sample + edge_frames]
        silence_end = audio[max(start_sample + edge_frames, end_sample - edge_frames):end_sample]

        # Criar gap de duração gap_frames
        if nchannels > 1:
            gap_silence = np.zeros((gap_frames, nchannels), dtype=dtype)
        else:
            gap_silence = np.zeros(gap_frames, dtype=dtype)

        # Aplicar crossfade nas bordas
        fade_in = np.linspace(0, 1, len(silence_start))
        fade_out = np.linspace(1, 0, len(silence_end))

        if nchannels > 1:
            fade_in = fade_in[:, np.newaxis]
            fade_out = fade_out[:, np.newaxis]

        # Posicionar as bordas no gap
        gap_start_pos = 0
        gap_end_pos = max(0, gap_frames - len(silence_end))

        if len(silence_start) > 0 and gap_start_pos < len(gap_silence):
            end_pos = min(gap_start_pos + len(silence_start), len(gap_silence))
            actual_len = end_pos - gap_start_pos
            gap_silence[gap_start_pos:end_pos] = (silence_start[:actual_len] * fade_in[:actual_len]).astype(dtype)

        if len(silence_end) > 0 and gap_end_pos < len(gap_silence):
            end_pos = min(gap_end_pos + len(silence_end), len(gap_silence))
            actual_len = end_pos - gap_end_pos
            gap_silence[gap_end_pos:end_pos] = (silence_end[:actual_len] * fade_out[:actual_len]).astype(dtype)

        new_segments.append(gap_silence)

        current_pos = end_sample
        total_cut += (end_sample - start_sample) - gap_frames

    # Adicionar áudio restante
    if current_pos < len(audio):
        new_segments.append(audio[current_pos:])

    # Concatenar todos os segmentos
    if nchannels > 1:
        new_audio = np.vstack(new_segments)
    else:
        new_audio = np.concatenate(new_segments)

    duracao_depois = len(new_audio) / framerate

    # Gravar o arquivo modificado
    with wave.open(str(wav_path), 'wb') as wf:
        wf.setnchannels(nchannels)
        wf.setsampwidth(sampwidth)
        wf.setframerate(framerate)
        wf.writeframes(new_audio.tobytes())

    # Atualizar o arquivo .words.json se existir
    palavras = ler_palavras(wav)
    if palavras:
        # Calcular mapeamento de tempo (antes -> depois)
        time_map = {}
        old_time = 0.0
        new_time = 0.0
        current_pos = 0

        for start_sample, end_sample, _ in regions_to_cut:
            # Tempo antes da região cortada
            segment_duration = (start_sample - current_pos) / framerate
            for t in np.arange(old_time, old_time + segment_duration, 0.001):
                time_map[t] = new_time + (t - old_time)

            old_time += segment_duration
            new_time += segment_duration

            # Região cortada
            old_silence_duration = (end_sample - start_sample) / framerate
            new_silence_duration = gap_s

            # Mapear linearmente dentro da região cortada
            if old_silence_duration > 0:
                for t in np.arange(old_time, old_time + old_silence_duration, 0.001):
                    progress = (t - old_time) / old_silence_duration
                    time_map[t] = new_time + progress * new_silence_duration

            old_time += old_silence_duration
            new_time += new_silence_duration
            current_pos = end_sample

        # Tempo restante
        remaining_duration = (len(audio) - current_pos) / framerate
        for t in np.arange(old_time, old_time + remaining_duration, 0.001):
            time_map[t] = new_time + (t - old_time)

        # Função para mapear tempo
        def map_time(t):
            # Encontrar mapeamento mais próximo
            if t in time_map:
                return time_map[t]
            keys = np.array(list(time_map.keys()))
            if len(keys) == 0:
                return t * duracao_depois / duracao_antes
            idx = np.searchsorted(keys, t)
            if idx == 0:
                return time_map[keys[0]] * (t / keys[0]) if keys[0] > 0 else 0
            if idx >= len(keys):
                return time_map[keys[-1]] + (t - keys[-1]) * (duracao_depois - time_map[keys[-1]]) / (duracao_antes - keys[-1])
            # Interpolação linear
            t0, t1 = keys[idx - 1], keys[idx]
            new_t0, new_t1 = time_map[t0], time_map[t1]
            return new_t0 + (new_t1 - new_t0) * (t - t0) / (t1 - t0)

        # Atualizar timestamps das palavras
        palavras_ajustadas = []
        for palavra in palavras:
            palavras_ajustadas.append({
                "word": palavra["word"],
                "start": map_time(palavra["start"]),
                "end": map_time(palavra["end"])
            })

        gravar_palavras(wav, palavras_ajustadas)

    return (duracao_antes, duracao_depois)
