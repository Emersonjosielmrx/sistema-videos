r"""
PC1 → VPS: trabalhador do recap longo num contêiner Docker (mesmo kaggle_trabalhador.py), pegando da mesma fila.
Limite de CPU/memória pra não derrubar o que já roda na VPS; reinicia sozinho (--restart unless-stopped).

  python vps_lancar.py <host_ssh> <cpus> [memoria]     ex.: hermes-staging 4 8g
  python vps_lancar.py <host_ssh> parar
  python vps_lancar.py <host_ssh> log
Plano: producao/COLAB_RECAP_LONGO.md
"""
import subprocess
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RCLONE = r"D:\tools\rclone.exe"
PASTA = "/opt/recap_worker"
NOME = "recap_worker"
IMAGEM = "python:3.13-slim"
PIP = "edge-tts==7.3.1 opencv-python-headless psutil pydub soundfile numpy pillow requests"


# o ssh do Windows (OpenSSH) trava sem console; o do Git Bash responde em 3 s (25/10)
SSH = r"C:\Program Files\Git\usr\bin\ssh.exe"
SCP = r"C:\Program Files\Git\usr\bin\scp.exe"


def ssh(host, cmd, check=True):
    r = subprocess.run([SSH, "-o", "BatchMode=yes", "-o", "ConnectTimeout=20", host, cmd],
                       capture_output=True, text=True, timeout=600, stdin=subprocess.DEVNULL)
    if check and r.returncode != 0:
        raise RuntimeError(f"{host}: {r.stderr[-400:]}")
    return r.stdout


def scp(host, origem, destino):
    origem = subprocess.run([r"C:\Program Files\Git\usr\bin\cygpath.exe", "-u", str(origem)], capture_output=True, text=True).stdout.strip() or str(origem)
    subprocess.run([SCP, "-q", "-o", "BatchMode=yes", origem, f"{host}:{destino}"], check=True, timeout=600, stdin=subprocess.DEVNULL)


def lancar(host, cpus, memoria="8g"):
    ssh(host, f"mkdir -p {PASTA} && chmod 700 {PASTA}")
    scp(host, AQUI / "kaggle_trabalhador.py", f"{PASTA}/kaggle_trabalhador.py")
    conf = "\n\n".join(subprocess.run([RCLONE, "config", "show", r], capture_output=True, text=True,
                                      check=True).stdout.strip() for r in ("manhwa-drive",)) + "\n"
    with tempfile.NamedTemporaryFile("w", suffix=".conf", delete=False, encoding="utf-8", newline="\n") as f:
        f.write(conf)
    try:
        scp(host, f.name, f"{PASTA}/rclone.conf")
    finally:
        Path(f.name).unlink()  # tem tokens
    ssh(host, f"chmod 600 {PASTA}/rclone.conf; docker rm -f {NOME} 2>/dev/null; true", check=False)
    nome_trab = f"vps_{host.replace('hermes-', '')}"
    cmd = (f"apt-get update -qq && apt-get install -y -qq ffmpeg fonts-dejavu-core >/dev/null && "
           f"pip install -q {PIP} && python -u /w/kaggle_trabalhador.py")
    ssh(host, f"docker run -d --name {NOME} --restart unless-stopped --cpus={cpus} --memory={memoria} "
              f"-v {PASTA}:/w -e TRAB_BASE=/w -e TRAB_NOME={nome_trab} -e TRAB_LIMITE_H=0 "
              f"-e RCLONE_CONF=/w/rclone.conf {IMAGEM} bash -c '{cmd}'")
    print(f"{host}: {NOME} rodando ({cpus} CPUs, {memoria}) como {nome_trab}", flush=True)


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) >= 2 and a[1] == "parar":
        ssh(a[0], f"docker rm -f {NOME}", check=False)
    elif len(a) >= 2 and a[1] == "log":
        print(ssh(a[0], f"docker logs --tail 40 {NOME} 2>&1", check=False))
    elif len(a) >= 2:
        lancar(a[0], a[1], a[2] if len(a) > 2 else "8g")
    else:
        print(__doc__)
