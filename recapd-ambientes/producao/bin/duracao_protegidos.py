#!/usr/bin/env python3
"""Reclassifica os PROTEGIDOS por DURACAO/USO:

- TRILHA (risco real de Content ID): faixa musical com duracao de musica (>= ~20s).
- TRECHO_CURTO / EFEITO: muito curto (< ~8s) -> na pratica nao gera reivindicacao.
- ZONA_CINZA: entre 8s e 20s -> depende; rever.

Le duracao via ffprobe.
"""
import os, re, subprocess, json
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("cc", str(Path(__file__).resolve().parent / "classificar_copyright.py"))
cc = importlib.util.module_from_spec(spec); spec.loader.exec_module(cc)

TRILHAS = cc.TRILHAS
CURTO = 8.0      # < 8s: efeito/sting, nao reivindicavel na pratica
TRILHA_MIN = 20.0  # >= 20s: trilha de verdade


def dur(path):
    try:
        out = subprocess.run(
            ["ffprobe","-v","quiet","-show_entries","format=duration",
             "-of","default=nw=1:nk=1", path],
            capture_output=True, text=True, timeout=30)
        return float(out.stdout.strip())
    except Exception:
        return -1.0


files = sorted(os.listdir(TRILHAS))
files = [f for f in files if f.lower().endswith((".mp3",".wav",".m4a",".opus",".flac"))]
prot = [f for f in files if cc.classify(f)[0] == "PROTEGIDO"]

buckets = {"TRILHA_RISCO": [], "ZONA_CINZA": [], "TRECHO_CURTO": [], "ERRO": []}
for f in sorted(prot):
    d = dur(os.path.join(TRILHAS, f))
    if d < 0:
        buckets["ERRO"].append((f, d))
    elif d < CURTO:
        buckets["TRECHO_CURTO"].append((f, d))
    elif d < TRILHA_MIN:
        buckets["ZONA_CINZA"].append((f, d))
    else:
        buckets["TRILHA_RISCO"].append((f, d))

for cat in ("TRECHO_CURTO","ZONA_CINZA","TRILHA_RISCO","ERRO"):
    lst = buckets[cat]
    print(f"\n===== {cat} ({len(lst)}) =====")
    for f, d in sorted(lst, key=lambda x: x[1]):
        print(f"  {d:6.1f}s  {f}")
print(f"\nTOTAL PROT={len(prot)} | curto={len(buckets['TRECHO_CURTO'])} "
      f"cinza={len(buckets['ZONA_CINZA'])} trilha={len(buckets['TRILHA_RISCO'])} "
      f"erro={len(buckets['ERRO'])}")
