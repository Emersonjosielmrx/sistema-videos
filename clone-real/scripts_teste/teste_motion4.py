# Teste 4 (01/11): isolar a causa do FAILED 13. E = edição simples (sem ref) no vídeo do rapaz (mudo, já no projeto);
# F = edição simples num vídeo SEM pessoa (fofos, mudo).
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, r"D:\projeto-navegador-sem-navegador")
from services.veo_flow.flow_gerar import FlowGerador  # noqa: E402

D = Path(r"D:\tmp_motion\teste")
FOFOS = r"D:\veo\beta\videos\cron_shorts\fofos_e_absurdo_20261029_152421.mp4"
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

with FlowGerador("fabiovideoseducativos") as fg:
    mudo = D / "fofos_mudo.mp4"
    # F = vídeo SEM rosto real: a mulher fictícia (aparencia.png) com zoom lento, 6 s, 720x1280
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", str(D / "aparencia.png"), "-t", "6", "-vf",
                    "scale=1440:2560,zoompan=z='1+0.0015*on':d=1:s=720x1280:fps=24", "-an", "-c:v", "libx264",
                    "-crf", "18", "-pix_fmt", "yuv420p", str(mudo)], check=True)
    vf = fg.f.subir_video(mudo)
    ids = {}
    for nome, vid in (("E", "24ae2461-6876-4ad8-a3ca-a27a0438cf9f"), ("F", vf)):
        try:
            r = fg.pedir(f"Use the generate_video_edit_video tool with Omni Flash, aspect ratio 9:16. Base video: "
                         f"uploaded video {vid}. Edit: add a small red hat on the main subject's head. Keep everything "
                         f"else the same.")
            ids[nome] = r["midias"][0]["media_id"]
            print(nome, "pedido", ids[nome], flush=True)
        except Exception as e:  # noqa: BLE001
            print(nome, "PEDIDO FALHOU", e, flush=True)
    fg.soltar_chrome()
    fim = time.time() + 900
    while ids and time.time() < fim:
        time.sleep(20)
        for nome, mid in list(ids.items()):
            falha = fg.f.falha_geracao(mid)
            if falha:
                print(nome, "FALHOU", falha, flush=True)
                ids.pop(nome)
                continue
            try:
                arq, tipo, _ = fg.f.baixar(mid, D / f"edit_{nome}.mp4")
                if (tipo or "").startswith("video"):
                    print(nome, "OK", arq, flush=True)
                    ids.pop(nome)
            except Exception:  # noqa: BLE001
                pass
    print("pendentes", ids, "creditos", fg.f.creditos(), flush=True)
