r"""Projeto João Lucas Virjão: espera o pedido do Kaggle ficar pronto, recolhe igual ao alimentador do recap (vídeo pro
Drive + ficha em animes recap\na_nuvem) SEM baixar de novo nem reescrever roteiro, guarda uma cópia em
prontos\ e chama o postar_quando_pronto.py (postagem SEMPRE agendada pelo postar_longos, respeitando limites).
    pythonw recolher_e_postar.py <pid> <video_id> "<titulo>"      log: ..\recolher.log"""
import json
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

PROJ = Path(__file__).resolve().parent.parent
COLAB = Path(r"D:\recapd-ambientes\producao\colab")
sys.path.insert(0, str(COLAB))
import cliente  # noqa: E402

LOG = PROJ / "recolher.log"
pid, vid, titulo = sys.argv[1], sys.argv[2], sys.argv[3]


def log(m):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now():%d/%m %H:%M}] {pid}: {m}\n")


log("esperando pronto.json")
pasta = f"{cliente.FILA}/{pid}"
fim, pronto = time.time() + 20 * 3600, None
while time.time() < fim:
    pronto = cliente._ler_json(f"{pasta}/pronto.json")
    erro = None if pronto else cliente._ler_json(f"{pasta}/erro.json")
    if pronto or erro:
        break
    time.sleep(120)
if not pronto:
    log(f"SEM PRONTO (erro ou 20 h): {str(erro)[:600] if erro else ''}")
    try:
        cliente._rc("copyto", f"{pasta}/pipeline.log", str(PROJ / "trabalho" / f"{pid}_pipeline.log"))
    except RuntimeError:
        pass
    raise SystemExit(1)
log(f"pronto por {pronto.get('por')} em {pronto.get('segundos')} s")
aa = cliente._projeto()
nome = f"{vid}_{aa._slug(titulo)}"
work = aa.BASE / nome
work.mkdir(parents=True, exist_ok=True)
p = {"vid": vid, "titulo": titulo, "nome": nome, "url": f"https://www.youtube.com/watch?v={vid}", "work": work,
     "video": work / "source.mp4", "roteiro": work / "roteiro.txt"}
final = work / "final_anime_deitado.mp4"
cliente.baixar_final(pid, final)
shutil.copy2(final, PROJ / "prontos" / f"{nome}.mp4")
try:
    cliente._rc("copyto", f"{pasta}/pipeline.log", str(PROJ / "trabalho" / f"{pid}_pipeline.log"))
except RuntimeError:
    pass
cliente.guardar_cortes(pid, nome)
cliente.publicar_drive(p, final, f"{pronto.get('por', 'kaggle')} (voz original)")
ficha = aa.ANIMES_FICHAS / nome
(ficha / "render.json").write_text(json.dumps(pronto, ensure_ascii=False, indent=1), encoding="utf-8")
cliente.limpar(pid)
log(f"ficha no Drive: {nome} — chamando postar_quando_pronto")
subprocess.Popen([r"D:\recapd-ambientes\producao\venv\Scripts\pythonw.exe", "-X", "utf8",
                  str(COLAB / "postar_quando_pronto.py"), vid, "36"], cwd=str(COLAB), creationflags=0x08000000)
