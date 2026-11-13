# Advance 2 (01/11): a 1ª troca saiu meio a meio (rosto/cabelo novos, corpo e barba do original).
# M = rapaz magro com prompt forte; N = mulher. Vídeo base dfda40b9 já assentado no Flow (sem espera).
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, r"D:\projeto-navegador-sem-navegador")
from services.veo_flow.flow_gerar import FlowGerador, _para_1080  # noqa: E402

D = Path(r"D:\tmp_motion\advance")
SEG = D / "trecho_original_10s.mp4"
BASE = "dfda40b9-a26b-4e43-bfc3-a28407233fd8"
RAPAZ = "32cc7cbd-e4f3-4f39-a327-3628b7a9a900"
FLAGS = getattr(subprocess, "CREATE_NO_WINDOW", 0)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CONTA = sys.argv[1] if len(sys.argv) > 1 else "mundosolar"
SO = sys.argv[2] if len(sys.argv) > 2 else "MN"  # quais variações pedir
with FlowGerador(CONTA) as fg:
    # vídeo base é por projeto: sobe nesta conta (mudo) e espera assentar enquanto gera a imagem
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(SEG), "-an", "-c:v", "copy", str(D / "_base_mudo.mp4")],
                   check=True, creationflags=FLAGS)
    BASE = fg.f.subir_video(D / "_base_mudo.mp4")
    t0 = time.time()
    RAPAZ = fg.subir_imagem(D / "pessoa_nova.png")
    mulher = fg.imagem("A woman about 30 years old, long straight black hair in a ponytail, wearing the SAME purple "
                       "t-shirt with the white 'ADVANCE energia solar' logo and black pants, standing on the same sunny "
                       "paved residential street as the reference photo, full body, looking at the camera, "
                       "photorealistic, vertical.", D / "mulher.png", refs=[D / "quadro.jpg"])["midias"][0]["media_id"]
    pedidos = {
        "M": (RAPAZ, "Edit: COMPLETELY replace the man in the video with the slim young man from the reference image "
                     "- his face, short light brown hair, clean-shaven skin, slim body and build. Nothing of the "
                     "original man's face, beard or body must remain. He does exactly the same movements, gestures, "
                     "mouth movements and timing as in the video. Keep the background of the video."),
        "N": (mulher, "Edit: the man in the video becomes the woman from the reference image (her face, long black "
                      "ponytail and body), doing exactly the same movements, gestures, mouth movements and timing as "
                      "in the video. Keep the background of the video."),
    }
    while time.time() - t0 < 150 or "/video/" not in fg.f.midias([BASE]).get(BASE, ""):
        time.sleep(10)
    ids = {}
    for nome, (ref, txt) in pedidos.items():
        if nome not in SO:
            continue
        try:
            ids[nome] = fg.pedir(f"Use the generate_video_edit_video tool with Omni Flash, aspect ratio 9:16. Base "
                                 f"video: {BASE}. Reference image: {ref}. {txt}")["midias"][0]["media_id"]
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
            mudo = D / f"_mudo_{nome}.mp4"
            try:
                arq, tipo, _ = fg.f.baixar(mid, mudo)
            except Exception:  # noqa: BLE001
                continue
            if not (tipo or "").startswith("video"):
                continue
            _para_1080(mudo)
            final = D / f"ADVANCE_{nome}_PT.mp4"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(mudo), "-i", str(SEG), "-map", "0:v", "-map",
                            "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(final)],
                           check=True, creationflags=FLAGS)
            print(nome, "OK", final, flush=True)
            ids.pop(nome)
    print("pendentes", ids, "creditos", fg.f.creditos(), flush=True)
