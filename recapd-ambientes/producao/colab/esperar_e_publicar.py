"""29/10: espera um pedido da fila ficar pronto e faz o que o alimentador faz ao recolher (cortes do longo guardados,
vídeo pro Drive, render.json e pipeline.log na ficha) — pra pedido refeito por refazer_pedido.py.
    python esperar_e_publicar.py <url> <pid>"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cliente  # noqa: E402

url, pid = sys.argv[1], sys.argv[2]
p = cliente.preparar(url)
pasta = f"{cliente.FILA}/{pid}"
fim = time.time() + 14 * 3600
pronto = None
while time.time() < fim:
    pronto = cliente._ler_json(f"{pasta}/pronto.json")
    if pronto or cliente._ler_json(f"{pasta}/erro.json"):
        break
    time.sleep(60)
if not pronto:
    raise SystemExit(f"{pid}: sem pronto.json (erro ou 14 h)")
final = p["work"] / "final_anime_deitado.mp4"
cliente.baixar_final(pid, final)
log = p["work"] / "_pipeline.log"
try:
    cliente._rc("copyto", f"{pasta}/pipeline.log", str(log))
except RuntimeError:
    pass
cliente.guardar_cortes(pid, p["nome"])
cliente.publicar_drive(p, final, f"{pronto.get('por', 'kaggle')} (emersonjosiel649)")
ficha = cliente._projeto().ANIMES_FICHAS / p["nome"]
(ficha / "render.json").write_text(json.dumps(pronto, ensure_ascii=False, indent=1), encoding="utf-8")
cliente._rc("copyto", f"{pasta}/pipeline.log", str(ficha / "pipeline.log"))
cliente.limpar(pid)
print("pronto e no Drive:", p["nome"], flush=True)
