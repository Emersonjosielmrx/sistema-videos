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
    """Corta silêncios maiores que gap_s deixando gap_s (pontas originais + crossfade de 6 ms).

    Mexe no .wav no lugar (16 bits, mono ou estéreo) e atualiza <wav>.words.json se existir.
    Devolve (dur_antes, dur_depois) em segundos, ou None se nada foi cortado.
    """
    if gap_s is None:
        gap_s = GAP_MICROCORTE

    wav_path = str(wav)
    with wave.open(wav_path, "rb") as wf:
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        n_frames = wf.getnframes()
        raw_bytes = wf.readframes(n_frames)

    if sampwidth != 2 or n_frames == 0:
        return None

    audio = np.frombuffer(raw_bytes, dtype=np.int16).reshape(-1, n_channels)
    dur_antes = n_frames / float(framerate)

    frame_len = max(1, int(round(framerate * 0.010)))  # quadros de 10 ms
    n_quadros = n_frames // frame_len
    if n_quadros == 0:
        return None

    limiar_amp = 32768.0 * (10.0 ** (LIMIAR_SILENCIO_DB / 20.0))

    quadros = audio[: n_quadros * frame_len].reshape(n_quadros, frame_len, n_channels).astype(np.float64)
    rms_por_quadro = np.sqrt(np.mean(quadros ** 2, axis=(1, 2)))
    silencio = rms_por_quadro < limiar_amp

    # Se houver sobra no final, verifica também
    sobra = n_frames - n_quadros * frame_len
    if sobra > 0:
        resto = audio[n_quadros * frame_len :].astype(np.float64)
        rms_resto = np.sqrt(np.mean(resto ** 2))
        silencio = np.append(silencio, rms_resto < limiar_amp)

    gap_samples = int(round(gap_s * framerate))
    xfade_samples = int(round(0.006 * framerate))
    # Garantir que o crossfade caiba dentro do gap guardado
    xfade_samples = min(xfade_samples, gap_samples)

    # Identificar trechos contínuos de silêncio em amostras
    cortes = []  # lista de (inicio_sample, fim_sample) do silêncio original que será encurtado
    i = 0
    total_q = len(silencio)
    while i < total_q:
        if silencio[i]:
            j = i
            while j < total_q and silencio[j]:
                j += 1
            s_ini = i * frame_len
            s_fim = min(n_frames, j * frame_len)
            if (s_fim - s_ini) > gap_samples:
                cortes.append((s_ini, s_fim))
            i = j
        else:
            i += 1

    if not cortes:
        return None

    # Montar novo áudio mantendo as pontas do silêncio original e aplicando crossfade de 6 ms na emenda
    # Para que o silêncio resultante tenha exatamente gap_samples após o crossfade de xfade_samples:
    # ponta_esq + ponta_dir - xfade_samples = gap_samples  =>  ponta_esq + ponta_dir = gap_samples + xfade_samples
    total_pontas = gap_samples + xfade_samples
    ponta_esq = total_pontas // 2
    ponta_dir = total_pontas - ponta_esq

    partes = []
    cursor = 0
    for s_ini, s_fim in cortes:
        # Se por acaso o silêncio for menor que total_pontas (ex: entre gap_samples e gap_samples + xfade_samples),
        # ajustamos o crossfade para caber no trecho disponível
        disp = s_fim - s_ini
        xf = min(xfade_samples, disp - gap_samples)
        tot_p = gap_samples + xf
        p_esq = tot_p // 2
        p_dir = tot_p - p_esq

        # Trecho de fala/áudio antes da emenda + ponta esquerda do silêncio (sem a zona de crossfade)
        partes.append(audio[cursor : s_ini + p_esq - xf])

        if xf > 0:
            fade_out = np.linspace(1.0, 0.0, xf, endpoint=True)[:, None]
            fade_in = 1.0 - fade_out
            trecho_esq = audio[s_ini + p_esq - xf : s_ini + p_esq].astype(np.float64)
            trecho_dir = audio[s_fim - p_dir : s_fim - p_dir + xf].astype(np.float64)
            emenda = np.round(trecho_esq * fade_out + trecho_dir * fade_in).clip(-32768, 32767).astype(np.int16)
            partes.append(emenda)

        # O cursor avança para depois da zona de crossfade da ponta direita
        cursor = s_fim - p_dir + xf

    partes.append(audio[cursor:])
    novo_audio = np.concatenate(partes, axis=0)

    with wave.open(wav_path, "wb") as wf:
        wf.setnchannels(n_channels)
        wf.setsampwidth(sampwidth)
        wf.setframerate(framerate)
        wf.writeframes(novo_audio.tobytes())

    dur_depois = len(novo_audio) / float(framerate)

    # Atualizar <wav>.words.json se existir
    words_path = Path(str(wav) + ".words.json")
    if words_path.exists():
        palavras = ler_palavras(wav)
        cortes_s = [(s_ini / float(framerate), s_fim / float(framerate), (s_fim - s_ini - gap_samples) / float(framerate)) for s_ini, s_fim in cortes]

        def ajustar_tempo(t):
            desconto = 0.0
            for c_ini, c_fim, remov in cortes_s:
                if t <= c_ini:
                    break
                elif t >= c_fim:
                    desconto += remov
                else:
                    # Dentro do silêncio cortado: mapeia proporcionalmente para o gap restante
                    frac = (t - c_ini) / (c_fim - c_ini)
                    desconto += frac * remov
                    break
            return round(max(0.0, t - desconto), 4)

        for w in palavras:
            if "start" in w:
                w["start"] = ajustar_tempo(w["start"])
            if "end" in w:
                w["end"] = ajustar_tempo(w["end"])
        gravar_palavras(wav, palavras)

    return (dur_antes, dur_depois)
