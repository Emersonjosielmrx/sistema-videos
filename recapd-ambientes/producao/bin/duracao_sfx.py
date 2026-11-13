#!/usr/bin/env python3
"""Mede duracao de todos os SFX e separa por: muito_curto (<8s, seguro) vs longo (>=8s, rever).

Tambem sinaliza nomes que parecem audio PROTEGIDO (musica/meme com trilha reconhecivel)
mesmo sendo SFX, pra revisao.
"""
import os, re, subprocess

PASTAS = [
    r"D:\hipercool-materiais\assets\sfx_memes",
    r"D:\hipercool-materiais\assets\sfx_extras",
    r"D:\hipercool-materiais\assets\sfx_foley",
    r"D:\hipercool-materiais\assets\sfx",
    r"D:\hipercool-materiais\assets\sfx_prioridade",
]
CURTO = 8.0

# nomes que sugerem MUSICA/trecho com melodia (risco mesmo sendo "sfx") - so se longo
SUSPEITA_MUSICA = re.compile(
    r"music|musica|song|theme|tema|trilha|beat|remix|ost|nyan|rickroll|never gonna|"
    r"megalovania|sandstorm|coffin|astronomia|pmv|amv|opening|ending", re.I)


def dur(path):
    try:
        out = subprocess.run(
            ["ffprobe","-v","quiet","-show_entries","format=duration",
             "-of","default=nw=1:nk=1", path],
            capture_output=True, text=True, timeout=30)
        return round(float(out.stdout.strip()), 1)
    except Exception:
        return -1.0


def main():
    tot = {"curto": 0, "longo": 0, "erro": 0}
    longos = []           # >=8s (rever)
    longos_suspeitos = [] # >=8s E nome sugere musica
    for pasta in PASTAS:
        if not os.path.isdir(pasta):
            continue
        base = os.path.basename(pasta)
        for f in sorted(os.listdir(pasta)):
            if not f.lower().endswith((".mp3",".wav",".m4a",".opus",".flac",".ogg")):
                continue
            d = dur(os.path.join(pasta, f))
            if d < 0:
                tot["erro"] += 1
            elif d < CURTO:
                tot["curto"] += 1
            else:
                tot["longo"] += 1
                entry = (base, f, d)
                longos.append(entry)
                if SUSPEITA_MUSICA.search(f):
                    longos_suspeitos.append(entry)
    print("=== SFX LONGOS SUSPEITOS (>=8s + nome de musica) — REVISAR ===")
    for base, f, d in sorted(longos_suspeitos, key=lambda x:-x[2]):
        print(f"  {d:6.1f}s  [{base}] {f}")
    print(f"\n=== TODOS OS LONGOS >=8s ({len(longos)}) ===")
    for base, f, d in sorted(longos, key=lambda x:-x[2]):
        print(f"  {d:6.1f}s  [{base}] {f}")
    print(f"\nRESUMO SFX: curto(<8s,seguro)={tot['curto']} | longo(>=8s,rever)={tot['longo']} "
          f"| erro={tot['erro']} | longos_suspeitos_musica={len(longos_suspeitos)}")


if __name__ == "__main__":
    main()
