# Teste 2 do Motion Sync (01/11): o 1º FALHOU no servidor (código 13) com prompt longo + vídeo 7,9 s.
# A = mesmos arquivos já no projeto, prompt CURTO.  B = vídeo cortado em 5 s, prompt curto.
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, r"D:\projeto-navegador-sem-navegador")
from services.veo_flow.flow_gerar import FlowGerador, Recusado  # noqa: E402

D = Path(r"D:\tmp_motion\teste")
VID = r"D:\veo\beta\videos\cron_shorts\danca_e_musica__20261101_161853.mp4"
CURTO = ("Replace the person in the base video with the woman from the reference image, keeping her face, hair, "
         "clothes and the kitchen background. Copy exactly the body and head movements and timing of the base video.")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def tentar(fg, nome, vid, img):
    pedido = (f"Use the generate_video_edit_video tool with Omni Flash, aspect ratio 9:16. Base video: uploaded video "
              f"{vid}. Reference image: uploaded image {img}. {CURTO}")
    try:
        res = fg.pedir(pedido)
        print(nome, "pedido ok", [m["media_id"] for m in res["midias"]], flush=True)
        return res
    except Exception as e:  # noqa: BLE001
        print(nome, "PEDIDO FALHOU", e, flush=True)


try:
    with FlowGerador("fabiovideoseducativos") as fg:
        # teste 3: o A voltou SPEECH_EDIT_BLOCKED -> vídeo base SEM ÁUDIO. C = prompt curto; D = motion() completo
        import subprocess
        mudo = D / "base_mudo.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", VID, "-an", "-c:v", "copy", str(mudo)], check=True)
        vidm = fg.f.subir_video(mudo)
        print("C video mudo", vidm, flush=True)
        a = tentar(fg, "C", vidm, "bf385912-d4b2-475d-b179-8f6119d1354a")
        b = None
        try:
            r = fg.motion(D / "aparencia.png", VID, D / "motion_D.mp4")
            print("D MOTION OK", r["arquivos"], flush=True)
        except Exception as e:  # noqa: BLE001
            print("D FALHOU", e, flush=True)
        fg.soltar_chrome()
        for nome, res in (("C", a), ("B", b)):
            if not res:
                continue
            try:
                arq = fg.baixar(res, [D / f"motion_{nome}.mp4"], video=True, espera_s=900)
                print(nome, "MOTION OK", arq, flush=True)
            except Recusado as e:
                print(nome, "FALHOU NO SERVIDOR", e, flush=True)
            except Exception as e:  # noqa: BLE001
                print(nome, "ERRO", e, flush=True)
        print("creditos depois", fg.f.creditos(), flush=True)
except Exception as e:  # noqa: BLE001
    traceback.print_exc()
    print("FALHOU", type(e).__name__, str(e)[:800], flush=True)
