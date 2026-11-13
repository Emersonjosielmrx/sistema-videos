# Teste 6 (01/11): H (ref GERADA no Flow + prompt curto) deu certo; C/D (ref ENVIADA + prompt) falharam.
# I = ref ENVIADA (bf385912, upload de aparencia.png) + o prompt do H. Falhou = o upload da imagem é o problema.
import sys
import time
from pathlib import Path

sys.path.insert(0, r"D:\projeto-navegador-sem-navegador")
from services.veo_flow.flow_gerar import FlowGerador  # noqa: E402

D = Path(r"D:\tmp_motion\teste")
BASE = "24ae2461-6876-4ad8-a3ca-a27a0438cf9f"
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

with FlowGerador("fabiovideoseducativos") as fg:
    img = fg.subir_imagem(D / "aparencia.png")
    mid = fg.pedir(f"Use the generate_video_edit_video tool with Omni Flash, aspect ratio 9:16. Base video: {BASE}. "
                   f"Reference image: {img}. Edit: the person in the video becomes the woman from the reference image "
                   f"(her face, curly red hair and green sweater), doing exactly the same movements and expressions. "
                   f"Use the kitchen background of the reference image.")["midias"][0]["media_id"]
    print("I pedido", mid, "ref", img, flush=True)
    fg.soltar_chrome()
    fim = time.time() + 900
    while time.time() < fim:
        time.sleep(20)
        falha = fg.f.falha_geracao(mid)
        if falha:
            print("I FALHOU", falha, flush=True)
            break
        try:
            arq, tipo, _ = fg.f.baixar(mid, D / "edit_I.mp4")
            if (tipo or "").startswith("video"):
                print("I OK", arq, flush=True)
                break
        except Exception:  # noqa: BLE001
            pass
    print("creditos", fg.f.creditos(), flush=True)
