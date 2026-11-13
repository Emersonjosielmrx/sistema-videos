"""Mede e apaga SÓ cache do Chrome (recriável), mantendo login/cookies/senhas de todos os perfis (10/11, dona: "os
caches pode apagar tudo, só não os perfis, porque não quero logar de novo"). Apaga dentro de cada perfil apenas as
pastas de cache; nunca Cookies, Login Data, Local Storage, IndexedDB, Preferences nem Network\\Cookies.
    python _tmp_cache_chrome.py [--apagar]"""
import os, shutil, sys
CACHES = ("Cache", "Code Cache", "GPUCache", "DawnCache", "DawnGraphiteCache", "DawnWebGPUCache", "GrShaderCache",
          "ShaderCache", "Service Worker\\CacheStorage", "Service Worker\\ScriptCache", "Media Cache",
          "Application Cache", "VideoDecodeStats", "optimization_guide_hint_cache_store",
          "optimization_guide_model_store")
RAIZ_CACHE = ("component_crx_cache", "GrShaderCache", "ShaderCache", "GraphiteDawnCache", "Crashpad\\reports",
              "extensions_crx_cache", "Safe Browsing")
apagar = "--apagar" in sys.argv
raizes = [r"C:\Users\Haylla\AppData\Local\Google\Chrome\User Data"]
# perfis do cofre (Chrome de automação) — também só cache
for base in (r"D:\logins-google\cofre", r"D:\logins-google\chrome-profiles"):
    if os.path.isdir(base):
        raizes += [os.path.join(base, d) for d in os.listdir(base) if os.path.isdir(os.path.join(base, d))]


def tam(p):
    t = 0
    for dp, _, fns in os.walk(p):
        for f in fns:
            try:
                t += os.path.getsize(os.path.join(dp, f))
            except OSError:
                pass
    return t


tot = {}
for r in raizes:
    alvos = [os.path.join(r, c) for c in RAIZ_CACHE]
    for perfil in (os.listdir(r) if os.path.isdir(r) else []):
        pp = os.path.join(r, perfil)
        if os.path.isdir(pp) and (perfil == "Default" or perfil.startswith("Profile")):
            alvos += [os.path.join(pp, c) for c in CACHES]
    for a in alvos:
        if os.path.isdir(a):
            t = tam(a)
            if t:
                disco = a[:2].upper()
                tot[disco] = tot.get(disco, 0) + t
                if apagar:
                    shutil.rmtree(a, ignore_errors=True)
for d, t in tot.items():
    print(f"{d} cache do Chrome: {t / 1e9:.2f} GB" + (" — apagado" if apagar else ""))
for d in ("C:\\", "D:\\"):
    print(d, "livre", round(shutil.disk_usage(d).free / 1e9, 2), "GB")
