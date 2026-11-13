r"""
PC1 → Kaggle (emersonjosiel649, API oficial): trabalhador do recap longo em segundo plano, sem aba aberta.

  python kaggle_lancar.py conf       # (re)sobe o dataset privado recap-worker-conf com o rclone.conf
  python kaggle_lancar.py lancar     # sobe kaggle_trabalhador.py como kernel CPU+internet e roda (até 12 h)
  python kaggle_lancar.py status     # estado do kernel
  python kaggle_lancar.py manter     # lança de novo se não estiver rodando (pra tarefa agendada)
Uma conta só (termos do Kaggle: 1 por pessoa). Plano: producao/COLAB_RECAP_LONGO.md
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
TMP = AQUI / "_kaggle"
RCLONE = r"D:\tools\rclone.exe"
KAGGLE = Path(sys.executable).with_name("kaggle.exe")
USUARIO = "emersonjosiel"
DATASET = f"{USUARIO}/recap-worker-conf"
KERNEL = f"{USUARIO}/recap-longo"


def _env():
    reg = json.loads(Path(r"D:\projetos-navegador\credential-factory\kaggle_contas.json").read_text(encoding="utf-8"))
    c = reg["emersonjosiel649@gmail.com"]
    (TMP / "cfg").mkdir(parents=True, exist_ok=True)
    return {**os.environ, "KAGGLE_USERNAME": c["username"], "KAGGLE_KEY": c["key"],
            "KAGGLE_CONFIG_DIR": str(TMP / "cfg")}


def kg(*args):
    r = subprocess.run([str(KAGGLE), *args], capture_output=True, text=True, env=_env())
    print((r.stdout + r.stderr).strip()[-1500:], flush=True)
    return r


def conf():
    d = TMP / "conf"
    shutil.rmtree(d, ignore_errors=True)
    d.mkdir(parents=True)
    partes = []
    for remoto in ("manhwa-drive",):
        txt = subprocess.run([RCLONE, "config", "show", remoto], capture_output=True, text=True, check=True).stdout
        partes.append(txt.strip())
    (d / "rclone.conf").write_text("\n\n".join(partes) + "\n", encoding="utf-8")
    (d / "dataset-metadata.json").write_text(json.dumps(
        {"title": "recap-worker-conf", "id": DATASET, "licenses": [{"name": "CC0-1.0"}]}), encoding="utf-8")
    try:
        r = kg("datasets", "create", "-p", str(d))
        if r.returncode != 0 or "already" in (r.stdout + r.stderr).lower():
            kg("datasets", "version", "-p", str(d), "-m", "rclone.conf novo")
    finally:
        shutil.rmtree(d, ignore_errors=True)  # o .conf tem tokens: não fica no disco


def lancar():
    d = TMP / "kernel"
    shutil.rmtree(d, ignore_errors=True)
    d.mkdir(parents=True)
    shutil.copy(AQUI / "kaggle_trabalhador.py", d / "kaggle_trabalhador.py")
    (d / "kernel-metadata.json").write_text(json.dumps(
        {"id": KERNEL, "title": "recap-longo", "code_file": "kaggle_trabalhador.py", "language": "python",
         "kernel_type": "script", "is_private": True, "enable_gpu": False, "enable_internet": True,
         "dataset_sources": [DATASET], "competition_sources": [], "kernel_sources": []}), encoding="utf-8")
    kg("kernels", "push", "-p", str(d))


def status():
    r = kg("kernels", "status", KERNEL)
    return (r.stdout + r.stderr).lower()


if __name__ == "__main__":
    a = sys.argv[1:] or ["status"]
    if a[0] == "conf":
        conf()
    elif a[0] == "lancar":
        lancar()
    elif a[0] == "status":
        status()
    elif a[0] == "manter":
        s = status()
        if "running" not in s and "queued" not in s:
            lancar()
    else:
        print(__doc__)
