r"""publicar.py — manda site\, nginx.conf e stack.yml para a VPS 157 (ssh hermes-bloqueio, /opt/landings-produtos) e
sobe/atualiza a stack "landings" no Swarm (nginx atrás do Traefik). Rodar depois do gerar.py.

    python publicar.py
"""
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
VPS = "hermes-bloqueio"
DEST = "/opt/landings-produtos"


def run(args, **kw):
    print("$", " ".join(args) if isinstance(args, list) else args, flush=True)
    r = subprocess.run(args, **kw)
    if r.returncode:
        sys.exit(f"falhou ({r.returncode})")


def main():
    run(["ssh", VPS, f"mkdir -p {DEST}"])
    tar = subprocess.Popen(["tar", "-C", str(BASE), "-cf", "-", "site", "nginx.conf", "stack.yml"], stdout=subprocess.PIPE)
    run(["ssh", VPS, f"rm -rf {DEST}/site && tar -C {DEST} -xf -"], stdin=tar.stdout)
    run(["ssh", VPS, f"docker stack deploy -c {DEST}/stack.yml landings && docker service update --force --quiet "
                     "landings_web >/dev/null; docker service ls --filter name=landings_web"])


if __name__ == "__main__":
    main()
