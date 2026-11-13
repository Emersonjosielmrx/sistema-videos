"""limpar_nomes.py — apaga (delogo) o nome do narrador na legenda dos longos de revezamento renderizados ANTES do conserto
de 26/10 22:20 (dona 27/10: "aproveitar os vídeos feitos, não gosto de desperdiçar"). A versão limpa sai ao lado:
<nome>_SEM_NOMES.mp4. Fica rodando (tarefa/fundo) e pega cada vídeo novo que chega na pasta de acompanhamento.
Os renderizados depois do conserto não têm nome — são pulados.

    python limpar_nomes.py [--uma-vez]
"""
import json
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import juri_longo  # noqa: F401,E402  (sem_janela)

PASTA = Path(r"D:\hipercool-materiais\recap-longos-prontos")
FICHAS = Path(r"D:\hipercool-materiais\animes recap\na_nuvem")
CONSERTO = datetime.fromisoformat("2026-10-27T01:20:00+00:00")
FILTRO = "delogo=x=420:y=560:w=440:h=40"  # faixa do nome em 1280x720 (medida em quadros reais 26/10)


def precisa(mp4):
    if "SEM_NOMES" in mp4.name or mp4.with_name(mp4.stem + "_SEM_NOMES.mp4").exists():
        return False
    pid = mp4.name.split("TESTE_NARRADORES_")[-1][:11]
    ficha = next(FICHAS.glob(f"{pid}*"), None)
    if not ficha or not (ficha / "render.json").exists():
        return False
    r = json.loads((ficha / "render.json").read_text(encoding="utf-8"))
    if not r.get("vozes_lista"):
        return False  # voz única: sem nome na legenda
    inicio = datetime.fromisoformat(r["fim"]) - timedelta(seconds=int(r.get("segundos") or 0))
    return inicio < CONSERTO


def limpar(mp4):
    saida = mp4.with_name(mp4.stem + "_SEM_NOMES.mp4")
    tmp = saida.with_suffix(".parcial.mp4")
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-threads", "2", "-i", str(mp4), "-vf", FILTRO, "-c:v", "libx264",
                        "-preset", "veryfast", "-crf", "20", "-threads", "2", "-c:a", "copy", str(tmp)],
                       capture_output=True, text=True)
    if r.returncode == 0 and tmp.exists():
        tmp.replace(saida)
        print(f"[{datetime.now():%H:%M}] limpo: {saida.name}", flush=True)
    else:
        tmp.unlink(missing_ok=True)
        print(f"[{datetime.now():%H:%M}] FALHOU {mp4.name}: {r.stderr[-200:]}", flush=True)


if __name__ == "__main__":
    while True:
        for f in sorted(PASTA.glob("*TESTE_NARRADORES*.mp4")):
            if ".parcial" not in f.name and precisa(f):
                limpar(f)
        if "--uma-vez" in sys.argv:
            break
        time.sleep(600)
