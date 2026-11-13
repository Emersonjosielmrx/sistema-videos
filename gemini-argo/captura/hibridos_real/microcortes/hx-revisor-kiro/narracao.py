"""Pós-processamento da narração dos Shorts (trecho de comum/narracao_curva.py)."""
import json
import os
import wave
import numpy as np
from pathlib import Path

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
    Remove pausas longas entre as falas, mantendo gap_s de silêncio.

    Args:
        wav: caminho do arquivo .wav (16 bits, mono ou estéreo)
        gap_s: duração do silêncio que fica (padrão GAP_MICROCORTE)

    Returns:
        (duração_antes, duração_depois) em segundos, ou None se não há nada a cortar
    """
    if gap_s is None:
        gap_s = GAP_MICROCORTE

    wav_path = Path(wav)

    # Ler o WAV
    with wave.open(str(wav_path), 'rb') as wf:
        n_canais = wf.getnchannels()
        sample_width = wf.getsampwidth()
        taxa = wf.getframerate()
        n_quadros = wf.getnframes()
        audio_bytes = wf.readframes(n_quadros)

    # Converter para numpy (int16)
    if sample_width != 2:
        raise ValueError(f"Apenas 16 bits suportado, encontrado {sample_width * 8} bits")

    audio = np.frombuffer(audio_bytes, dtype=np.int16)
    if n_canais == 2:
        audio = audio.reshape(-1, 2)

    duracao_antes = n_quadros / taxa

    # Detectar silêncio em janelas de 10 ms
    janela_samples = int(taxa * 0.01)  # 10 ms
    crossfade_samples = int(taxa * 0.006)  # 6 ms
    gap_samples = int(taxa * gap_s)

    # Calcular RMS por janela e converter para dB
    n_janelas = len(audio) // janela_samples
    if n_canais == 2:
        rms_por_janela = np.array([
            np.sqrt(np.mean(audio[i*janela_samples:(i+1)*janela_samples]**2))
            for i in range(n_janelas)
        ])
    else:
        rms_por_janela = np.array([
            np.sqrt(np.mean(audio[i*janela_samples:(i+1)*janela_samples]**2))
            for i in range(n_janelas)
        ])

    # Converter para dBFS (referência = 32768 para int16)
    rms_por_janela = np.maximum(rms_por_janela, 1e-10)  # evitar log(0)
    db_por_janela = 20 * np.log10(rms_por_janela / 32768.0)

    # Identificar janelas de silêncio
    silencio = db_por_janela < LIMIAR_SILENCIO_DB

    # Encontrar regiões contíguas de silêncio
    regioes_silencio = []
    em_silencio = False
    inicio_silencio = 0

    for i, e_silencio in enumerate(silencio):
        if e_silencio and not em_silencio:
            inicio_silencio = i
            em_silencio = True
        elif not e_silencio and em_silencio:
            regioes_silencio.append((inicio_silencio, i))
            em_silencio = False

    if em_silencio:
        regioes_silencio.append((inicio_silencio, len(silencio)))

    # Filtrar apenas gaps maiores que gap_s
    gaps_para_cortar = []
    for inicio_jan, fim_jan in regioes_silencio:
        inicio_sample = inicio_jan * janela_samples
        fim_sample = fim_jan * janela_samples
        duracao_gap = (fim_sample - inicio_sample) / taxa

        if duracao_gap > gap_s:
            gaps_para_cortar.append((inicio_sample, fim_sample, duracao_gap))

    if not gaps_para_cortar:
        return None  # nada a cortar

    # Construir novo áudio com cortes
    segmentos = []
    tempo_removido_acumulado = []  # para ajustar timestamps
    tempo_removido = 0.0
    pos_atual = 0

    for inicio_gap, fim_gap, duracao_gap in gaps_para_cortar:
        # Adicionar áudio antes do gap
        segmentos.append(audio[pos_atual:inicio_gap])

        # Adicionar gap reduzido com crossfade
        if gap_samples > 0:
            # Pegar as pontas do gap original
            ponta_inicio = audio[inicio_gap:min(inicio_gap + crossfade_samples, fim_gap)]
            ponta_fim = audio[max(fim_gap - crossfade_samples, inicio_gap):fim_gap]

            # Criar o gap de tamanho gap_samples
            if len(ponta_inicio) + len(ponta_fim) >= gap_samples:
                # Usar as pontas com crossfade
                fade_out = np.linspace(1, 0, len(ponta_inicio)).reshape(-1, 1) if n_canais == 2 else np.linspace(1, 0, len(ponta_inicio))
                fade_in = np.linspace(0, 1, len(ponta_fim)).reshape(-1, 1) if n_canais == 2 else np.linspace(0, 1, len(ponta_fim))

                parte_inicio = (ponta_inicio * fade_out).astype(np.int16)
                parte_fim = (ponta_fim * fade_in).astype(np.int16)

                # Silêncio no meio se necessário
                silencio_meio = gap_samples - len(parte_inicio) - len(parte_fim)
                if silencio_meio > 0:
                    if n_canais == 2:
                        meio = np.zeros((silencio_meio, 2), dtype=np.int16)
                    else:
                        meio = np.zeros(silencio_meio, dtype=np.int16)
                    segmentos.extend([parte_inicio, meio, parte_fim])
                else:
                    segmentos.extend([parte_inicio, parte_fim])
            else:
                # Gap muito pequeno, usar o que tiver
                segmentos.append(audio[inicio_gap:fim_gap])

        tempo_removido += duracao_gap - gap_s
        tempo_removido_acumulado.append((fim_gap / taxa, tempo_removido))
        pos_atual = fim_gap

    # Adicionar o resto do áudio
    segmentos.append(audio[pos_atual:])

    # Concatenar segmentos
    audio_novo = np.concatenate(segmentos)

    # Gravar o WAV modificado
    with wave.open(str(wav_path), 'wb') as wf:
        wf.setnchannels(n_canais)
        wf.setsampwidth(sample_width)
        wf.setframerate(taxa)
        wf.writeframes(audio_novo.tobytes())

    duracao_depois = len(audio_novo) / taxa

    # Atualizar .words.json se existir
    palavras = ler_palavras(wav)
    if palavras:
        for palavra in palavras:
            # Ajustar timestamps baseado no tempo removido acumulado
            for tempo_corte, tempo_remov in tempo_removido_acumulado:
                if palavra['start'] >= tempo_corte:
                    palavra['start'] -= tempo_remov
                    palavra['end'] -= tempo_remov
                    break
                elif palavra['end'] > tempo_corte:
                    # Palavra cruza um corte (raro)
                    palavra['end'] -= tempo_remov
                    break

        gravar_palavras(wav, palavras)

    return (duracao_antes, duracao_depois)
