# Motion Sync com vídeo REAL do dono (dono_1.mp4, 8,1 s, propaganda followupia) — 01/11
# K = o próprio dono com outra roupa/cenário (imagem gerada no Nano Banana a partir de um quadro dele)
# L = a ruiva fictícia (aparencia.png) fazendo os gestos dele
import subprocess
import sys
import traceback
from pathlib import Path

sys.path.insert(0, r"D:\projeto-navegador-sem-navegador")
from services.veo_flow.flow_gerar import FlowGerador  # noqa: E402

D = Path(r"D:\tmp_motion\teste\dono")
D.mkdir(exist_ok=True)
VID = r"D:\postador-de-videos\remotion\trabalhos\followupia_ia_20261029_182908\public\dono_1.mp4"
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "1", "-i", VID, "-frames:v", "1", str(D / "quadro_dono.jpg")],
               check=True)

with FlowGerador("fabiovideoseducativos") as fg:
    try:
        fg.imagem("Same man from the reference photo (same face, glasses, beard and hair), now wearing an elegant navy "
                  "blue suit with white shirt, standing at a large solar power plant with rows of solar panels under a "
                  "sunny blue sky, waist-up, looking at the camera, photorealistic, vertical.",
                  D / "dono_terno_usina.png", refs=[D / "quadro_dono.jpg"])
        print("imagem K ok", flush=True)
        r = fg.motion(D / "dono_terno_usina.png", VID, D / "K_dono_terno_usina.mp4",
                      quem="man (glasses, beard, navy blue suit)")
        print("K OK", r["arquivos"], flush=True)
    except Exception as e:  # noqa: BLE001
        traceback.print_exc()
        print("K FALHOU", e, flush=True)
    try:
        r = fg.motion(r"D:\tmp_motion\teste\aparencia.png", VID, D / "L_ruiva_gestos_dono.mp4",
                      quem="woman (curly red hair, green sweater)")
        print("L OK", r["arquivos"], flush=True)
    except Exception as e:  # noqa: BLE001
        print("L FALHOU", e, flush=True)
    print("creditos", fg.f.creditos(), flush=True)
