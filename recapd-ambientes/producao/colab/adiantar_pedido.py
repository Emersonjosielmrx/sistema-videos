"""29/10 (dona: "passa o Simples Pastor pra frente"): o trabalhador pega o 1º pedido LIVRE da fila em ordem de nome
(data). Pra adiantar um pedido, os que estão na frente ganham a marca em_andamento_SEGURADO.json (o trabalhador
pula pedido com qualquer em_andamento*) e, assim que o pedido escolhido começar, as marcas saem e a fila volta ao normal.
    python adiantar_pedido.py <pid_que_vai_primeiro>"""
import json
import subprocess
import sys
import time
from datetime import datetime

RC = r"D:\tools\rclone.exe"
FILA = "manhwa-drive:colab_recap/fila"
MARCA = "em_andamento_SEGURADO.json"
LOG = r"D:\recapd-ambientes\producao\colab\adiantar_pedido.log"


def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now():%d/%m %H:%M}] {msg}\n")


def lsf(caminho, *extra):
    return [x.rstrip("/") for x in subprocess.run([RC, "lsf", caminho, *extra], capture_output=True, text=True,
                                                  creationflags=0x08000000).stdout.split()]


alvo = sys.argv[1]
segurados = []
for pid in sorted(lsf(FILA, "--dirs-only")):
    if pid >= alvo:
        break
    arqs = set(lsf(f"{FILA}/{pid}"))
    if "pedido.json" in arqs and not ({"pronto.json", "erro.json"} & arqs) and not any(
            a.startswith("em_andamento") for a in arqs):
        subprocess.run([RC, "rcat", f"{FILA}/{pid}/{MARCA}"], input=json.dumps(
            {"por": "SEGURADO", "motivo": f"dona adiantou {alvo}", "desde": datetime.now().isoformat()}).encode(),
            creationflags=0x08000000)
        segurados.append(pid)
log(f"segurados até {alvo} começar: {segurados}")
for _ in range(24 * 30):  # até 24 h
    if any(a.startswith("em_andamento") for a in lsf(f"{FILA}/{alvo}")):
        break
    time.sleep(120)
for pid in segurados:
    subprocess.run([RC, "deletefile", f"{FILA}/{pid}/{MARCA}"], creationflags=0x08000000)
log(f"{alvo} começou (ou passou 24 h) — marcas tiradas de {segurados}")
