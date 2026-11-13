#!/usr/bin/env python
"""Wrapper subprocesso que libera memória entre chunks do Whisper."""
import os
import sys
from pathlib import Path

os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

wav_dir = Path(sys.argv[1])
model_size = sys.argv[2] if len(sys.argv) > 2 else "tiny"
out_txt = Path(sys.argv[3]) if len(sys.argv) > 3 else Path("transcricao.txt")

import subprocess

chunks = sorted(wav_dir.glob("chunk_*.wav"))
out_txt.parent.mkdir(parents=True, exist_ok=True)
out_txt.write_text("", encoding="utf-8")

for i, chunk in enumerate(chunks):
    print(f"=== Chunk {i+1}/{len(chunks)}: {chunk.name} ===", flush=True)
    try:
        r = subprocess.run(
            [sys.executable, str(Path(__file__).parent / "_whisper_sub.py"),
             str(chunk), model_size],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=900,
        )
        if r.returncode == 0:
            lines = r.stdout.strip().splitlines()
            txt = lines[0] if lines else ""
            lang = lines[1] if len(lines) > 1 else "?"
            print(f"  lang={lang}, len={len(txt)} chars", flush=True)
            with open(out_txt, "a", encoding="utf-8") as f:
                f.write(txt + "\n")
        else:
            err = r.stderr.strip().splitlines()[-3:] if r.stderr.strip() else []
            print(f"  FALHOU: {' | '.join(err)}", flush=True)
            with open(out_txt, "a", encoding="utf-8") as f:
                f.write(f"[ERRO chunk {i}]\n")
    except subprocess.TimeoutExpired:
        print(f"  TIMEOUT", flush=True)
        with open(out_txt, "a", encoding="utf-8") as f:
            f.write(f"[TIMEOUT chunk {i}]\n")

print(f"OK → {out_txt} ({out_txt.stat().st_size} bytes)", flush=True)