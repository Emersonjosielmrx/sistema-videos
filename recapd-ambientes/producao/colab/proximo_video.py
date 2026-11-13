"""29/10 dona: "esse é o próximo vídeo <url>" — faz o longo com tudo e posta sozinho, sem depender do chat:
  1. cliente.preparar (baixa, corta a intro do parceiro, roteiro) + cliente.enviar (narradores pelos grupos);
  2. adiantar_pedido.py: o pedido passa na frente dos que estão esperando na fila;
  3. espera o pronto.json e faz o que o esperar_e_publicar.py faz (cortes, Drive, ficha);
  4. postar_quando_pronto.py: posta (agendado) com ele na frente da fila.
    pythonw proximo_video.py <url>     log: proximo_video.log"""
import subprocess
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
PYW = r"D:\recapd-ambientes\producao\venv\Scripts\pythonw.exe"
LOG = AQUI / "proximo_video.log"
url = sys.argv[1]


def log(m):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now():%d/%m %H:%M}] {m}\n")


def solto(*args):
    subprocess.Popen([PYW, "-X", "utf8", *args], cwd=str(AQUI), creationflags=0x08000000 | 0x00000008)


try:
    import cliente
    log(f"começou {url}")
    p = cliente.preparar(url)
    pid = cliente.enviar(p["work"], p["video"], p["roteiro"], p["titulo"])
    vid = p["nome"][:11]  # id do YouTube tem 11 letras e pode ter "_" (G1_iPga6nLg)
    log(f"enviado {pid} ({p['nome']}) — adiantando na fila e ligando o vigia da postagem")
    solto(str(AQUI / "adiantar_pedido.py"), pid)
    solto(str(AQUI / "postar_quando_pronto.py"), vid, "60")
    pasta = f"{cliente.FILA}/{pid}"
    fim = time.time() + 30 * 3600
    pronto = None
    while time.time() < fim:
        pronto = cliente._ler_json(f"{pasta}/pronto.json")
        if pronto or cliente._ler_json(f"{pasta}/erro.json"):
            break
        time.sleep(120)
    if not pronto:
        raise SystemExit(f"{pid}: sem pronto.json (erro ou 30 h)")
    final = p["work"] / "final_anime_deitado.mp4"
    cliente.baixar_final(pid, final)
    cliente.guardar_cortes(pid, p["nome"])
    cliente.publicar_drive(p, final, f"{pronto.get('por', 'kaggle')} (proximo_video)")
    ficha = cliente._projeto().ANIMES_FICHAS / p["nome"]
    import json
    (ficha / "render.json").write_text(json.dumps(pronto, ensure_ascii=False, indent=1), encoding="utf-8")
    cliente._rc("copyto", f"{pasta}/pipeline.log", str(ficha / "pipeline.log"))
    cliente.limpar(pid)
    log(f"pronto e no Drive: {p['nome']} — o vigia posta")
except BaseException:
    log("MORREU:\n" + traceback.format_exc())
    raise
