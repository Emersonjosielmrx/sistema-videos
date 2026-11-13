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
    """Mexe no .wav no lugar (16 bits, mono ou estéreo).

    Todo silêncio maior que gap_s (padrão GAP_MICROCORTE, 0.07 s; silêncio = quadros de 10 ms abaixo
    de LIMIAR_SILENCIO_DB) fica com gap_s, guardando o som original das pontas e com crossfade de
    6 ms na emenda. A fala não acelera nem muda. O <wav>.words.json (se existir) acompanha os cortes.

    Devolve (duração antes, duração depois) em segundos, ou None quando não há nada a cortar (arquivo intocado).
    """
    if gap_s is None:
        gap_s = float(os.environ.get("NARRACAO_GAP_MICROCORTE") or GAP_MICROCORTE)
    else:
        gap_s = max(0.0, float(gap_s))

    wav_path = Path(wav)
    with wave.open(str(wav_path), "rb") as wf:
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

    # Se houver sobra no final, avalia também
    sobra = n_frames - n_quadros * frame_len
    if sobra > 0:
        resto = audio[n_quadros * frame_len :].astype(np.float64)
        rms_resto = np.sqrt(np.mean(resto ** 2))
        silencio = np.append(silencio, rms_resto < limiar_amp)

    gap_samples = int(round(gap_s * framerate))
    xfade_samples = int(round(0.006 * framerate))
    xfade_samples = min(xfade_samples, gap_samples)

    # Identifica trechos contínuos de silêncio que superam gap_s
    cortes = []
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

    # Monta novo áudio guardando as pontas originais com crossfade de 6 ms na emenda central
    partes = []
    cursor = 0
    for s_ini, s_fim in cortes:
        disp = s_fim - s_ini
        xf = min(xfade_samples, disp - gap_samples)
        tot_p = gap_samples + xf
        p_esq = tot_p // 2
        p_dir = tot_p - p_esq

        # Fala antes do corte + ponta esquerda do silêncio intacta (antes da zona de crossfade)
        partes.append(audio[cursor : s_ini + p_esq - xf])

        if xf > 0:
            fade_out = np.linspace(1.0, 0.0, xf, endpoint=False)[:, None]
            fade_in = 1.0 - fade_out
            trecho_esq = audio[s_ini + p_esq - xf : s_ini + p_esq].astype(np.float64)
            trecho_dir = audio[s_fim - p_dir : s_fim - p_dir + xf].astype(np.float64)
            emenda = np.round(trecho_esq * fade_out + trecho_dir * fade_in).clip(-32768, 32767).astype(np.int16)
            partes.append(emenda)

        # O cursor fica no ponto onde termina o crossfade na ponta direita
        cursor = s_fim - p_dir + xf

    partes.append(audio[cursor:])
    novo_audio = np.concatenate(partes, axis=0)

    dur_depois = len(novo_audio) / float(framerate)
    if len(novo_audio) == n_frames:
        return None

    # Grava o .wav no lugar
    with wave.open(str(wav_path), "wb") as wf:
        wf.setnchannels(n_channels)
        wf.setsampwidth(sampwidth)
        wf.setframerate(framerate)
        wf.writeframes(novo_audio.tobytes())

    # Atualiza <wav>.words.json se existir
    words_path = Path(str(wav_path) + ".words.json")
    if words_path.exists():
        palavras = ler_palavras(wav_path)
        cortes_s = [(s_ini / float(framerate), s_fim / float(framerate), (s_fim - s_ini - gap_samples) / float(framerate)) for s_ini, s_fim in cortes]

        def ajustar_tempo(t):
            desconto = 0.0
            for c_ini, c_fim, remov in cortes_s:
                if t <= c_ini:
                    break
                elif t >= c_fim:
                    desconto += remov
                else:
                    frac = (t - c_ini) / (c_fim - c_ini) if c_fim > c_ini else 0.0
                    desconto += frac * remov
                    break
            return round(max(0.0, t - desconto), 3)

        for w in palavras:
            if "start" in w:
                w["start"] = ajustar_tempo(float(w["start"]))
            if "end" in w:
                w["end"] = ajustar_tempo(float(w["end"]))
        gravar_palavras(wav_path, palavras)

    return (dur_antes, dur_depois)
