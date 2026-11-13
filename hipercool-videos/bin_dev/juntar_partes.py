#!/usr/bin/env python3
"""juntar_partes.py — Junta partes de um capítulo num vídeo único.

Uso:
    python bin/juntar_partes.py parte1.mp4 parte2.mp4 [parte3.mp4 ...] \
        --out workspace/videos/cap2_COMPLETO_ULTIMO.mp4

Concatena com -c copy (sem re-encode) quando os params batem; se falhar,
re-encoda. Segue a convenção _ULTIMO no nome do output.
"""
import argparse
import subprocess
import sys
from pathlib import Path


def juntar(partes, out_path):
    partes = [Path(p) for p in partes]
    for p in partes:
        if not p.exists():
            print(f"ERRO: não existe: {p}", file=sys.stderr)
            return False

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    list_file = out_path.parent / "_juntar_partes.txt"
    list_file.write_text("".join(f"file '{p.resolve()}'\n" for p in partes))

    # Tenta copy puro (sem re-encode)
    cmd_copy = ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
                "-i", str(list_file), "-c", "copy",
                "-movflags", "+faststart", str(out_path)]
    try:
        subprocess.run(cmd_copy, check=True, capture_output=True, timeout=180)
        print(f"✅ Juntado (copy): {out_path}")
    except subprocess.CalledProcessError:
        # Fallback: re-encode
        cmd_re = ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
                  "-i", str(list_file),
                  "-c:v", "libx264", "-preset", "fast", "-crf", "23", "-g", "30",
                  "-c:a", "aac", "-b:a", "192k",
                  "-movflags", "+faststart", "-pix_fmt", "yuv420p", str(out_path)]
        subprocess.run(cmd_re, check=True, capture_output=True, timeout=600)
        print(f"✅ Juntado (re-encode): {out_path}")
    finally:
        try:
            list_file.unlink()
        except Exception:
            pass

    if out_path.exists():
        size = out_path.stat().st_size / (1024 * 1024)
        dur = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "csv=p=0", str(out_path)],
            capture_output=True, text=True).stdout.strip()
        print(f"   {size:.1f} MB, {float(dur):.0f}s")
        return True
    return False


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("partes", nargs="+", help="MP4s na ordem (parte1 parte2 ...)")
    ap.add_argument("--out", required=True, help="Caminho do MP4 final (use _ULTIMO no nome)")
    args = ap.parse_args()
    ok = juntar(args.partes, args.out)
    sys.exit(0 if ok else 1)
