# Motion Sync no vídeo REAL da Advance (dona 01/11): troca SÓ a pessoa, mantém o cenário e a fala em português.
import subprocess
import sys
import traceback
from pathlib import Path

sys.path.insert(0, r"D:\projeto-navegador-sem-navegador")
from services.veo_flow.flow_gerar import FlowGerador  # noqa: E402

ORIG = r"D:\hipercool-materiais\fluxo-anuncio-api\videos_prontos\EDITOR_Advance_Solar_video_real\1_ORIGINAL.mp4"
D = Path(r"D:\tmp_motion\advance")
D.mkdir(exist_ok=True)
SEG = D / "trecho_original_10s.mp4"
FLAGS = getattr(subprocess, "CREATE_NO_WINDOW", 0)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def ff(*a):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *map(str, a)], check=True, creationflags=FLAGS)


ff("-i", ORIG, "-t", "10", "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", SEG)
ff("-ss", "2", "-i", SEG, "-frames:v", "1", D / "quadro.jpg")

with FlowGerador("fabiovideoseducativos") as fg:
    try:
        fg.imagem("A DIFFERENT man (not the one in the reference): about 35 years old, slim build, short light brown "
                  "hair, clean-shaven, friendly face. He wears the SAME purple t-shirt with the white 'ADVANCE energia "
                  "solar' logo and black pants, standing on the same sunny paved residential street as the reference "
                  "photo, full body, looking at the camera, photorealistic, vertical.",
                  D / "pessoa_nova.png", refs=[D / "quadro.jpg"])
        print("imagem ok", flush=True)
        fg.motion(D / "pessoa_nova.png", SEG, D / "_mudo.mp4",
                  quem="man (short light brown hair, clean-shaven, purple ADVANCE t-shirt)", fundo="video")
        # a fala original em português por cima (a boca segue o movimento da fala original)
        ff("-i", D / "_mudo.mp4", "-i", SEG, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a",
           "192k", "-shortest", D / "ADVANCE_pessoa_trocada_PT.mp4")
        print("OK", D / "ADVANCE_pessoa_trocada_PT.mp4", flush=True)
    except Exception as e:  # noqa: BLE001
        traceback.print_exc()
        print("FALHOU", e, flush=True)
    print("creditos", fg.f.creditos(), flush=True)
