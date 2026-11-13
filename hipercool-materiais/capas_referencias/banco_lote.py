# 03/11 dona: "o sistema de pegar os personagens já começou a funcionar, aí você pode inserir eles nas capas" -> banco
# de mulheres das obras que ainda estão com capa pra fazer/refazer. O vídeo vem do Drive (nuvem.json da obra), um de
# cada vez: baixa -> banco_mulheres (venv_imgutils) -> nomear (D:\veo\venv) -> apaga o vídeo.
#   python banco_lote.py <vid> [<vid> ...]
import json
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).parent
NUVEM = Path(r"D:\hipercool-materiais\animes recap\na_nuvem")
TMP = Path(r"D:\hipercool-materiais\tmp\banco_video")
PY_IMG = r"D:\hipercool-materiais\python\venv_imgutils\Scripts\python.exe"
PY_VEO = r"D:\veo\venv\Scripts\python.exe"
SEM_JANELA = 0x08000000


def log(m):
    from datetime import datetime
    with open(AQUI / "banco_lote.log", "a", encoding="utf-8") as f:
        f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} {m}\n")


def um(vid):
    # 03/11 dona ("personagens de fundo que estão na história"): banco antigo sem homens.json é refeito, para ter
    # o protagonista e os personagens de fundo
    if (AQUI / vid / "indice.json").exists() and (AQUI / vid / "homens.json").exists():
        log(f"{vid}: já tem banco")
        return
    pasta = next(NUVEM.glob(f"{vid}*"), None)
    if not pasta:
        log(f"{vid}: sem pasta na_nuvem")
        return
    drive = json.loads((pasta / "nuvem.json").read_text(encoding="utf-8")).get("drive")
    TMP.mkdir(parents=True, exist_ok=True)
    video = TMP / "video.mp4"
    video.unlink(missing_ok=True)
    r = subprocess.run([r"D:\tools\rclone.exe", "copyto", drive, str(video)], capture_output=True, text=True,
                       creationflags=SEM_JANELA)
    if not video.exists():
        log(f"{vid}: download falhou {r.stderr[-200:]}")
        return
    try:
        # 04/11: KJ5F travou 8 h. Com o PC ocupado, 90 min não bastou para nenhuma obra -> 1 quadro a cada 6 s e no
        # máximo 4 h; passou do tempo = mata a ÁRVORE (o python do venv abre um filho que segurava o video.mp4)
        p = subprocess.Popen([PY_IMG, str(AQUI / "banco_mulheres.py"), str(video), vid, "6"], stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace",
                             creationflags=SEM_JANELA,
                             env={**__import__("os").environ, "HF_HOME": r"D:\caches\huggingface"})
        try:
            saida, _ = p.communicate(timeout=4 * 3600)
        except subprocess.TimeoutExpired:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True, creationflags=SEM_JANELA)
            p.communicate()
            log(f"{vid}: banco passou de 4 h, pulado")
            return
        r = subprocess.CompletedProcess(p.args, p.returncode, saida, "")
        log(f"{vid}: banco -> {(r.stdout or r.stderr).strip().splitlines()[-1:]}")
        if (AQUI / vid / "indice.json").exists():
            r = subprocess.run([PY_VEO, str(AQUI / "nomear.py"), vid, str(pasta / "roteiro.txt")],
                               capture_output=True, text=True, encoding="utf-8", errors="replace",
                               creationflags=SEM_JANELA)
            log(f"{vid}: nomes -> {' | '.join(r.stdout.strip().splitlines())}")
    finally:
        video.unlink(missing_ok=True)


if __name__ == "__main__":
    for v in sys.argv[1:]:
        try:
            um(v)
        except Exception as e:  # noqa: BLE001
            log(f"{v}: erro {type(e).__name__}: {e}")
