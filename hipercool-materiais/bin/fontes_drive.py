"""fontes_drive.py — vídeos-fonte do anime (D:\\hipercool-materiais\\anime\\<id>_<título>\\source.*) vão pro Drive depois
de usados; voltam sozinhos se precisar (dona 23/10/2026: "as fontes também, com script pra baixar automaticamente na
hora, sem precisar de IA"). Volta: anime_fetch.download_video chama trazer(pasta) antes de ir ao YouTube.

Fonte completa (source.mp4/.mkv/.webm) parada há DIAS dias -> moveto Drive (confere e só então apaga do PC).
Sobra de download que não terminou (source.temp.*, source.fNNN.*, *.part, *.ytdl) parada há DIAS dias -> apagada
(não serve pra nada: o yt-dlp recomeça do zero).

    python fontes_drive.py subir [--simular]
"""
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import registro_drive  # noqa: E402

ANIME = Path(r"D:\hipercool-materiais\anime")
DRIVE = "manhwa-drive:videos-backup/hipercool-materiais/anime"
RCLONE = r"D:\tools\rclone.exe"
DIAS = 3
FONTE = re.compile(r"^source\.(mp4|mkv|webm)$", re.I)
SOBRA = re.compile(r"^source\.(temp\.|f\d+\.).+|.+\.(part|ytdl)$", re.I)


def _rclone(*args, timeout=3600):
    return subprocess.run([RCLONE, *args, "--retries", "3"], capture_output=True, text=True, timeout=timeout,
                          creationflags=0x08000000)


def trazer(pasta):
    """Traz do Drive a fonte desta pasta (mesmo nome de pasta). Path do arquivo ou None. Uma consulta ao Drive."""
    pasta = Path(pasta)
    try:
        r = _rclone("lsf", f"{DRIVE}/{pasta.name}", "--files-only", timeout=120)
        nome = next((n.strip() for n in r.stdout.splitlines() if FONTE.match(n.strip())), None)
        if not nome:
            return None
        pasta.mkdir(parents=True, exist_ok=True)
        _rclone("copyto", f"{DRIVE}/{pasta.name}/{nome}", str(pasta / nome))
        return pasta / nome if (pasta / nome).exists() else None
    except Exception:  # noqa: BLE001 — sem Drive: o download normal segue
        return None


def mover(f, quem="fontes_drive.py"):
    """moveto de um arquivo de ANIME pro mesmo caminho no Drive (confere e só então apaga do PC) e anota no _NO_DRIVE.md
    da pasta. True = saiu do PC. 25/10: o limpar_source.py usa isto em vez de apagar a fonte."""
    f = Path(f)
    tam = f.stat().st_size
    destino = f"{DRIVE}/{f.relative_to(ANIME).as_posix()}"
    r = _rclone("moveto", str(f), destino, timeout=600 + tam / 80e3)
    if r.returncode == 0 and not f.exists():
        registro_drive.anotar(f, destino, tam, quem)
        return True
    print(f"fontes_drive: {f.parent.name}/{f.name} não subiu ({(r.stderr or '')[-120:]})", flush=True)
    return False


def subir(simular=False):
    lim, sub, apag = time.time() - DIAS * 86400, 0, 0
    for pasta in sorted(p for p in ANIME.iterdir() if p.is_dir()):
        arqs = [f for f in pasta.rglob("*") if f.is_file()]
        parada = bool(arqs) and max(f.stat().st_mtime for f in arqs) <= lim  # pasta inteira sem mexer há DIAS dias
        for f in arqs:
            if f.stat().st_mtime > lim:
                continue
            if SOBRA.match(f.name):
                apag += f.stat().st_size
                if not simular:
                    f.unlink(missing_ok=True)
            # fonte: sempre que parada; os outros vídeos (clip_N, final_anime_short, lang_*/source): só com a pasta
            # inteira parada (é material de trabalho; a postagem usa a cópia dela em "animes recap")
            elif (FONTE.match(f.name) and f.parent == pasta) or (parada and f.suffix.lower() in (".mp4", ".mkv", ".webm")):
                tam = f.stat().st_size
                if simular:
                    sub += tam
                    continue
                if mover(f):
                    sub += tam
    print(f"fontes_drive: {sub / 1e9:.1f} GB {'iriam' if simular else 'foram'} pro Drive; "
          f"{apag / 1e9:.1f} GB de sobra de download {'seriam apagados' if simular else 'apagados'}", flush=True)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if sys.argv[1:2] == ["subir"]:
        subir("--simular" in sys.argv)
    else:
        print(__doc__)
