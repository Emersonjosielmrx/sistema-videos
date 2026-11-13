"""capas_na_vps.py — coleta de fotos das capas (banco_mulheres.py do chat das CAPAS) na hermes-staging (04/11/2026).

Dona 04/11 (relato do chat das capas): com a CPU do PC1 a 100%, 1 h de vídeo levava > 90 min e as obras eram puladas.
Aqui a VPS (8 núcleos, só Drive) baixa o vídeo da obra, roda o banco_mulheres.py (cópia ajustada pro Linux em
/opt/capas, passo 6) e o resultado volta pra capas_referencias\\<vid>\\ (mulheres/ + homens/ + indice.json + homens.json,
substitui o banco antigo). O nomear.py (visão) roda no PC, como no banco_lote.py. 1 linha por obra no banco_lote.log.

    python capas_na_vps.py KwdNrk4skKg PFbuZNbc6cA ...
"""
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

CAPAS = Path(r"D:\hipercool-materiais\capas_referencias")
NUVEM = Path(r"D:\hipercool-materiais\animes recap\na_nuvem")
PY_VEO = r"D:\veo\venv\Scripts\python.exe"
VPS = "hermes-staging"
RC = "rclone --config /opt/recap_central/rclone.conf"


def log(m):
    with open(CAPAS / "banco_lote.log", "a", encoding="utf-8") as f:
        f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} {m}\n")
    print(m, flush=True)


def ssh(cmd, timeout):
    return subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ServerAliveInterval=60", VPS, cmd],
                          capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)


def uma(vid):
    pasta = next(NUVEM.glob(f"{vid}*"), None)
    if not pasta or not (pasta / "nuvem.json").exists():
        log(f"{vid}: sem pasta na_nuvem (VPS)")
        return
    drive = json.loads((pasta / "nuvem.json").read_text(encoding="utf-8"))["drive"]
    r = ssh(f"cd /opt/capas && rm -rf {vid} && {RC} copyto '{drive}' tmp/{vid}.mp4 && "
            f"venv/bin/python banco_mulheres.py tmp/{vid}.mp4 {vid} 6 2>&1 | tail -3; rm -f tmp/{vid}.mp4; ls {vid}",
            timeout=4 * 3600)
    saida = (r.stdout + r.stderr).strip().splitlines()
    log(f"{vid}: banco (VPS) -> {saida[-4:]}")
    if "indice.json" not in r.stdout and "mulheres" not in r.stdout:
        return
    local = CAPAS / vid
    novo = CAPAS / f"_{vid}_vps"
    shutil.rmtree(novo, ignore_errors=True)
    subprocess.run(["scp", "-q", "-r", f"{VPS}:/opt/capas/{vid}", str(novo)], check=True, timeout=1800)
    for sub in ("mulheres", "homens", "indice.json", "homens.json"):  # substitui o banco antigo (sem homens)
        alvo = local / sub
        if alvo.is_dir():
            shutil.rmtree(alvo, ignore_errors=True)
        elif alvo.exists():
            alvo.unlink()
        if (novo / sub).exists():
            local.mkdir(parents=True, exist_ok=True)
            shutil.move(str(novo / sub), str(alvo))
    shutil.rmtree(novo, ignore_errors=True)
    # 05/11 (chat das capas): sem roteiro.txt na na_nuvem o nomear acha o roteiro sozinho — só passa se existir
    rot = [str(pasta / "roteiro.txt")] if (pasta / "roteiro.txt").exists() else []
    r = subprocess.run([PY_VEO, str(CAPAS / "nomear.py"), vid, *rot], capture_output=True,
                       text=True, encoding="utf-8", errors="replace", creationflags=0x08000000, cwd=str(CAPAS))
    log(f"{vid}: nomes -> {' | '.join(r.stdout.strip().splitlines()[-8:])}")


if __name__ == "__main__":
    for v in sys.argv[1:]:
        try:
            uma(v)
        except Exception as e:  # noqa: BLE001
            log(f"{v}: erro (VPS) {type(e).__name__}: {e}")
