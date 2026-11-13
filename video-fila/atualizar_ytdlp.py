"""atualizar_ytdlp.py — mantém o yt-dlp em dia no PC1 e no PC2 (dono 18/10/2026: "devia ter um script pra fazer isso
automaticamente"). O YouTube muda e versão velha leva 403 no download: em 18/10 o PC2 (2026.07.04) falhou 13 Shorts
seguidos enquanto o PC1 (2026.08.19) baixava normal.
Tarefa `AtualizarYtDlp` (05:23 e 17:23, sem janela); log em atualizar_ytdlp.log. Só mexe em pacote que o Python já
tem: o do sistema (de onde sai o comando yt-dlp) e os venvs do recapd.
18/10: edge-tts também — o PC2 com 7.2.8 levava 403 do Bing e um Short ficou 3 h preso na narração (PC1, 7.3.1, ok).
"""
import subprocess
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
LOG = BASE / "atualizar_ytdlp.log"
_SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)
PYTHONS = {
    "pc1": [(r"C:\Users\Haylla\AppData\Local\Programs\Python\Python313\python.exe", ["yt-dlp"]),
            (r"D:\recapd-ambientes\producao\venv\Scripts\python.exe", ["yt-dlp", "edge-tts"])],
    "pc2": [(r"C:\Users\Emerson-IA\AppData\Local\Programs\Python\Python313\python.exe", ["yt-dlp"]),
            (r"C:\recapd-e-animes\venv\Scripts\python.exe", ["yt-dlp", "edge-tts"])],
}
VERSAO = "import sys, importlib.metadata as m; print(m.version(sys.argv[1]))"


def log(msg):
    linha = f"[{datetime.now():%d/%m %H:%M:%S}] {msg}"
    print(linha, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(linha + "\n")


def rodar(host, args, timeout=900):
    cmd = args if host == "pc1" else ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", host,
                                      subprocess.list2cmdline(args)]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=timeout, creationflags=_SEM_JANELA)
    except (OSError, subprocess.TimeoutExpired) as e:
        return 1, f"{type(e).__name__}"
    saida = [l for l in (r.stdout or "").splitlines() + (r.stderr or "").splitlines()
             if l.strip() and "post-quantum" not in l and "store now" not in l and "openssh.com" not in l]
    return r.returncode, (saida[-1] if saida else "")


def main():
    for host, pythons in PYTHONS.items():
        for py, pacotes in pythons:
            for pac in pacotes:
                rc, antes = rodar(host, [py, "-c", VERSAO, pac], timeout=120)
                if rc != 0:
                    log(f"{host} {py}: sem {pac} ou inacessível ({antes[:120]})")
                    continue
                rc, msg = rodar(host, [py, "-m", "pip", "install", "-U", "-q", "--disable-pip-version-check", pac])
                _, depois = rodar(host, [py, "-c", VERSAO, pac], timeout=120)
                if rc != 0:
                    log(f"{host} {py} {pac}: FALHOU atualizar ({antes}) — {msg[:200]}")
                else:
                    log(f"{host} {py} {pac}: {antes} -> {depois}" if antes != depois
                        else f"{host} {py} {pac}: já na última ({depois})")


if __name__ == "__main__":
    main()
