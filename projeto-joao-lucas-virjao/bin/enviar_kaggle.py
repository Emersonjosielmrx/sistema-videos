r"""Projeto João Lucas Virjão: manda UM vídeo pra fila do recap longo no Kaggle, no modo voz original.
O PC NÃO fala com o Kaggle: o pedido vai pra central da hermes-prod (igual ao colab\cliente.enviar), que põe na fila;
cada conta Kaggle só sai pela saída fixa dela (regra do banimento 02/11).
    python enviar_kaggle.py <source.mp4> "<titulo>" <video_id> [urgente]
urgente = pid 20261027_0001xx: o trabalhador pega o 1º pedido livre por NOME, então este passa na frente."""
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

VPS = "hermes-prod"
VPS_ENTRADA = "/opt/recap_central/entrada"
SCP = r"C:\Program Files\Git\usr\bin\scp.exe"
SSH = r"C:\Program Files\Git\usr\bin\ssh.exe"
CREATE_NO_WINDOW = 0x08000000

video, titulo, vid = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
urgente = len(sys.argv) > 4 and sys.argv[4] == "urgente"
pid = f"20261027_000100_{vid}" if urgente else f"{datetime.now():%Y%m%d_%H%M%S}_{vid}"
remoto = f"{VPS_ENTRADA}/{pid}"
ssh = [SSH, "-o", "BatchMode=yes", "-o", "ConnectTimeout=20", VPS]
run = lambda c, t: subprocess.run(c, check=True, capture_output=True, timeout=t, creationflags=CREATE_NO_WINDOW)  # noqa: E731

pedido = {"titulo": titulo, "enviado": datetime.now().isoformat(timespec="seconds"),
          "projeto": "joao-lucas-virjao", "url": f"https://www.youtube.com/watch?v={vid}",
          "longo_override": {"voz_original": True}}
tmp = video.with_name("_pedido.json")
tmp.write_text(json.dumps(pedido, ensure_ascii=False), encoding="utf-8")
run(ssh + [f"mkdir -p {remoto}"], 120)
run([SCP, "-q", "-o", "BatchMode=yes", str(video), f"{VPS}:{remoto}/source.mp4"], 7200)
run([SCP, "-q", "-o", "BatchMode=yes", str(tmp), f"{VPS}:{remoto}/pedido.json"], 300)
run(ssh + [f"touch {remoto}/enviado.ok"], 120)
tmp.unlink()
estado = Path(__file__).resolve().parent.parent / "pedidos.json"
lista = json.loads(estado.read_text(encoding="utf-8")) if estado.exists() else []
lista.append({"pid": pid, "vid": vid, "titulo": titulo, "enviado": pedido["enviado"]})
estado.write_text(json.dumps(lista, ensure_ascii=False, indent=1), encoding="utf-8")
print(pid)
