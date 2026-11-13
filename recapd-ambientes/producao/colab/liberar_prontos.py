"""liberar_prontos.py — dona 27/10 ("põe no Drive que estamos ficando sem espaço"): esvazia a pasta de revisão
D:\\hipercool-materiais\\recap-longos-prontos. Cada vídeo já tem o original no Drive (nuvem.json da ficha); a versão
_SEM_NOMES (feita aqui pelo limpar_nomes.py) sobe no LUGAR do original com nome. Só apaga a cópia local depois de
conferir o tamanho no Drive. Fica o mais novo pra dona assistir.

    python liberar_prontos.py [--ver]
"""
import json
import subprocess
import sys
from pathlib import Path

PASTA = Path(r"D:\hipercool-materiais\recap-longos-prontos")
FICHAS = Path(r"D:\hipercool-materiais\animes recap\na_nuvem")
RCLONE = r"D:\tools\rclone.exe"
SEM_JANELA = 0x08000000 if sys.platform == "win32" else 0


def rc(*a):
    r = subprocess.run([RCLONE, *a], capture_output=True, text=True, timeout=7200, creationflags=SEM_JANELA)
    if r.returncode:
        raise RuntimeError(r.stderr[-300:])
    return r.stdout


def tamanho_drive(remoto):
    try:
        return json.loads(rc("lsjson", remoto))[0]["Size"]
    except (RuntimeError, ValueError, IndexError, KeyError):
        return None


def main(ver=False):
    videos = sorted(PASTA.glob("*.mp4"), key=lambda p: p.stat().st_mtime)
    if not videos:
        return
    manter = videos[-1]  # o mais novo fica pra dona assistir
    limpos = {v.name.split("TESTE_NARRADORES_")[-1][:11] for v in videos if v.stem.endswith("_SEM_NOMES")}
    for v in videos:
        if v == manter:
            continue
        vid = v.name.split("TESTE_NARRADORES_")[-1][:11] if "TESTE_NARRADORES_" in v.name else v.name[17:28]
        ficha = next(iter(FICHAS.glob(f"{vid}*")), None)
        try:
            drive = json.loads((ficha / "nuvem.json").read_text(encoding="utf-8"))["drive"]
        except (TypeError, OSError, ValueError, KeyError):
            print(f"sem ficha/nuvem.json: {v.name} — fica", flush=True)
            continue
        if v.stem.endswith("_SEM_NOMES"):
            print(f"{'(ver) ' if ver else ''}sobe no lugar do original: {v.name}", flush=True)
            if not ver:
                rc("copyto", str(v), drive)
        elif vid in limpos:
            print(f"{'(ver) ' if ver else ''}original com nome (a limpa substitui): {v.name}", flush=True)
            if not ver:
                v.unlink()
            continue
        if ver:
            print(f"(ver) apagaria se o Drive conferir: {v.name}", flush=True)
            continue
        if tamanho_drive(drive) == v.stat().st_size:
            v.unlink()
            print(f"apagado (Drive conferiu): {v.name}", flush=True)
        else:
            print(f"Drive NÃO conferiu, fica: {v.name}", flush=True)


if __name__ == "__main__":
    main(ver="--ver" in sys.argv)
