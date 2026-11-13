"""limpar_cache_chrome.py — apaga o CACHE dos perfis do Chrome do cofre de logins (dono 17/10/2026: "faça com que isso
limpe automático, já que o Chrome refaz e não compromete"). Só pastas de cache (imagem/script de site, shader, GPU);
NUNCA cookies, "Login Data", "Local Storage", "Preferences" — os logins ficam intactos. Perfil com Chrome aberto
(linha de comando do chrome.exe aponta pra ele) é pulado. Tarefa `LimparCacheChrome`, todo dia 04:30.
"""
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

RAIZES = [Path(r"D:\logins-google\cofre\perfis"), Path(r"D:\logins-google\chrome-profiles")]
CACHES = ["Cache", "Code Cache", "GPUCache", "DawnCache", "DawnGraphiteCache", "DawnWebGPUCache",
          "Service Worker/CacheStorage", "Service Worker/ScriptCache"]
NA_RAIZ = ["GrShaderCache", "ShaderCache", "GraphiteDawnCache", "component_crx_cache", "Crashpad/reports"]
LOG = Path(__file__).resolve().parent / "limpar_cache_chrome.log"


def _abertos():
    r = subprocess.run(["powershell", "-NoProfile", "-Command",
                        "Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" | ForEach-Object { $_.CommandLine }"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return (r.stdout or "").lower()


def _tam(p):
    return sum(f.stat().st_size for f in p.rglob("*") if f.is_file()) if p.exists() else 0


def main():
    abertos, total, pulados = _abertos(), 0, []
    for raiz in RAIZES:
        for perfil in raiz.iterdir() if raiz.exists() else []:
            if not perfil.is_dir() or perfil.is_symlink() or not (perfil / "Local State").exists():
                continue
            if str(perfil).lower() in abertos:
                pulados.append(perfil.name)
                continue
            alvos = [perfil / n for n in NA_RAIZ]
            for sub in [perfil / "Default"] + [d for d in perfil.glob("Profile *") if d.is_dir()]:
                alvos += [sub / c for c in CACHES]
            for a in alvos:
                if a.exists():
                    t = _tam(a)
                    shutil.rmtree(a, ignore_errors=True)
                    total += t - _tam(a)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now():%d/%m %H:%M}] liberou {total / 1e6:.0f} MB; pulados (Chrome aberto): "
                f"{', '.join(pulados) or '-'}\n")
    print(f"liberou {total / 1e6:.0f} MB; pulados: {pulados}")


if __name__ == "__main__":
    main()
