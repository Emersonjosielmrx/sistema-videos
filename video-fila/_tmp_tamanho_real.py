import os, sys
from collections import defaultdict


def tamanho(raiz):
    """Soma real, sem seguir junction/symlink (os.walk followlinks=False + pula reparse points)."""
    tot = 0
    for dp, dns, fns in os.walk(raiz, followlinks=False):
        dns[:] = [d for d in dns if not os.path.islink(os.path.join(dp, d))
                  and not (os.stat(os.path.join(dp, d), follow_symlinks=False).st_file_attributes & 0x400)]
        for f in fns:
            try:
                tot += os.stat(os.path.join(dp, f), follow_symlinks=False).st_size
            except OSError:
                pass
    return tot


for raiz in sys.argv[1:]:
    filhos = []
    for d in os.scandir(raiz):
        if d.is_dir(follow_symlinks=False) and not (d.stat(follow_symlinks=False).st_file_attributes & 0x400):
            filhos.append((tamanho(d.path), d.name))
    tot = sum(t for t, _ in filhos)
    print(f"== {raiz}  {tot / 1e9:.1f} GB reais")
    for t, n in sorted(filhos, reverse=True)[:8]:
        if t > 0.5e9:
            print(f"   {t / 1e9:6.1f} GB  {n}")
