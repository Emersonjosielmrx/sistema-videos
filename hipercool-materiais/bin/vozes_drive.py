"""vozes_drive.py — o .index das vozes RVC paradas fica no Drive; volta sozinho na hora de usar (dona 23/10/2026:
"pode mandar as vozes pro Drive, só deixe scripts pra baixar automaticamente na hora de fazer, sem precisar de IA").

O .index é o grosso (8,7 GB de 14 GB). O <voz>.pth FICA no PC: é ele que marca "modelo pronto" pra fila/vigia/Kaggle
(sem ele a voz seria treinada de novo). garantir(voz) traz o .index se faltar e anota o uso (<voz>/.ultimo_uso);
subir_paradas() manda pro Drive o .index de quem não é usada há DIAS dias e não foi treinada há pouco.

    python vozes_drive.py subir [--simular]   # manda as paradas
    python vozes_drive.py garantir <voz>      # traz uma voz de volta
O vigia geral chama "subir" 1x por dia (junto da faxina_disco).
"""
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import registro_drive  # noqa: E402

VOZES = Path(r"D:\hipercool-materiais\models\rvc\vozes")
DRIVE = "manhwa-drive:videos-backup/hipercool-materiais/models/rvc/vozes"
RCLONE = r"D:\tools\rclone.exe"
DIAS = 7          # sem uso há mais que isso: o .index vai pro Drive
NOVA_DIAS = 14    # treinada há menos que isso: fica (a fila/testes ainda usam)
NO_DRIVE = ".index_no_drive"  # aviso na pasta: o .index está no Drive


def _rclone(*args, timeout=3600):
    return subprocess.run([RCLONE, *args, "--retries", "3"], capture_output=True, text=True, timeout=timeout,
                          creationflags=0x08000000)


def marcar_uso(voz):
    try:
        (VOZES / voz / ".ultimo_uso").write_text(str(time.time()), encoding="utf-8")
    except OSError:
        pass


def garantir(voz):
    """Traz o <voz>.index do Drive se não estiver no PC. True = está no PC. Sempre anota o uso."""
    pasta = VOZES / voz
    idx = pasta / f"{voz}.index"
    marcar_uso(voz)
    if idx.exists():
        return True
    try:
        _rclone("copyto", f"{DRIVE}/{voz}/{voz}.index", str(idx))
    except Exception as e:  # noqa: BLE001
        print(f"vozes_drive: {voz}.index não veio do Drive ({type(e).__name__})", flush=True)
    if idx.exists():
        (pasta / NO_DRIVE).unlink(missing_ok=True)
        print(f"vozes_drive: {voz}.index voltou do Drive", flush=True)
    return idx.exists()


def _ultimo_uso(pasta):
    try:
        return float((pasta / ".ultimo_uso").read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return 0.0


def subir_paradas(simular=False, usadas_extra=()):
    """Manda pro Drive (moveto: confere e só então apaga) o .index de quem está parada. usadas_extra: vozes que não
    podem subir agora (ex.: vistas nos logs recentes, no 1º uso deste script, que ainda não tinha .ultimo_uso)."""
    agora, total, n = time.time(), 0, 0
    for pasta in sorted(p for p in VOZES.iterdir() if p.is_dir()):
        voz = pasta.name
        idx, pth = pasta / f"{voz}.index", pasta / f"{voz}.pth"
        if not idx.exists() or not pth.exists() or voz in usadas_extra:
            continue
        if agora - pth.stat().st_mtime < NOVA_DIAS * 86400 or agora - _ultimo_uso(pasta) < DIAS * 86400:
            continue
        tam = idx.stat().st_size
        if simular:
            total, n = total + tam, n + 1
            continue
        r = _rclone("moveto", str(idx), f"{DRIVE}/{voz}/{voz}.index", timeout=600 + tam / 80e3)
        if r.returncode == 0 and not idx.exists():
            (pasta / NO_DRIVE).write_text("o .index está no Drive; vozes_drive.garantir traz de volta\n", encoding="utf-8")
            registro_drive.anotar(idx, f"{DRIVE}/{voz}/{voz}.index", tam, "vozes_drive.py")
            total, n = total + tam, n + 1
        else:
            print(f"vozes_drive: {voz}.index não subiu ({(r.stderr or '')[-150:]}) — fica no PC", flush=True)
    print(f"vozes_drive: {n} .index {'seriam enviados' if simular else 'no Drive'} ({total / 1e9:.1f} GB)", flush=True)
    return total


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    a = sys.argv[1:]
    if a[:1] == ["garantir"] and len(a) > 1:
        print(garantir(a[1]))
    elif a[:1] == ["subir"]:
        subir_paradas("--simular" in a)
    else:
        print(__doc__)
