"""Limpa SÓ cache recriável do C: (10/11, C com 1,9 GB). Não toca perfil do Chrome nem dados do Claude.
- Temp do usuário: arquivos com mais de 2 dias (em uso dá erro e é pulado)
- VS Code CachedExtensionVSIXs: cópias dos instaladores de extensões já instaladas"""
import os, shutil, time
livre0 = shutil.disk_usage("C:\\").free
lim = time.time() - 2 * 86400
tot = 0
for raiz in (r"C:\Users\Haylla\AppData\Local\Temp",):
    for dp, dns, fns in os.walk(raiz):
        if "claude" in dp.lower():  # arquivos de saída das tarefas do Claude ficam
            continue
        for f in fns:
            p = os.path.join(dp, f)
            try:
                st = os.stat(p)
                if st.st_mtime < lim:
                    os.remove(p)
                    tot += st.st_size
            except OSError:
                pass
v = r"C:\Users\Haylla\AppData\Roaming\Code\CachedExtensionVSIXs"
if os.path.isdir(v):
    for f in os.listdir(v):
        p = os.path.join(v, f)
        try:
            s = os.path.getsize(p) if os.path.isfile(p) else 0
            (os.remove if os.path.isfile(p) else shutil.rmtree)(p)
            tot += s
        except OSError:
            pass
livre1 = shutil.disk_usage("C:\\").free
print(f"apagado ~{tot / 1e6:.0f} MB | C livre {livre0 / 1e9:.2f} -> {livre1 / 1e9:.2f} GB")
