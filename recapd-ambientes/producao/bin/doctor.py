#!/usr/bin/env python3
"""doctor.py — RAIO-X do projeto Hipercool. Rode isto quando algo parecer errado
ou pra se localizar. Não muda nada; só reporta.

    D:\\hipercool-videos\\venv\\Scripts\\python.exe bin\\doctor.py
    ...\\python.exe bin\\doctor.py --cap the-warrior-disappointed-cap11   (checa cobertura de depth)

Mostra: pasta certa, deps do python, ffmpeg, caches (contagens), cobertura de
parallax, assets de efeito, flags e últimos vídeos. Verde = ok, ⚠ = atenção.
"""
import os
import sys
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OK, WARN, BAD = "  ✓", "  ⚠", "  ✗"


def _count(p, pat="*"):
    p = Path(p)
    return len(list(p.glob(pat))) if p.exists() else -1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cap", help="slug do capítulo (nome da pasta em workspace/panels) p/ checar cobertura de depth")
    args = ap.parse_args()

    print("=" * 60)
    print(f"HIPERCOOL DOCTOR — {ROOT}")
    print("=" * 60)

    # 1) Pasta certa
    print("\n[1] PASTA")
    marker = (ROOT / "bin" / "hiper-pipeline.py")
    is_fix = "inferior-fix" in str(ROOT)
    print((OK if is_fix else WARN), f"dir: {ROOT.name}", "(cópia CERTA)" if is_fix else "⚠ NÃO é -fix! confira LEIA_PRIMEIRO.md")
    try:
        n_sub = _count(ROOT / "bin" / "render_subtitles_short.py")  # marcador
    except Exception:
        n_sub = 0
    has_short = "render_subtitles_short" in (marker.read_text(encoding="utf-8", errors="ignore") if marker.exists() else "")
    print((OK if has_short else BAD), "render_subtitles_short no pipeline:", "sim" if has_short else "NÃO (cópia velha!)")

    # 2) Python deps
    print("\n[2] PYTHON")
    print("   ", sys.executable)
    import importlib.util as u
    for m in ("numpy", "torch", "transformers", "cv2", "PIL", "requests", "rembg"):
        ok = u.find_spec(m) is not None
        print((OK if ok else BAD), m, "ok" if ok else "FALTA → use D:\\hipercool-videos\\venv\\Scripts\\python.exe")

    # 3) ffmpeg
    print("\n[3] FFMPEG")
    import shutil
    for b in ("ffmpeg", "ffprobe"):
        p = shutil.which(b)
        print((OK if p else BAD), b, p or "NÃO ACHADO no PATH")

    # 4) Caches (ouro — não apagar)
    print("\n[4] CACHES (não apagar)")
    ws = ROOT / "workspace"
    for label, path, pat in [
        ("narração", ws / "narration_cache", "*.json"),
        ("censura (Sightengine)", ws / "censura_cache", "*.json"),
        ("depth (parallax)", Path(r"D:\hipercool-motionframes\cache\depth"), "*.png"),
        ("panel_class", ws / "panel_class_cache", "*"),
    ]:
        n = _count(path, pat)
        print((OK if n > 0 else WARN), f"{label}: {n if n >= 0 else 'pasta não existe'}")

    # 5) Cobertura de depth pro capítulo
    if args.cap:
        print(f"\n[5] DEPTH p/ {args.cap}")
        pdir = ws / "panels" / args.cap
        if not pdir.exists():
            print(BAD, "pasta de painéis não existe:", pdir)
        else:
            try:
                sys.path.insert(0, str(ROOT / "bin"))
                import parallax_engine as pe
                panels = sorted(pdir.glob("*.jpg"))
                hit = sum((pe._MF_CACHE / f"{pe._md5_file(x)}.png").exists() for x in panels)
                pct = (hit / len(panels) * 100) if panels else 0
                msg = f"{hit}/{len(panels)} cacheados ({pct:.0f}%)"
                if hit == 0:
                    msg += " → parallax só roda com PARALLAX_ONDEMAND=1 (gera na hora)"
                print((OK if hit else WARN), msg)
            except Exception as e:
                print(BAD, "erro:", e)

    # 6) Assets de efeito
    print("\n[6] ASSETS")
    el = ws / "assets" / "overlays" / "elemental"
    print(OK if _count(el, "fx_mascot*.mov") >= 14 else WARN,
          f"mascote poses: {_count(el, 'fx_mascot*.mov')} (esperado 14)")
    print(OK if _count(el, "fx_*.mov") > 50 else WARN, f"overlays elementais: {_count(el, 'fx_*.mov')}")
    print("   ", f"memes: {_count(ws / 'assets' / 'memes_img' / 'memes', '*.mp4')}")
    trans = _count(ws / "assets" / "overlays" / "transitions", "*.mp4")
    print("   ", f"transition clips: {trans} (0 = só corte seco/xfade, ok)")

    # 7) Flags ligadas neste ambiente
    print("\n[7] FLAGS (env atual — presets ligam tudo de uma vez)")
    for f in ("PANEL_FX", "PARALLAX", "PARALLAX_ONDEMAND", "MASCOTE_OVERLAY",
              "ELEMENTAL_TRANS", "MEMES", "TEST_MODE", "TTS_ENGINE"):
        v = os.environ.get(f)
        print("   ", f"{f}={v}" if v is not None else f"{f}=(default)")

    # 8) Últimos vídeos
    print("\n[8] ÚLTIMOS VÍDEOS")
    vids = sorted((ws / "videos").glob("*_ULTIMO.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)[:5]
    for v in vids:
        mb = v.stat().st_size / (1024 * 1024)
        print("   ", f"{v.name} ({mb:.0f}MB)")

    print("\n" + "=" * 60)
    print("Dica: rode com --preset teste|final no hiper-pipeline.py (liga efeitos certos).")
    print("Dica 2: Para monitorar o progresso, rode `run_painel_html.bat` na raiz (abre no navegador).")
    print("=" * 60)


if __name__ == "__main__":
    main()
