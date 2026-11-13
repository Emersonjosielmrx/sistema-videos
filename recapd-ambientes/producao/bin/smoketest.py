#!/usr/bin/env python3
"""smoketest.py — verifica a CADEIA DE RENDER em ~1 min, sem LLM/TTS/narração.
Rode depois de mexer em censura/efeitos/parallax pra saber se quebrou, sem
esperar 25 min de render completo.

    D:\\hipercool-videos\\venv\\Scripts\\python.exe bin\\smoketest.py
    ...\\python.exe bin\\smoketest.py --cap the-warrior-disappointed-cap11

Testa em 1 painel real: censura (leve+forte), panel-fx, parallax (ondemand),
build_clip padrão. Verde = ok, ✗ = quebrou (com o erro).
"""
import os
import sys
import argparse
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "bin"))
os.environ.setdefault("PYTHONUTF8", "1")

OK, BAD = "  ✓", "  ✗"
_fails = 0


def check(nome, fn):
    global _fails
    try:
        r = fn()
        if r:
            print(OK, nome)
        else:
            print(BAD, nome, "→ retornou vazio/False")
            _fails += 1
    except Exception as e:
        print(BAD, nome, f"→ {type(e).__name__}: {str(e)[:150]}")
        _fails += 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cap", help="slug do capítulo (pasta em workspace/panels)")
    args = ap.parse_args()

    print("=" * 56)
    print("HIPERCOOL SMOKETEST (cadeia de render, sem LLM/TTS)")
    print("=" * 56)

    # 1) achar um painel real
    pdir = None
    if args.cap:
        pdir = ROOT / "workspace" / "panels" / args.cap
    if not (pdir and pdir.exists()):
        cands = [d for d in (ROOT / "workspace" / "panels").glob("*") if list(d.glob("*.jpg"))]
        pdir = cands[0] if cands else None
    if not pdir:
        print(BAD, "nenhuma pasta de painéis encontrada"); sys.exit(1)
    panels = sorted(pdir.glob("*.jpg"))
    painel = str(panels[len(panels) // 2])  # um do meio (evita capa)
    print(f"  painel-cobaia: {Path(painel).name} de {pdir.name}\n")

    tmp = Path(tempfile.mkdtemp(prefix="smoke_"))
    # wav silencioso de 2s p/ os builders que exigem áudio
    wav = tmp / "s.wav"
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
                    "-t", "2", str(wav)], capture_output=True, timeout=30)

    # 2) censura (leve = exodia, forte = blur)
    import censura_visual as cv
    check("censura NIVEL2_TOTAL_BLUR (forte)",
          lambda: cv.censurar_imagem(painel, str(tmp / "cf.jpg"), 2.0) and (tmp / "cf.jpg").exists())
    check("censura NIVEL1_EXODIA_FOSCO (leve)",
          lambda: cv.censurar_imagem(painel, str(tmp / "cl.jpg"), 0.6) and (tmp / "cl.jpg").exists())

    # 3) panel-fx (T15)
    import panel_effects as pfx
    check("panel-fx build_effect_clip (dollypush)",
          lambda: pfx.build_effect_clip(painel, str(wav), str(tmp / "fx.mp4"), "dollypush") and (tmp / "fx.mp4").exists())

    # 4) parallax 2.5D (ondemand — gera depth)
    import parallax_engine as pe
    import effects_engine as ee
    check("parallax build_parallax_clip (ondemand)",
          lambda: pe.build_parallax_clip(painel, str(wav), str(tmp / "px.mp4"),
                                         W=ee.W, H=ee.H, fps=ee.FPS) and (tmp / "px.mp4").exists())

    # 5) build_clip padrão (Ken Burns + efeitos)
    check("effects_engine.build_clip (padrão)",
          lambda: ee.build_clip(painel, str(wav), str(tmp / "kb.mp4"), 0, ee.EffectsManager()) and (tmp / "kb.mp4").exists())

    # cleanup
    import shutil
    shutil.rmtree(tmp, ignore_errors=True)

    print("\n" + "=" * 56)
    if _fails == 0:
        print("✓ TUDO OK — cadeia de render saudável.")
    else:
        print(f"✗ {_fails} falha(s) — veja acima. Cadeia de render QUEBRADA.")
    print("=" * 56)
    sys.exit(1 if _fails else 0)


if __name__ == "__main__":
    main()
