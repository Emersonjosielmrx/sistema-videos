# Teste 5 (01/11): edição simples funciona (E OK); com imagem de referência de pessoa FALHA (C/D).
# G = referência que NÃO é pessoa (chapéu gerado no Flow, usado pelo media_id direto).
# H = troca de pessoa com a mulher gerada no Flow (media_id direto, sem baixar/subir de novo).
import sys
import time
from pathlib import Path

sys.path.insert(0, r"D:\projeto-navegador-sem-navegador")
from services.veo_flow.flow_gerar import FlowGerador  # noqa: E402

D = Path(r"D:\tmp_motion\teste")
BASE = "24ae2461-6876-4ad8-a3ca-a27a0438cf9f"  # vídeo do rapaz, mudo (o E deu certo nele)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

with FlowGerador("fabiovideoseducativos") as fg:
    chapeu = fg.imagem("Product photo of a bright yellow straw cowboy hat on a plain white background.",
                       D / "chapeu.png")["midias"][0]["media_id"]
    mulher = fg.imagem("Photorealistic vertical portrait of a young woman with long curly red hair, green sweater, "
                       "waist-up, looking at the camera, plain studio background.", D / "mulher2.png", formato="9:16"
                       )["midias"][0]["media_id"]
    print("imagens", chapeu, mulher, flush=True)
    pedidos = {
        "G": f"Use the generate_video_edit_video tool with Omni Flash, aspect ratio 9:16. Base video: {BASE}. "
             f"Reference image: {chapeu}. Edit: put the yellow straw hat from the reference image on the man's head. "
             f"Keep everything else the same.",
        "H": f"Use the generate_video_edit_video tool with Omni Flash, aspect ratio 9:16. Base video: {BASE}. "
             f"Reference image: {mulher}. Edit: the person in the video becomes the woman from the reference image "
             f"(her face, curly red hair and green sweater), doing exactly the same movements and expressions. "
             f"Keep the background of the base video.",
    }
    ids = {}
    for nome, txt in pedidos.items():
        try:
            ids[nome] = fg.pedir(txt)["midias"][0]["media_id"]
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
