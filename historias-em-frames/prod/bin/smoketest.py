# -*- coding: utf-8 -*-
"""smoketest.py — Teste rápido do pipeline (gera 1 vídeo curto com preset teste).

Valida que imports, TTS, render, concat funcionam. Resultado em workspace/videos/.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from story_pipeline import run


def smoketest():
    print("=" * 50)
    print("SMOKETEST — Historias em Frames")
    print("  Gerando 1 video com preset 'teste' (6 cenas, rapido)")
    print("=" * 50)

    t0 = time.time()
    result = run(
        genero="superacao",
        tema="garoto que aprendeu a programar sozinho",
        preset="teste",
        output_suffix="_smoketest",
        skip_notify=True,
        quality="low",
    )
    elapsed = time.time() - t0

    print(f"\nTempo: {elapsed:.0f}s ({elapsed/60:.1f} min)")

    if result and result.get("video"):
        video = Path(result["video"])
        if video.exists():
            size_mb = video.stat().st_size / (1024 * 1024)
            print(f"OK: {video}")
            print(f"  Tamanho: {size_mb:.1f} MB")
            print(f"  Duracao: {result.get('duracao_s', 0):.0f}s")
            return 0
        else:
            print(f"FAIL: arquivo nao existe: {video}")
            return 1
    elif result and result.get("audio_count"):
        print(f"PARCIAL: audio gerado ({result['audio_count']} arquivos) mas video falhou")
        return 1
    else:
        print("FAIL: pipeline retornou None")
        return 1


if __name__ == "__main__":
    sys.exit(smoketest())
