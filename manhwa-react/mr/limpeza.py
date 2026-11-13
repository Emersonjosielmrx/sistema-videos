"""Limpeza automatica do que e regeneravel: wavs intermediarios do work/ e video/audio baixados das bases/.

O que fica: transcript.json, silences.json, temas.json, cenas.json, base.json (cache barato que evita refazer o Whisper).
O que sai: raw.wav, clean.wav, grande_audio.wav, final.wav, mixed.wav (refeitos sozinhos se o video for reprocessado)
e bases/<id>/base.mp4 + audio16k.wav (a base so precisa da transcricao depois de preparada).
So apaga o que esta parado ha HORAS, para nunca pegar um video em processamento.
"""
import time
from pathlib import Path

from .common import log

HORAS_WORK = 6
HORAS_BASES = 24


def _velhos(pasta, padroes, horas):
    limite = time.time() - horas * 3600
    for pad in padroes:
        for f in Path(pasta).rglob(pad):
            try:
                if f.is_file() and f.stat().st_mtime < limite:
                    yield f
            except OSError:
                continue


def limpar(cfg):
    work = Path(cfg["paths"]["work"])
    bases = Path(cfg["paths"].get("bases", work.parent / "bases"))
    n, total = 0, 0
    alvos = list(_velhos(work, ["*.wav"], HORAS_WORK)) if work.exists() else []
    if bases.exists():
        alvos += list(_velhos(bases, ["base.mp4", "audio16k.wav"], HORAS_BASES))
    for f in alvos:
        try:
            tam = f.stat().st_size
            f.unlink()
            n, total = n + 1, total + tam
        except OSError:
            continue  # em uso: fica para a proxima
    if n:
        log(f"limpeza: {n} arquivo(s) intermediario(s) apagado(s), {total / 1e6:.0f} MB liberados")
    return n, total
