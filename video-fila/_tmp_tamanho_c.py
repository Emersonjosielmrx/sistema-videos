import os


def tamanho(raiz):
    tot = 0
    for dp, dns, fns in os.walk(raiz, followlinks=False, onerror=lambda e: None):
        keep = []
        for d in dns:
            p = os.path.join(dp, d)
            try:
                if not (os.stat(p, follow_symlinks=False).st_file_attributes & 0x400):
                    keep.append(d)
            except OSError:
                pass
        dns[:] = keep
        for f in fns:
            try:
                tot += os.stat(os.path.join(dp, f), follow_symlinks=False).st_size
            except OSError:
                pass
    return tot


for raiz in (r"C:\\", r"C:\Users\Haylla", r"C:\Users\Haylla\AppData\Local", r"C:\Users\Haylla\AppData\Roaming",
             r"C:\ProgramData"):
    out = []
    try:
        for d in os.scandir(raiz):
            try:
                if d.is_dir(follow_symlinks=False) and not (d.stat(follow_symlinks=False).st_file_attributes & 0x400):
                    out.append((tamanho(d.path), d.name))
            except OSError:
                pass
    except OSError:
        continue
    print(f"== {raiz}")
    for t, n in sorted(out, reverse=True)[:7]:
        if t > 0.8e9:
            print(f"   {t / 1e9:6.1f} GB  {n}")
