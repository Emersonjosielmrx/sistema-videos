r"""postar_quando_pronta.py — 12/11 dona: "Medieval 13 tem que postar já público e me avisar assim que postar".
Tarefa PostarMedieval13 de 5 em 5 min: se a ficha do vídeo apareceu pronta (na_nuvem/<id>*) e ainda não foi postada,
posta NA HORA (postar_longos --so: sem intervalo VIP; LONGOS_POR_DIA alto) — sai público (publicar_ja.json) com a capa
reserva da série e o aviso 🔥 no Telegram. Postado = a tarefa se apaga sozinha.

    pythonw postar_quando_pronta.py PReloN5HWSI
"""
import json
import os
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
FICHAS = Path(r"D:\hipercool-materiais\animes recap\na_nuvem")


def main(vid, tarefa):
    est = json.loads((AQUI / "longos_postados.json").read_text(encoding="utf-8"))
    if any(x.get("nome", "").startswith(vid) for x in est.get("postados", [])):
        subprocess.run(["schtasks", "/delete", "/tn", tarefa, "/f"], capture_output=True)
        return
    if not any(d.name.startswith(vid) and (d / "nuvem.json").exists() for d in FICHAS.iterdir()):
        return
    # 13/11: a 13 e a 15 travaram por disco ("sem espaço": vídeo de 5-6 GB + 6 GB de folga). Antes de postar a série,
    # se o D: tiver menos de SERIE_DISCO_MIN_GB (13), manda pro Drive a reserva de Shorts que passa de 7 dias.
    import shutil
    if shutil.disk_usage("D:\\").free / 1e9 < float(os.environ.get("SERIE_DISCO_MIN_GB", "13")):
        subprocess.run([r"D:\hipercool-videos\venv\Scripts\python.exe",
                        r"D:\hipercool-materiais\comum\reserva_shorts_drive.py"], timeout=3000, creationflags=0x08000000)
    env = dict(os.environ, LONGOS_POR_DIA="9", PYTHONIOENCODING="utf-8")
    subprocess.run([str(AQUI.parent / "venv" / "Scripts" / "python.exe"), "-X", "utf8", str(AQUI / "postar_longos.py"),
                    "--so", vid], cwd=str(AQUI), env=env, creationflags=0x08000000)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "PostarMedieval13")
