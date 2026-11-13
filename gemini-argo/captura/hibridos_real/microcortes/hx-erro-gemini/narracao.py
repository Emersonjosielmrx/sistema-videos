"""Pós-processamento da narração dos Shorts (trecho de comum/narracao_curva.py)."""
import json
import os
import wave
from pathlib import Path

import numpy as np

LIMIAR_SILENCIO_DB = -40.0   # quadro de 10 ms abaixo disso (dBFS) é silêncio
GAP_MICROCORTE = 0.07        # segundos de silêncio que ficam entre as falas
CROSSFADE_S = 0.006          # 6 ms de crossfade na emenda
QUADRO_S = 0.010             # quadro de análise de 10 ms


def ler_palavras(wav):
    """Lista de {"word", "start", "end"} (segundos) do <wav>.words.json, ou [] se não tem."""
    p = Path(str(wav) + ".words.json")
    return json.loads(p.read_text("utf-8")) if p.exists() else []


def gravar_palavras(wav, palavras):
    Path(str(wav) + ".words.json").write_text(json.dumps(palavras, ensure_ascii=False), "utf-8")


def microcortes(wav, gap_s=None):
    """Encurta silêncios maiores que gap_s no .wav (16-bit mono/estéreo) no lugar.

    Mantém as pontas originais do silêncio com crossfade de 6 ms na emenda central,
    sem acelerar nem alterar a fala, e atualiza <wav>.words.json se existir.
    Devolve (duracao_antes, duracao_depois) em segundos, ou None se nada foi cortado.
    """
    if gap_s is None:
        gap_s = GAP_MICROCORTE

    wav_path = Path(wav)
    with wave.open(str(wav_path), "rb") as wf:
        nchannels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        nframes = wf.getnframes()
        comptype = wf.getcomptype()
        compname = wf.getcompname()
        raw = wf.readframes(nframes)

    if sampwidth != 2:
        raise ValueError(f"Apenas WAV de 16 bits é suportado (recebido {sampwidth * 8} bits).")
    if nframes == 0:
        return None

    amostras = np.frombuffer(raw, dtype=np.int16).reshape(-1, nchannels)
    dur_antes = nframes / float(framerate)

    quadro_len = max(1, int(round(framerate * QUADRO_S)))
    gap_len = int(round(framerate * gap_s))
    cf_padrao = int(round(framerate * CROSSFADE_S))

    n_quadros = nframes // quadro_len
    if n_quadros == 0:
        return None

    # Calcula dBFS (RMS relativo a 32768.0) para cada quadro de 10 ms
    blocos = amostras[: n_quadros * quadro_len].astype(np.float64) / 32768.0
    blocos = blocos.reshape(n_quadros, quadro_len * nchannels)
    rms = np.sqrt(np.mean(blocos * blocos, axis=1))
    limiar_linear = 10.0 ** (LIMIAR_SILENCIO_DB / 20.0)
    silencio_quadro = rms < limiar_linear

    # Identifica intervalos contíguos de silêncio [ini, fim)
    intervalos_corte = []
    i = 0
    while i < n_quadros:
        if silencio_quadro[i]:
            j = i + 1
            while j < n_quadros and silencio_quadro[j]:
                j += 1
            ini = i * quadro_len
            fim = j * quadro_len
            if fim - ini > gap_len:
                intervalos_corte.append((ini, fim))
            i = j
        else:
            i += 1

    if not intervalos_corte:
        return None

    partes = []
    cursor = 0
    for ini, fim in intervalos_corte:
        if ini > cursor:
            partes.append(amostras[cursor:ini])

        tam_sil = fim - ini
        if gap_len <= 0:
            cursor = fim
            continue

        cf = min(cf_padrao, gap_len, tam_sil - gap_len)
        meio_esq = gap_len // 2
        meio_dir = gap_len - meio_esq

        if cf > 0:
            cf_esq = cf // 2
            cf_dir = cf - cf_esq

            ponta_esq_len = meio_esq - cf_esq
            ponta_dir_len = meio_dir - cf_dir

            if ponta_esq_len > 0:
                partes.append(amostras[ini : ini + ponta_esq_len])

            bloco_esq = amostras[ini + ponta_esq_len : ini + ponta_esq_len + cf].astype(np.float64)
            bloco_dir = amostras[fim - ponta_dir_len - cf : fim - ponta_dir_len].astype(np.float64)

            pesos = np.linspace(0.0, 1.0, cf, endpoint=True, dtype=np.float64).reshape(-1, 1)
            emenda = np.round(bloco_esq * (1.0 - pesos) + bloco_dir * pesos)
            emenda = np.clip(emenda, -32768, 32767).astype(np.int16)
            partes.append(emenda)

            if ponta_dir_len > 0:
                partes.append(amostras[fim - ponta_dir_len : fim])
        else:
            if meio_esq > 0:
                partes.append(amostras[ini : ini + meio_esq])
            if meio_dir > 0:
                partes.append(amostras[fim - meio_dir : fim])

        cursor = fim

    if cursor < nframes:
        partes.append(amostras[cursor:nframes])

    novo_audio = np.vstack(partes) if partes else np.empty((0, nchannels), dtype=np.int16)
    dur_depois = novo_audio.shape[0] / float(framerate)

    # Grava o .wav no lugar
    with wave.open(str(wav_path), "wb") as wf_out:
        wf_out.setnchannels(nchannels)
        wf_out.setsampwidth(sampwidth)
        wf_out.setframerate(framerate)
        wf_out.setcomptype(comptype, compname)
        wf_out.writeframes(novo_audio.tobytes())

    # Atualiza <wav>.words.json se existir
    words_path = Path(str(wav_path) + ".words.json")
    if words_path.exists():
        palavras = ler_palavras(wav_path)
        cortes_s = []
        for ini, fim in intervalos_corte:
            meio_esq = gap_len // 2
            meio_dir = gap_len - meio_esq
            corte_ini_s = (ini + meio_esq) / float(framerate)
            corte_fim_s = (fim - meio_dir) / float(framerate)
            cortado_s = ((fim - ini) - gap_len) / float(framerate)
            cortes_s.append((corte_ini_s, corte_fim_s, cortado_s))

        def ajustar_tempo(t):
            desconto = 0.0
            for c_ini, c_fim, c_dur in cortes_s:
                if t <= c_ini:
                    break
                elif t >= c_fim:
                    desconto += c_dur
                else:
                    desconto += (t - c_ini)
                    break
            return round(max(0.0, t - desconto), 4)

        novas_palavras = []
        for item in palavras:
            novo_item = dict(item)
            if "start" in novo_item:
                novo_item["start"] = ajustar_tempo(float(novo_item["start"]))
            if "end" in novo_item:
                novo_item["end"] = ajustar_tempo(float(novo_item["end"]))
            novas_palavras.append(novo_item)
        gravar_palavras(wav_path, novas_palavras)

    return (dur_antes, dur_depois)
