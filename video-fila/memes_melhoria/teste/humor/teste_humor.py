# -*- coding: utf-8 -*-
# PC1: testa humor_narrador numa COPIA (teste\humor) com roteiro real. Nao mexe na producao.
import logging, os, sys
sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
logging.basicConfig(level=logging.INFO, format="%(message)s")
sys.path.insert(0, r"D:\video-fila\memes_melhoria\teste\humor"); sys.path.insert(1, r"D:\recapd-ambientes\producao\bin")
import humor_narrador as h
print("modulo:", h.__file__)
os.environ["VOZ_CLONADA"] = sys.argv[2]
L = [l.strip() for l in open(sys.argv[1], encoding="utf-8") if l.strip()]
ini = int(sys.argv[3]); fr = L[ini:ini + 300]; tp = [float(i) for i in range(len(fr))]
novo, nt = h.polir(list(fr), list(tp))
assert len(novo) == len(nt) and all(nt[i] <= nt[i + 1] for i in range(len(nt) - 1)), "tempos quebrados"
orig = set(fr)
print(f"\n=== {len(fr)} -> {len(novo)} frases. NOVAS/MUDADAS (>>), com a frase de antes:")
for i, f in enumerate(novo):
    if f not in orig:
        print(f"   {novo[i-1][:95] if i else ''}\n>> {f}")
