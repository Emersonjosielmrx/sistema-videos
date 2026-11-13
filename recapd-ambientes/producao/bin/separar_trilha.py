#!/usr/bin/env python3
"""Separa voz/trilha com demucs via API, salvando WAV com soundfile.

Contorna o torchcodec quebrado (torchaudio.save exige torchcodec, cuja DLL nao
carrega). Usa demucs.apply.apply_model direto e grava com soundfile.

Uso: python separar_trilha.py <audio_in> <out_dir>
Gera: <out_dir>/vocals.wav e <out_dir>/no_vocals.wav
"""
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
from demucs.apply import apply_model
from demucs.audio import convert_audio
from demucs.pretrained import get_model


def carregar_audio(caminho, sample_rate, canais):
    # le qualquer formato via soundfile (libsndfile); mp3 suportado na 0.14
    wav, sr = sf.read(str(caminho), dtype="float32", always_2d=True)
    # soundfile devolve (amostras, canais) -> queremos (canais, amostras)
    tensor = torch.from_numpy(wav.T).float()
    tensor = convert_audio(tensor, sr, sample_rate, canais)
    return tensor


def main():
    audio_in = Path(sys.argv[1])
    out_dir = Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"  carregando modelo htdemucs...")
    model = get_model("htdemucs")
    model.eval()

    print(f"  lendo {audio_in.name}...")
    wav = carregar_audio(audio_in, model.samplerate, model.audio_channels)

    ref = wav.mean(0)
    wav_norm = (wav - ref.mean()) / (ref.std() + 1e-8)

    print(f"  separando (CPU, pode levar minutos)...")
    with torch.no_grad():
        sources = apply_model(
            model, wav_norm[None], device="cpu", progress=True, split=True, overlap=0.25
        )[0]
    sources = sources * ref.std() + ref.mean()

    nomes = model.sources  # ['drums','bass','other','vocals']
    idx_vocals = nomes.index("vocals")

    vocals = sources[idx_vocals]
    no_vocals = sum(sources[i] for i in range(len(nomes)) if i != idx_vocals)

    sr = model.samplerate
    sf.write(str(out_dir / "vocals.wav"), vocals.T.numpy(), sr)
    sf.write(str(out_dir / "no_vocals.wav"), no_vocals.T.numpy(), sr)
    # tambem um mp3 leve da trilha pra ouvir/abrir rapido
    print(f"  OK -> {out_dir/'no_vocals.wav'}")


if __name__ == "__main__":
    main()
