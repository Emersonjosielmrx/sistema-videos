"""Pós-processamento da narração dos Shorts (trecho de comum/narracao_curva.py)."""
import json
import os
from pathlib import Path

LIMIAR_SILENCIO_DB = -40.0   # quadro de 10 ms abaixo disso (dBFS) é silêncio
GAP_MICROCORTE = 0.07        # segundos de silêncio que ficam entre as falas


def ler_palavras(wav):
    """Lista de {"word", "start", "end"} (segundos) do <wav>.words.json, ou [] se não tem."""
    p = Path(str(wav) + ".words.json")
    return json.loads(p.read_text("utf-8")) if p.exists() else []


def gravar_palavras(wav, palavras):
    Path(str(wav) + ".words.json").write_text(json.dumps(palavras, ensure_ascii=False), "utf-8")
