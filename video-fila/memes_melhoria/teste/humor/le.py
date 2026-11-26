import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
d = r"D:\video-fila\memes_melhoria\teste\humor"
for l in open(d + r"\saida_v2.log", encoding="utf-8", errors="replace"):
    if l.startswith(">>") or "frases" in l: print(l.rstrip()[:200])
for l in open(d + r"\erro_v2.log", encoding="utf-8", errors="replace"):
    if "[humor]" in l or "Traceback" in l or "Error" in l: print(l.rstrip()[:900])
